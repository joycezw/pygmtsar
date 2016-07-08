#! /usr/bin/env python

###############################################################################
#  tops_prepare_stack.py
#
#  Project:  
#  Purpose:  Prepare TOPS SLCs for stack alignment with GMT5SAR
#  Author:   Scott Baker, baker@unavco.org 
#  Created:  May 2016
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
import argparse
import datetime
import zipfile
import fnmatch
import shutil
from xml.etree import ElementTree as ET
import glob
import re
import urllib2

import numpy as np

import gmtsarutils

####################################################
def extract_tiff_xml(infile,swath_num):
    input_zip = zipfile.ZipFile(infile)
    for t in input_zip.namelist():
        if fnmatch.fnmatch(t,'*annotation/s1a-iw'+swath_num+'-slc-vv*.xml') or fnmatch.fnmatch(t,'*annotation/s1a-iw'+swath_num+'-slc-hh*.xml'):
#            print("extracting %s" % t)
            xml = os.path.basename(t)
            if os.path.exists(xml): continue
            source = input_zip.open(t)
            target = open(xml,'wb')
            shutil.copyfileobj(source,target)
            target.close()
            source.close()
        if fnmatch.fnmatch(t,'*measurement/s1a-iw'+swath_num+'-slc-vv*tiff') or fnmatch.fnmatch(t,'*measurement/s1a-iw'+swath_num+'-slc-hh*tiff'):
#            print("extracting %s" % t)
            tiff = os.path.basename(t)
            if os.path.exists(tiff): continue
            source = input_zip.open(t)
            target = open(tiff,'wb')
            shutil.copyfileobj(source,target)
            target.close()
            source.close()
    input_zip.close()
    return tiff,xml

####################################################
def get_orbit(meta_dict):
    """ Find an orbit file for the scene
    Use Precise (POE) orbit if available (i.e. scene is > 20 days old) otherwise use Restituted (RES)

    """
    if (datetime.datetime.now()-meta_dict['startTime']).days > 20:
        orb_dir = 'aux_poeorb'
    else:
        orb_dir = 'aux_resorb'
    ### using a local copy of all the orbit files, ideally something like ISCE uses to
    ### search and download the orbits from either UNAVCO or PGDG would be ideal
    ##### FIND THE CORRECT ORBIT FILE #####
    BASE_URL = 'https://www.unavco.org/data/imaging/sar/lts1/winsar/s1qc'
    ##### GET LIST OF FILES AND FIND ONE THAT COVERS THE SCENE #####
    orb_file=None
    files = urllib2.urlopen(BASE_URL+'/'+ orb_dir +'/').read().splitlines()
    xml_resorb = [f.split(">")[2].split("<")[0] for f in files  if "ORB_" in f]
    for xml_orb in xml_resorb:
        orb_file_dates = os.path.splitext(xml_orb)[0].split('_V')[1].split("_")
        orb_start = datetime.datetime.strptime(orb_file_dates[0], "%Y%m%dT%H%M%S")
        orb_stop = datetime.datetime.strptime(orb_file_dates[1], "%Y%m%dT%H%M%S")
        if (orb_start < meta_dict['startTime']) and (orb_stop > meta_dict['stopTime']):
            orbit_file_url = BASE_URL+'/'+ orb_dir +'/'+xml_orb.strip()
            orbit_file = os.path.basename(orbit_file_url)
            if os.path.exists(orbit_file):
                print("Orbit already downloaded: %s" % orbit_file)
                continue
            print("Downloading %s" % orbit_file_url)
            s = urllib2.urlopen(orbit_file_url)
            contents = s.read()
            xmlfile = open(orbit_file, 'w')
            xmlfile.write(contents)
            xmlfile.close()
    return orbit_file

####################################################
def parse_subswath_xml(xmlfile):
    '''Parse S1 subswath xml file and assign metadata parameters

    This function will parse the xml file and assign the values needed
    to a python dictionary
    '''
    xmldoc = ET.parse(xmlfile).getroot()
    meta_dict = {}
    meta_dict['missionId'] = xmldoc.find('.//adsHeader/missionId').text
    meta_dict['productType'] = xmldoc.find('.//adsHeader/productType').text
    meta_dict['polarisation'] = xmldoc.find('.//adsHeader/polarisation').text
    meta_dict['mode'] = xmldoc.find('.//adsHeader/mode').text
    meta_dict['swath'] = xmldoc.find('.//adsHeader/swath').text
    meta_dict['startTime'] =  datetime.datetime.strptime(xmldoc.find('.//adsHeader/startTime').text,"%Y-%m-%dT%H:%M:%S.%f")
    meta_dict['stopTime'] =  datetime.datetime.strptime(xmldoc.find('.//adsHeader/stopTime').text,"%Y-%m-%dT%H:%M:%S.%f")
    meta_dict['absoluteOrbitNumber'] = xmldoc.find('.//adsHeader/absoluteOrbitNumber').text
