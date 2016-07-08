#! /usr/bin/env python

###############################################################################
#  selectPairsGMTSAR.py 
#
#  Project:
#  Purpose:  Select pairs for interferogram processing
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
import shutil
import datetime
import itertools
from operator import itemgetter
import argparse

import matplotlib.delaunay as md 
import matplotlib.pyplot as plt

def remove_bad_pairs(igramIndices,pbase,tbase,Bcrit,Tcrit):
    ## Remove pairs/interoferogram that have baseline or doppler overlap issues
    perpBaseMax = Bcrit 
    goodPairs = []
    for igram in igramIndices:
        index1 = igram[0]
        index2 = igram[1]
        baseline = pbase[index1] - pbase[index2]
        if baseline > perpBaseMax or baseline < -perpBaseMax : 
            continue  # if the baseline is bad, no need to calculate doppler overlap, go to the next igram
        if (tbase[index2]-tbase[index1]) > Tcrit: # remove pairs exceeding critical temporal baseline
            continue
        goodPairs.append(igram)        
    return goodPairs

def get_prm(file):
    file_root = os.path.basename(file.partition('.')[0])  
    prm_file = os.path.dirname(file) + '/' + file_root + ".PRM"
    prm_dict = {}
    for line in open(prm_file):
        c = line.split("=")
        if len(c) < 2 or line.startswith('%') or line.startswith('#'): 
            next #ignore commented lines or those without variables
        else: 
            prm_dict[c[0].strip()] = str.replace(c[1], '\n', '').strip()
    return prm_dict


def parse():
    '''Command line parser.'''
    parser = argparse.ArgumentParser(description='Select Interferogram Pairs')
    parser.add_argument('-i', action='store', default='bl_list.txt', dest='infile', help='Baseline List', type=str)
    parser.add_argument('-Mmin', dest='monthMin', action='store', default=1, help='Integer of min. month of year (Default: 1 (Jan.))', type=int)
    parser.add_argument('-Mmax', dest='monthMax', action='store', default=12, help='Integer of max. month of year (Default: 12 (Dec.))', type=int)
    parser.add_argument('-method',action='store', dest='selectMethod',default='del', help='Pairs selection method. all or del(aunay)')
    parser.add_argument('-Bcrit', action='store', default=200.,dest='Bcrit', help='Critical perpendicular baseline (meters)', type=float)
    parser.add_argument('-Tcrit', action='store', default=9999,dest='Tcrit', help='Critical temporal baseline (days)', type=int)
    parser.add_argument('-Dmax', action='store', default=48,dest='lengthDayMax', help='Max. number of days for adding additional pairs', type=int)
    parser.add_argument("-mask", action="store", dest="mask", default='yes')
    parser.add_argument('-span', action='store', dest='dateSpan', help='Date you want ifgrams to span (ie an event of interest)', type=str)
    parser.add_argument("-np", action="store_true", default=False, help='Show network plot')
    clos = parser.parse_args()
    return clos

