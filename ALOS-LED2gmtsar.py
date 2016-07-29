#! /usr/bin/env python

###############################################################################
#  ALOS-LED2gmtsar.py
#
#  Project:
#  Purpose:  Extract the state vectors from the ALOS-1 LED
#  Author:   Scott Baker, baker@unavco.org
#  Created:  July 2016
#
###############################################################################
#  Copyright (c) 2016, Scott Baker
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
###############################################################################

import sys

infile = sys.argv[1]
### OPEN THE LED FILE FOR READING ###
f = open(infile,'rb')
#led_descriptor = f.read(720)
#dset_summary = f.read(4096)
#pos_record = f.read(4680)
### WE ONLY WANT THE STATE VECTORS SO SEEK TO THE START ###
f.seek(4956)

### GET THE INFO NEEDED FOR THE STATE VECTORS ###
num_points = int(f.read(4))
year = int(f.read(4))
month = int(f.read(4))
day = int(f.read(4))
jday = int(f.read(4))
sod = float(f.read(22))
interval = float(f.read(22))

junk = f.read(182)

### WRITE THE NEW LED FILE ###
outfile = '%d%02d%02d.LED' % (year,month,day)
print "Writing: %s" % outfile
with open(outfile,'w') as LED:
    LED.write('%d %d %d %f %f\n' % (num_points,year,jday,sod,interval))
    for i in range(28):
        tmp = f.read(132)
        LED.write('%d %d %f %.16f %.16f %.16f %.16f %.16f %.16f\n' % (year,jday,sod+interval*i,float(tmp[0:22]),float(tmp[22:44]),float(tmp[44:66]),float(tmp[66:88]),float(tmp[88:110]),float(tmp[110:132])))
