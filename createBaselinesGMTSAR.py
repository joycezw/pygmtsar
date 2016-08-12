#! /usr/bin/env python

###############################################################################
#  createBaselinesGMTSAR.py
#
#  Project:
#  Purpose:  Create the bl_list.txt file with GMTSAR  
#  Author:   Scott Baker, baker@unavco.org
#  Created:  June 2016
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

from __future__ import print_function
import os
import sys
import glob
import subprocess as sub

import numpy as np

import gmtsarutils

masterDate = sys.argv[1]

f = open('bl_list.txt','w')
workdir = os.getcwd()

if os.path.exists('SLC'): 
    os.chdir('SLC')
masterPRM = glob.glob("*"+masterDate+'*.PRM')[0]
prmDict = gmtsarutils.read_prm(masterPRM)
scID = prmDict['SC_identity']
prmList = sorted(glob.glob('*PRM'))
for scene in prmList:
    temp_dict = gmtsarutils.read_prm(scene)
    if not 'SC_vel' in temp_dict.keys():
       gmtsarutils.calc_dop_orb(scene)
    date = os.path.splitext(scene)[0]
    cmd = 'SAT_baseline ' + masterPRM + ' ' + scene
    pipe = sub.Popen(cmd, shell=True, stdout=sub.PIPE).stdout
    output = pipe.read()
    print(output)
    tmp = output.split('\n')
    outDict = {}
    for l in tmp:
        c = l.split("=")
        if len(c) < 2:
            next
        else:
            outDict[c[0].strip()] = str.replace(c[1], '\n', '').strip()
    f.write('%s %5.6f %5.6f %s\n' % (date,float(outDict['B_perpendicular']),float(outDict['B_parallel']),date+'.SLC'))
f.close()
os.chdir(workdir)

### FIND MASTER DATE THAT MINIMIZES BASELINE ###
dat = open('bl_list.txt','r').readlines()
data = []
for d in dat:
    data.append(d.split())
dates = np.array([d[0] for d in data])
pbase = np.array([float(d[1]) for d in data])
print("OPTIMAL MASTER DATE: %s" %  dates.flat[np.abs(pbase - np.mean(pbase)).argmin()])
