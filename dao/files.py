#!/usr/bin/env python
# coding: utf-8
'''
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
'''
"""
Functions for accessing and updating files
"""

# First party classes
import zipfile
import json
import os,glob,shutil
import re
import datetime, time

def get_workout_data(curr_dir):
    """
    Parses files and directories in the passed curr_dir till finds a file
    that ends in rungap.json. Then loads that json data to a Dictionary.
    Returns the Dictionary storing the json data.
    """
    data = ''
    jsonFileRegex = re.compile(r'(rungap.json)$')
    jsonExtRegex = re.compile(r'(.json)$')

    for filename in os.listdir(curr_dir):
        if jsonFileRegex.search(filename):
            with open(os.path.join(curr_dir, filename)) as data_file:
                data = json.load(data_file)
                break
    return data

def file_with_ext(curr_dir, ext):
    extRegex = re.compile(r'(.' + ext + ')$')
    for filename in os.listdir(curr_dir):
        if extRegex.search(filename):
            return filename
    return ''


def get_workout_data_from_file(fNamePath):
    """
    Parses passed files and loads that json data to a Dictionary.
    Returns the Dictionary storing the json data.
    """
    data = ''
    with open(fNamePath) as data_file:
        data = json.load(data_file)
    return data

def extract_files(fname, dest_dir, src_dir=''):
    """
    Extract filename in analyzeDir and put output into tempDir
    """
    z = zipfile.ZipFile(src_dir + fname,mode='r')
    z.extractall(path=dest_dir)


def save_df(df, outDir, outName, frmt='csv'):
    '''
    Save passed dataframe to specified output formats
    Output format can be passed as a list to save as multiple formats.
    Default output format is csv. Options are csv and pickle
    '''
    if not (isinstance(frmt, list)):
        frmt = [frmt]
    for outFrmt in frmt:
        if outFrmt == 'csv':
            df.to_csv(os.path.join(outDir, outName) + '.csv')
        elif outFrmt == 'pickle':
            df.to_pickle(os.path.join(outDir, outName) + '.pickle')
        # elif outFrmt == 'json':
            # df.to_json(os.path.join(outDir, outName) + '.json',orient='index')
        # elif outFrmt == 'wrktIntrvlJson':
        else:
            logger.error('Invalid Format: ' + outFrmt)


def clean_dir(dir):
    files = glob.glob(dir + '/*')
    for f in files:
        os.remove(f)

def listdir_fullpath(d):
    '''
    get full directory path for files in passed directory
    '''
    return [os.path.join(d, f) for f in os.listdir(d)]

def getLatestFile(d):
    '''
    get latest filename from passed in directory
    '''
    fileLst = glob.glob(os.path.join(d,'*'))
    latestFile = max(fileLst, key=os.path.getctime)
    return latestFile