def main():
    clos = parse()
    print(clos)
    dat = open(clos.infile,'r').readlines()
    data = []
    for d in dat:
        data.append(d.split())
  
    dates = []
    tbase = []
    pbase = []
    slcs = []
    prms = []
    for d in data:
      date=datetime.datetime.strptime(d[0],"%Y%m%d")
      if date.month >= clos.monthMin and date.month <= clos.monthMax:
          pbase.append(float(d[1]))
          dates.append(d[0])
          slcs.append(d[3])
          prms.append(os.path.splitext(d[3])[0]+'.PRM')
    print("************************************")
    print("Total # of scenes in %s: %d" % (clos.infile,len(data)))
    print("Total after filtering by month: %d" % len(dates))
    print("************************************")
  
    '''calculate tbase from d1 to dni'''
    d1 = datetime.datetime.strptime(dates[0],"%Y%m%d")
    for d in dates:
        d2 = datetime.datetime.strptime(d,"%Y%m%d")
        diff = d2-d1
        tbase.append(diff.days)
  
    '''
    This returns a list of all possible pairs of dates.  Should eliminate
    those pairs with bad bperp and doppler overlap and leave elimination
    based on time for later since we can still use them if there is no
    other alternative.
    '''
    indexList = []
    for ni in range(len(dates)): 
        indexList.append(ni)
    allPairs = list(itertools.combinations(indexList, 2))    
    ## Lets remove the ones with bad doppler and baselines
    print("all possible pairs = " + str(len(allPairs)))
    allPairs = remove_bad_pairs(allPairs,pbase,tbase,clos.Bcrit,clos.Tcrit)
    print("all pairs with baselines less than Bcrit (%d m) and Tcrit (%d days): %d" % (clos.Bcrit, clos.Tcrit, len(allPairs)))
  
    ''' 
    Do a delaunay triangulation to find the "best" pairs.
    The edges will contain index to the pairs we need. We apply a 
    weighting factor to the time baseline so that the space being
    triangulated is symetric (base on Pepe and Lanari (2006))
  
    After the pairs are selected we then eliminate pairs which 
    are not "good" due to perpendicular baseline and doppler overlap.
    We then add in the pairs with short temporal baselines (lengthDayMax).  
    '''
    tbaseFac = []
    for idx in range(len(tbase)): tbaseFac.append(tbase[idx] * (max(pbase) - min(pbase)) / (max(tbase)))
    centers, edges, tri, neighbors = md.delaunay(tbaseFac, pbase)
    delaunayPairs = edges.tolist()
    '''
    The delaunay pairs do not necessarily have the indexes with lowest 
    first, so let's arrange and sort the delaunay pairs
    '''
    for idx in range(len(delaunayPairs)):
        if delaunayPairs[idx][0] > delaunayPairs[idx][1]:
            index1 = delaunayPairs[idx][1]
            index2 = delaunayPairs[idx][0]
            delaunayPairs[idx][0] = index1
            delaunayPairs[idx][1] = index2
    delaunayPairs = sorted(delaunayPairs, key=itemgetter(0)) 
    ## Lets remove the ones with bad doppler and baselines
    print("delaunay possible pairs = " + str(len(delaunayPairs)))
    delaunayPairs = remove_bad_pairs(delaunayPairs,pbase,tbase,clos.Bcrit,clos.Tcrit)
    print("delaunay pairs with baselines less than Bcrit (%d m) and Tcrit (%d days): %d"  % (clos.Bcrit,clos.Tcrit,len(delaunayPairs)))
    ## Now lets add all additional pairs less than lengthDayMax from allPairs
    for idx in range(len(allPairs)):
        allPairs[idx] = list(allPairs[idx])
        if tbase[allPairs[idx][1]] - tbase[allPairs[idx][0]] <= clos.lengthDayMax:
            if allPairs[idx] not in delaunayPairs: 
                delaunayPairs.append(allPairs[idx])
    print("delaunay pairs with added pairs less than " + str(clos.lengthDayMax) + " days = " + str(len(delaunayPairs)))
  
    projectDir = os.getcwd()
    projectName = os.path.basename(projectDir) 
  
    if clos.selectMethod == 'all':
        pairs = allPairs
    else:
        pairs = delaunayPairs
  
    dates_obj = [datetime.datetime.strptime(d,"%Y%m%d") for d in dates]
    if clos.dateSpan:
        """ This will filter out the pairs that don't span the date of interest """
        date_span = datetime.datetime.strptime(clos.dateSpan,"%Y-%m-%d")
        pairs = [igram for igram in pairs if dates_obj[igram[0]]<date_span and dates_obj[igram[1]]>date_span ]
        print("# of pairs spanning %s: %d" % (clos.dateSpan,len(pairs)))
  
    intf = open('intf.in','w')
    f = open('run_p2pTOPS','w')
    for igram in sorted(pairs):
        ndx1 = igram[0]
        ndx2 = igram[1]
        baseline = '%05.0f' % round(pbase[ndx1]-pbase[ndx2])
        temporalbaseline = '%04.0f' % round(tbase[ndx2]-tbase[ndx1])
#        print(slcs[ndx1].split("_")[0]+":"+slcs[ndx2].split("_")[0])
        intf.write(slcs[ndx1].split("_")[0]+":"+slcs[ndx2].split("_")[0]+'\n')
        f.write('p2p_S1A_TOPS.csh %s %s config.tops.txt\n' % (os.path.splitext(slcs[ndx1])[0],os.path.splitext(slcs[ndx2])[0])) 
    intf.close()
    f.close()

    f = open('config.tops.txt','w')
    f.write('proc_stage = 4\n')
    f.write('topo_phase = 1\n')
    f.write('topo_shift = 1\n')
    f.write('switch_master = 0\n')
    f.write('filter_wavelength = 200\n')
    f.write('dec_factor = 2\n')
    f.write('threshold_snaphu = 0.1\n')
    f.write('switch_land = 1\n')
    f.write('defomax = 0\n')
    f.write('threshold_geocode = .10')
    f.close()

    plt.figure()
    for e in edges:
        x = [dates_obj[e[0]],dates_obj[e[1]]]
        y = [pbase[e[0]],pbase[e[1]]]
        plt.plot(x,y,'--', c='gray')
    for igram in sorted(pairs):
        ndx1 = igram[0]
        ndx2 = igram[1]
        x = [dates_obj[ndx1], dates_obj[ndx2]]
        y = [pbase[ndx1], pbase[ndx2]]
        plt.plot(x, y, 'b')
    plt.plot(dates_obj, pbase, 'ro')
    if clos.dateSpan:
        plt.axvline(datetime.datetime.strptime(clos.dateSpan,'%Y-%m-%d'),ls='-',color='g')
        plt.annotate('Event',xy=(datetime.datetime.strptime(clos.dateSpan,'%Y-%m-%d'),min(pbase)), xycoords='data', color='g' ) 
    plt.xlabel('Date')
    plt.ylabel('Perpendicular Baseline (m)')
    projectName = os.path.basename(os.getcwd())
    plt.title('SBAS Network - ' + projectName)
    plt.savefig(projectName+'_network.png',transparent=True)
    if clos.np:
        plt.show()

if __name__ == '__main__':
    main()
