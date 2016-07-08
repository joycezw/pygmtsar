#! /usr/bin/env python

###############################################################################
#  baseline_plot.py
#
#  Project:
#  Purpose:  Plot baselines from bl_list.txt with Matplotlib
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

import sys
import datetime
import time

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

baselineFile = open(sys.argv[1])
lines = []
'''Read bl_list.txt and put each line into an array'''
for line in baselineFile.xreadlines():
    l = str.replace(line,'\n','').strip()
    lines.append(l)

'''This is what we need from bl_list.txt to calculate the pairs'''
dates   = []
pbase   = []
doppler = []
prf     = [] 
SLCdirs = []
tbase   = []  # this will be calculated below

'''Read each line and put the values into arrays'''
for line in lines:
    c = line.split()                # splits on white space
    dates.append(c[0])
    pbase.append(float(c[1]))

'''calculate tbase from d1 to dni'''
d1 = datetime.datetime(*time.strptime(dates[0],"%Y%m%d")[0:5])
for ni in range(len(dates)):
    d2 = datetime.datetime(*time.strptime(dates[ni],"%Y%m%d")[0:5])
    diff = d2-d1
    tbase.append(diff.days)

dates_obj = []
for d in dates:
    dates_obj.append(datetime.datetime.strptime(d,"%Y%m%d"))

plt.figure()
ax1 = plt.subplot(111)
#plt.plot(tbase, pbase, 'ro')
plt.plot(dates_obj,pbase,'ro-')
plt.ylabel('bperp(m)')
plt.xlabel('tbase (date)')
ax1.yaxis.grid(color='gray', linestyle='dashed')
plt.show()

