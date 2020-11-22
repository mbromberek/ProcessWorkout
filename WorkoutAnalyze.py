#!/usr/bin/env python
# coding: utf-8

# First party classes
import os,glob,shutil
import re
import datetime, time
import configparser
import sys, getopt

# 3rd party classes
import numpy as np
import pandas as pd

# custom classes
import dao.files as fao
import util.timeConv as tc
import rungap.normWrkt as rgNorm


def printArgumentsHelp():
    print ('WorkoutAnalyze.py -i <inputfile> -o <outputdir>')
    print ("-i, --ifile arg  : Input filename to process")
    print ("-idir arg        : Input directory with file name")
    print ("-o, --odir arg   : Output directory for results")
    print ("--osplit arg     : Segments to generate in file, default is all (CURRENTLY NOT SETUP)")
    print ("                    options are mile, segment, kilometer, pause, all")


def main(argv):
    '''
    Steps
    1. Get config details
    2. Extract files
    3. Load files into activities and events data frames
    4. Clean up and merge the activities and events data frames
    5. Group activities by different splits
    6. Export activiies grouped by splits to CSV files
    '''
    config = configparser.ConfigParser()
    # progDir = os.path.dirname(os.path.abspath(__file__)) #might need to use this in actual Python script, but does not work in Jupyter Notebook
    progDir = os.path.abspath('')
    config.read(progDir + "/wrktAnalyzeConfig.txt")

    filename = config['analyze_inputs']['file_name']
    analyzeDir = config['analyze_inputs']['analyze_dir']
    tempDir = config['analyze_inputs']['temp_dir']
    outDir = config['analyze_outputs']['dir']

    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=", "idir=", "odir="])
    except getopt.GetoptError:
        printArgumentsHelp()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h': # Print help for input arguments
            printArgumentsHelp()
            sys.exit()
        elif opt in ("-i", "--ifile"):
            filename = arg
        elif opt in ("--idir"):
            analyzeDir = arg
        elif opt in ("-o", "--odir"):
            outDir = arg
    print ('Input file: ', filename)
    print ('Input directory: ', analyzeDir)

    fao.extract_files(filename, analyzeDir, tempDir)

    data = fao.get_workout_data(tempDir)

    actv_df = rgNorm.normalize_activity(data)

    '''
    # Group activities by mile and segment
    '''
    miles_df = rgNorm.group_actv(actv_df, 'mile')
    kilometers_df = rgNorm.group_actv(actv_df, 'kilometer')
    segments_df = rgNorm.group_actv(actv_df, 'segment')
    resume_pause_df = rgNorm.group_actv(actv_df, 'resume')

    '''
    # Export data frames to CSV for review
    '''
    fao.save_df(miles_df, outDir+'miles_split.csv')
    fao.save_df(segments_df, outDir+'segments_split.csv')
    fao.save_df(resume_pause_df, outDir+'pause_resume_split.csv')
    fao.save_df(actv_df, outDir+'activity.csv')
    actv_df.to_pickle(os.path.join(outDir, "activity.pickle"))
    print(actv_df.info())
    miles_df.to_pickle(os.path.join(outDir, "miles.pickle"))
    # miles_df = pd.read_pickle(os.path.join("/Users/mikeyb/Library/Mobile Documents/com~apple~CloudDocs/_Runs/analyze/results/", "miles.pickle"))

    fao.clean_dir(tempDir)

if __name__ == '__main__':
	main(sys.argv[1:])
