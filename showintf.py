#! /usr/bin/env python
from __future__ import print_function
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from osgeo import gdal

###############################################################################
def dismph_colormap():
    '''Make a custom colormap like the one used in dismph.  The list was
      created from dismphN.mat in geodmod which is a 64 segmented colormap
      using the following:
        from scipy.io import loadmat
        cmap = loadmat('dismphN.mat',struct_as_record=True)['dismphN']
        from matplotlib.colors import rgb2hex
        list=[]
        for i in cmap: list.append(rgb2hex(i))
    '''
    list = ['#f579cd', '#f67fc6', '#f686bf', '#f68cb9', '#f692b3', '#f698ad',
            '#f69ea7', '#f6a5a1', '#f6ab9a', '#f6b194', '#f6b78e', '#f6bd88',
            '#f6c482', '#f6ca7b', '#f6d075', '#f6d66f', '#f6dc69', '#f6e363',
            '#efe765', '#e5eb6b', '#dbf071', '#d0f477', '#c8f67d', '#c2f684',
            '#bbf68a', '#b5f690', '#aff696', '#a9f69c', '#a3f6a3', '#9cf6a9',
            '#96f6af', '#90f6b5', '#8af6bb', '#84f6c2', '#7df6c8', '#77f6ce',
            '#71f6d4', '#6bf6da', '#65f6e0', '#5ef6e7', '#58f0ed', '#52e8f3',
            '#4cdbf9', '#7bccf6', '#82c4f6', '#88bdf6', '#8eb7f6', '#94b1f6',
            '#9aabf6', '#a1a5f6', '#a79ef6', '#ad98f6', '#b392f6', '#b98cf6',
            '#bf86f6', '#c67ff6', '#cc79f6', '#d273f6', '#d86df6', '#de67f6',
            '#e561f6', '#e967ec', '#ed6de2', '#f173d7']
    dismphCM = matplotlib.colors.LinearSegmentedColormap.from_list('mycm', list)
    dismphCM.set_bad('w', 0.0)
    return dismphCM

infile = sys.argv[1]

#os.environ['GDAL_NETCDF_BOTTOMUP'] = 'NO'
u = gdal.Open(infile).ReadAsArray() #[3000:4300,500:1500]

if 'unwrap' in infile:
    print(np.nanmin(u),np.nanmax(u))
#    plt.imshow(u,cmap=plt.cm.RdBu,clim=[-10,10])
    plt.imshow(u,cmap=plt.cm.RdBu)
elif 'amp' in infile or 'mli' in infile:
    print(np.nanmin(u),np.nanmax(u))
    plt.imshow(u,cmap=plt.cm.gray)
elif 'corr' in infile:
    print(np.nanmin(u),np.nanmax(u))
    plt.imshow(u)
else:
    plt.imshow(u,cmap=dismph_colormap())
plt.show()
