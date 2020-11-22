#!/usr/bin/env python
# coding: utf-8
"""
Functions for accessing and updating files
"""

# First party classes
import zipfile
import json
import os,glob,shutil
import re
import datetime, time


def getFileName():
    """
    Eventually change to use command line arguments instead of hardcoding
    Get filename from first parameter passed to the program
    Return the filename as text
    """
    filename = '2020-10-15_16-16-25_hk_1602796585.zip'
    return filename

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
            with open(curr_dir + filename) as data_file:
                data = json.load(data_file)
                break
    return data


def extract_files(fname, src_dir, dest_dir):
    """
    Extract filename in analyzeDir and put output into tempDir
    """
    z = zipfile.ZipFile(src_dir + fname,mode='r')
    z.extractall(path=dest_dir)


def save_df(df, out_name):
    df.to_csv(out_name)

def clean_dir(dir):
    files = glob.glob(dir + '/*')
    for f in files:
        os.remove(f)