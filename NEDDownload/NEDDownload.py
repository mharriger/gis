import os.path
import subprocess
import sys
import math
import urllib2
import glob
import zipfile

def DownloadNED(west, north, east, south, path="./"):
    fileList = []

    west = int(math.ceil(abs(float(west))))
    north = int(math.ceil(abs(float(north))))
    east = int(math.ceil(abs(float(east)))) + 1
    south = int(math.ceil(abs(float(south)))) + 1

    for y in range(south, north + 1):
        for x in range(east, west + 1):
            response = urllib2.urlopen("http://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/ArcGrid/n{:02d}w{:03d}.zip".format(y,x))
            if not os.path.isfile(os.path.join(path, 'n{0}w{1}.zip'.format(y,x))):
                with open(os.path.join(path, 'n{0}w{1}.zip'.format(y,x)), 'wb') as dest_file:
                    dest_file.write(response.read())
            fileList.append(os.path.join(path, 'n{0}w{1}.zip'.format(y,x)))

    return fileList

def downloadNLCD(path="./"):
    response = urllib2.urlopen("https://prd-tnm.s3.amazonaws.com/StagedProducts/Woodland/GDB/National_Woodland.gdb.zip")
    if not os.path.isfile(os.path.join(path, 'National_Woodland.gdb.zip')):
        with open(os.path.join(path, 'National_Woodland.gdb.zip'), 'wb') as dest_file:
            dest_file.write(response.read())

def convertNED(gridsq):
    path = glob.glob('{0}/*/w001001.adf'.format(gridsq))[0]
    print path
    #Convert to .tif
    subprocess.call(['gdal_translate', path, '{0}_nad83.tif'.format(gridsq)])
    #Reproject to EPSG:3857 (Google Mercator)
    #subprocess.call(['gdalwarp', '-s_srs', 'EPSG:4269', '-t_srs', 'EPSG:3857', '-r', 'bilinear', '{0}_nad83.tif'.format(gridsq), '{0}.tif'.format(gridsq)])
    #Convert to feet
    os.system('c:\python27\python c:\\osgeo4w64\\bin\\gdal_calc.py -A {0}_nad83.tif --outfile={0}_ft.tif --calc="A/.3048"'.format(gridsq))

def loadRasterToPostgis(filename, tablename, colname, overviewlist, createTable=False):
    args = ['raster2pgsql']
    if createTable:
        args.append('-d')
        args.append('-I')
    else:
        args.append('-a')
    args.append('-C') #Apply raster constraints
    args.append('-x') #Don't apply max extent contraint
    args.extend(['-t', '256x256']) #Tile size
    if overviewlist:
        args.extend(['-l', ",".join(overviewlist)])
    args.extend(['-f', colname])
    args.append(filename)
    args.append(tablename)
    print args
    r2pproc = subprocess.Popen(args, stdout=subprocess.PIPE)
    psqlproc = subprocess.Popen(['psql', '-h', '10.0.1.91', '-U', 'postgres', 'gis'], stdin = r2pproc.stdout) 
    r2pproc.stdout.close()
    psqlproc.wait()

def loadShapefileToPostgis(filename, tablename, colname, overviewlist, createTable=False):
    args = ['shp2pgsql']
    if createTable:
        args.append('-d')
        args.append('-I')
    else:
        args.append('-a')
    args.extend(['-g', colname])
    args.extend(['-s', 'EPSG:3857'])
    args.append(filename)
    args.append(tablename)
    print args
    r2pproc = subprocess.Popen(args, stdout=subprocess.PIPE)
    psqlproc = subprocess.Popen(['psql', '-h', '10.0.1.91', '-U', 'postgres', 'gis'], stdin = r2pproc.stdout) 
    r2pproc.stdout.close()
    psqlproc.wait()

def createHillshade(demFilename, outFilename):
    subprocess.call(['gdaldem', 'hillshade', '-s', '3.28084', demFilename, outFilename])

def createContour(demFilename, outFilename, interval):
    subprocess.call(['gdal_contour', '-a', 'elev', '-i', str(interval), demFilename, outFilename])

def unzipFile(filename):
    with zipfile.ZipFile(filename, 'r') as zf:
        zf.extractall('./' + fname[:-4])
    

if __name__ == '__main__':
    if len(sys.argv) < 5:
        raise Exception("Not enough arguments")
    else:
        #TODO: Download OSM data: http://overpass-api.de/api/map?bbox=-97.000,40.000,-95.000,43.000
        #TODO: Download NHD
        #Extract shapefiles for area of interest from national NHD
        #ogr2ogr NHDArea.shp NationalNHD\NHD.gdb NHDArea -spat -97 43 -95 40 -t_srs EPSG:3857
	#Flowline requires installing the FileGDB driver (vs. OpenFileGDB driver). I used OSGeo4W installer to install it on Windows
        #ogr2ogr NHDFlowline.shp NationalNHD\NHD.gdb NHDFlowline -spat -97 43 -95 40 -t_srs EPSG:3857
        #ogr2ogr NHDWaterbody.shp NationalNHD\NHD.gdb NHDWaterbody -spat -97 43 -95 40 -t_srs EPSG:3857
        fileList = DownloadNED(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
        for fname in fileList:
            print fname
            gridsq = fname[2:].split('.')[0]
            if not os.path.isdir('./' + fname[:-4]):
                unzipFile(fname)
            if not os.path.exists('./' + gridsq + '_ft.tif'):
                convertNED(gridsq)
        if not os.path.exists('./dem.vrt'):
            subprocess.call(['gdalbuildvrt', 'dem.vrt', '*ft.tif'])
        if not os.path.exists('./dem_3857.tif'):
            subprocess.call(['gdalwarp', '-t_srs', 'EPSG:3857', '-r', 'bilinear', 'dem.vrt', 'dem_3857.tif']) 
        if not os.path.exists('./hillshade.tif'):
            createHillshade('dem_3857.tif', 'hillshade.tif')
        if not os.path.exists('./contour.shp'):
            createContour('dem_3857.tif', 'contour.shp', 20)
        #Download the national woodland tint dataset, then trim it to our area. Easier than joining state datasets.
        #https://prd-tnm.s3.amazonaws.com/StagedProducts/Woodland/Shape/WOODLAND_31_Nebraska_GU_STATEORTERRITORY.zip
        #https://prd-tnm.s3.amazonaws.com/StagedProducts/Woodland/Shape/WOODLAND_19_Iowa_GU_STATEORTERRITORY.zip
        #set up merge.vrt
        #ogr2ogr woodland.shp woodland.vrt -dialect sqlite -sql "SELECT DISTINCT geometry, * FROM unionLayer" -spat -97 43 -95 40 -t_srs EPSG:3857
        if not os.path.exists('./National_Woodland.gdb.zip'):
            downloadNLCD()
            unzipFile('./National_Woodland.gdb.zip')
            #subprocess.call(['ogr2ogr', '-f', 'ESRI Shapefile', 'woodland.shp', '-clipsrc', sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]) 

        #loadRasterToPostgis('hillshade.tif', 'hillshade_3857', 'rast', None, True)
        #loadShapefileToPostgis('contour', 'contour_3857', 'contour_geom', None, True)
        #osm2pgsql.exe -s -U postgres -d gis -S default.style -W map.osm
        
