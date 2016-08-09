import os.path
import subprocess
import sys
import math
import urllib2
import glob

def DownloadNED(west, north, east, south, path="./"):
    fileList = []

    west = int(math.ceil(abs(float(west))))
    north = int(math.ceil(abs(float(north))))
    east = int(math.ceil(abs(float(east))))
    south = int(math.ceil(abs(float(south))))

    for y in range(south, north + 1):
        for x in range(east, west + 1):
            response = urllib2.urlopen("http://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/ArcGrid/n{:02d}w{:03d}.zip".format(y,x))
            if not os.path.isfile(os.path.join(path, 'n{0}w{1}.zip'.format(y,x))):
                with open(os.path.join(path, 'n{0}w{1}.zip'.format(y,x)), 'wb') as dest_file:
                    dest_file.write(response.read())
            fileList.append(os.path.join(path, 'n{0}w{1}.zip'.format(y,x)))

    return fileList

def convertNED(gridsq):
    path = glob.glob('{0}/*/w001001.adf'.format(gridsq))[0]
    print path
    #Convert to .tif
    subprocess.call(['gdal_translate', path, '{0}_nad83.tif'.format(gridsq)])
    #Reproject to EPSG:3857 (Google Mercator)
    #subprocess.call(['gdalwarp', '-s_srs', 'EPSG:4269', '-t_srs', 'EPSG:3857', '-r', 'bilinear', '{0}_nad83.tif'.format(gridsq), '{0}.tif'.format(gridsq)])
    #Convert to feet
    subprocess.call('gdal_calc.py -A {0}_nad83.tif --outfile={0}_ft.tif --calc="A/.3048"'.format(gridsq), shell=True)

def loadNEDToPostgis(filename, overviewlist, createTable=False):
    print filename
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
    args.extend(['-f', 'dem'])
    args.append(filename)
    args.append('public.usgs_dem_13')
    print args
    r2pproc = subprocess.Popen(args, stdout=subprocess.PIPE)
    psqlproc = subprocess.Popen(['psql', '-h', '10.0.1.91', '-U', 'postgres', 'gis'], stdin = r2pproc.stdout) 
    r2pproc.stdout.close()
    psqlproc.wait()


if __name__ == '__main__':
    if len(sys.argv) < 5:
        raise Exception("Not enough arguments")
    else:
        fileList = DownloadNED(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
        makeDemTable = True
#TODO: Need to load DEM rasters before reprojection
        for fname in fileList:
            print fname
            gridsq = fname[2:].split('.')[0]
            subprocess.call(['unzip', fname, '-d', fname[:-4]])
            convertNED(gridsq)
            loadNEDToPostgis("{0}_ft.tif".format(gridsq), None, makeDemTable)
            makeDemTable = False
            

