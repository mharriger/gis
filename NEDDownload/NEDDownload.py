import sys
import math

if len(sys.argv) < 5:
    raise Exception("Not enough arguments")

west = int(math.ceil(abs(float(sys.argv[1]))))
north = int(math.ceil(abs(float(sys.argv[2]))))
east = int(math.ceil(abs(float(sys.argv[3]))))
south = int(math.ceil(abs(float(sys.argv[4]))))

print west, north, east, south

for y in range(south, north + 1):
    for x in range(east, west + 1):
        print "n{0}w{1}".format(y,x)
