import sys
import math
import urllib2

if len(sys.argv) < 5:
    raise Exception("Not enough arguments")

west = int(math.ceil(abs(float(sys.argv[1]))))
north = int(math.ceil(abs(float(sys.argv[2]))))
east = int(math.ceil(abs(float(sys.argv[3]))))
south = int(math.ceil(abs(float(sys.argv[4]))))

print west, north, east, south

for y in range(south, north + 1):
    for x in range(east, west + 1):
        print "http://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/ArcGrid/n{:02d}w{:03d}.zip".format(y,x)
        response = urllib2.urlopen("http://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/ArcGrid/n{:02d}w{:03d}.zip".format(y,x))
        with open('n{0}w{1}.zip'.format(y,x), 'wb') as dest_file:
            dest_file.write(response.read())