#    meta_dict['missionDataTakeId'] = xmldoc.find('.//adsHeader/missionDataTakeId').text
    meta_dict['flight_direction'] = xmldoc.find('.//generalAnnotation/productInformation/pass').text
    meta_dict['frequency'] = float(xmldoc.find('.//generalAnnotation/productInformation/radarFrequency').text)
    meta_dict['rangeSampleRate'] = float(xmldoc.find('.//generalAnnotation/productInformation/rangeSamplingRate').text)
    meta_dict['rangePixelSize'] = 299792458./(2.0*meta_dict['rangeSampleRate'])
    meta_dict['azimuthPixelSize'] = float(xmldoc.find('.//imageAnnotation/imageInformation/azimuthPixelSpacing').text)
    meta_dict['azimuthTimeInterval'] = float(xmldoc.find('.//imageAnnotation/imageInformation/azimuthTimeInterval').text)
    meta_dict['lines'] = int(xmldoc.find('.//swathTiming/linesPerBurst').text)
    meta_dict['samples'] = int(xmldoc.find('.//swathTiming/samplesPerBurst').text)
    meta_dict['startingRange'] = float(xmldoc.find('.//imageAnnotation/imageInformation/slantRangeTime').text)*299792458./2.0
    meta_dict['incidenceAngle'] = float(xmldoc.find('.//imageAnnotation/imageInformation/incidenceAngleMidSwath').text)
    meta_dict['prf'] = float(xmldoc.find('.//generalAnnotation/downlinkInformationList/downlinkInformation/prf').text)
    meta_dict['terrainHeight'] = float(xmldoc.find('.//generalAnnotation/terrainHeightList/terrainHeight/value').text)
    return meta_dict

####################################################
def calc_dop_orb(prm_file):
    ##### COMPUTE DOPPLER AND UPDATE PRM FILE #####
    log_file = os.path.splitext(prm_file)[0] + '.log'
    output = gmtsarutils.run_command('calc_dop_orb ' + prm_file + ' ' + log_file + ' 0 0')
    log_out = open(log_file).readlines()
    PRM = open(prm_file, 'a')
    for line in log_out:
        PRM.write(line)
    PRM.close()
    os.remove(log_file)

####################################################
def compute_baselines(masterDate):
    masterPRM = glob.glob("*"+masterDate+'*.PRM')[0]
    prmDict = gmtsarutils.read_prm(masterPRM)
    prmList = sorted(glob.glob('*PRM'))
    f = open('bl_list.txt','w')
    dates = []
    pbase = []
    for scene in prmList:
        temp_dict = gmtsarutils.read_prm(scene)
        date = os.path.splitext(scene)[0].split("_")[1]
        cmd = 'SAT_baseline ' + masterPRM + ' ' + scene
        print(cmd)
        output = gmtsarutils.run_command(cmd) 
        tmp = output.split('\n')
        outDict = {}
        for l in tmp:
            c = l.split("=")
            if len(c) < 2:
                next
            else:
                outDict[c[0].strip()] = str.replace(c[1], '\n', '').strip()
        dates.append(date)
        pbase.append(float(outDict['B_perpendicular']))
        f.write('%s %5.6f %5.6f %s\n' % (date,float(outDict['B_perpendicular']),float(outDict['B_parallel']),os.path.splitext(scene)[0]+'.SLC'))
    f.close()
    ### FIND MASTER DATE THAT MINIMIZES BASELINE ###
    dates = np.array(dates)
    pbase = np.array(pbase)
    optimal_ref = dates.flat[np.abs(pbase - np.mean(pbase)).argmin()]
    print("OPTIMAL REFERENCE DATE: %s" % optimal_ref)
    return optimal_ref

####################################################
def parse():
    '''Command line parser.'''
    parser = argparse.ArgumentParser(description='Align a stack of Sentinel-1 scenes')
    parser.add_argument('-s', action='store', type=str, dest='swath_num', required=True, help='Swath number (integer, without IW or EW)')
#    parser.add_argument('-ref', action='store', type=str, dest='ref_date', required=False, help='Reference (master) date to align SLCs')
    clos = parser.parse_args()
    return clos

if __name__ == '__main__':
    clos = parse()
    if len(sys.argv)<2:
        print("USAGE: tops_prepare_stack.py SUBSWATH\n  Example:\n  tops_prepare_stack.py 1\nThis command will extract the VV or HH IW1 subswath from each Sentinel-1 ZIP file in a raw directory to the SLC directory and create data.in")
        exit()
    safe_zip_list = sorted(glob.glob(os.getcwd()+"/raw/S1*_IW_SLC*.zip"))
    if not os.path.exists("SLC"):
        os.mkdir("SLC")
    os.chdir("SLC")
    datain_file = open("data.in",'w')
    for z in safe_zip_list:
        print("Working on %s" % z)
        tmp_tiff,tmp_xml = extract_tiff_xml(z,clos.swath_num)
        tmp_meta = parse_subswath_xml(tmp_xml)
        tmp_orbit_file = get_orbit(tmp_meta)
        tmp_meta['orbit_file'] = tmp_orbit_file
        tmp_meta['tiff'] = tmp_tiff
        tmp_meta['xml'] = tmp_xml
        tmp_meta['prefix'] = tmp_meta['swath']+'_'+tmp_meta['startTime'].strftime('%Y%m%d')
        tmp_meta['prm'] = tmp_meta['prefix']+'.PRM'
        output = gmtsarutils.run_command('make_s1a_tops %s %s %s 0' % (tmp_meta['xml'],tmp_meta['tiff'],tmp_meta['prefix']) )
        output = gmtsarutils.run_command('ext_orb_s1a %s %s %s' % (tmp_meta['prm'],tmp_meta['orbit_file'],tmp_meta['prefix']) )
        calc_dop_orb(tmp_meta['prm'])
        datain_file.write("%s:%s\n" %(os.path.splitext(tmp_tiff)[0],tmp_orbit_file))

    ref_date = compute_baselines(tmp_meta['startTime'].strftime('%Y%m%d'))
