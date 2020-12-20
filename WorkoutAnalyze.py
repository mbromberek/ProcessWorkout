#!/usr/bin/env python
# coding: utf-8
'''
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
'''

# First party classes
import os,glob,shutil, subprocess
import re
import datetime, time
import configparser
import sys, getopt
import logging
import logging.config

# 3rd party classes
import numpy as np
import pandas as pd

# custom classes
import dao.files as fao
import util.timeConv as tc
import util.WrktSummary as wrktSum
import rungap.normWrkt as rgNorm

# tempDir = '/tmp/' #default to /tmp
logging.config.fileConfig('logging.conf')
logger = logging.getLogger()


def summarizeWrkoutSegments(segments_df):
    '''
    Get summary of Workout and write it to logs
    '''
    wrkt_summary = wrktSum.calcWrktSummary(segments_df.rename(columns={'segment': 'interval'}, inplace=False))
    logger.info('Workout Stats:')
    logger.info('Warm Up: ' \
        + wrkt_summary['warm_up']['dur_str'] + ' total, ' \
        + str(wrkt_summary['warm_up']['dist_mi']) + ' miles, ' \
        + wrkt_summary['warm_up']['pace_str'] + 'per mile, ' \
        + str(wrkt_summary['warm_up']['ele_up']) + ' ele up, ' \
        + str(wrkt_summary['warm_up']['ele_down']) + ' ele down' \
    )
    logger.info('Intervals: ' \
        + wrkt_summary['intvl_tot']['dur_str'] + ' total, ' \
        + str(wrkt_summary['intvl_tot']['dist_mi']) + ' miles, ' \
        + wrkt_summary['intvl_tot']['pace_str'] + 'per mile, '\
        + str(wrkt_summary['intvl_tot']['ele_up']) + ' ele up, ' \
        + str(wrkt_summary['intvl_tot']['ele_down']) + ' ele down' \
    )
    logger.info('Cool Down: ' \
        + wrkt_summary['cool_down']['dur_str'] + ' total, ' \
        + str(wrkt_summary['cool_down']['dist_mi']) + ' miles, ' \
        + wrkt_summary['cool_down']['pace_str'] + 'per mile, '\
        + str(wrkt_summary['cool_down']['ele_up']) + ' ele up, ' \
        + str(wrkt_summary['cool_down']['ele_down']) + ' ele down' \
    )

    # wrkt_sum_frmla = wrktSum.calcWrktSumFrmla(segments_df.rename(columns={'segment': 'interval'}, inplace=False))
    return wrkt_summary


def custSplits(actv_df, tempDir):
    '''
    Create a CSV file with a custom split column for the passed in activity. User can then add the split marks in the CSV and resave it as CSV with the same name.
    Job will use markers in the custom column to create a new grouping of splits.
    '''
    df = actv_df.copy()
    # 1) Add Empty Custom_Split column to passed in DataFrame
    df.insert(5,'custom', np.nan) #column will be added before other split indicators

    # 2) Export DF to CSV and Pickle (Pickle is not needed at this time)
    fao.save_df(df, tempDir,'temp_custom_split', frmt=['csv','pickle'])

    # 3) Pause job for user input
    # 4) Open CSV on users system
    openCmd = os.path.join(tempDir,'temp_custom_split.csv')
    logger.debug('Path to temp custom file: ' + openCmd)

    subprocess.run(args=['open', openCmd], cwd='/')

    # 5) User enters data to custom columns of spreadsheet and saves it to CSV of same name (maybe keep the file in Numbers)
    input("Update the temp_custom_split.csv file with custom splits. Then Press Enter to continue")

    # 6) Read updated CSV file (and original pickle if needed)
    edit_df = pd.read_csv(os.path.join(tempDir,'temp_custom_split.csv'))

    # 7) Remove all but the records that have a custom value and change the custom value to a sequential number
    edit_df.loc[0,'custom'] = 1
    cust_df = edit_df[edit_df['custom'].notna()][['date_time','custom']]
    cust_df.reset_index(inplace=True, drop=True)
    cust_df['custom'] = cust_df.index.get_level_values(0).values
    cust_df['custom'] = cust_df['custom'].astype('int64')
    cust_df['date_time'] = cust_df['date_time'].astype('datetime64')

    # 7) Update DF custom column with value from custom column in CSV
    df.drop(['custom'], axis=1, inplace=True)
    actv_cust_df = pd.merge(df, cust_df, how='left', on='date_time')

    # 8) In DF fillna based on the split data provided in the custom column
    actv_cust_df['custom'].fillna(method='ffill', inplace=True)

    # 9) Group using custom column
    return rgNorm.group_actv(actv_cust_df, 'custom')



def printArgumentsHelp():
    print ('WorkoutAnalyze.py -i <inputfile> -o <outputdir>')
    print ("-i, --ifile arg  : Input filename to process")
    print ("-o, --odir arg   : Output directory for results")
    print ("--splits arg     : Segments to split up file, ")
    print ("                    options are mile, kilometer, segment, pause, custom, all")
    print ("                    all option will generate mile, kilometer, segment, pause")
    print ("                    default is mile, segment, pause")

def getSplitOptions(arg):
    '''
    Parameger arg: comma delimited list of arguments for splitting the workout

    Converts passed in split argument to lower case and splits on comma
    Parses each argument doing needed transformations before adding to a list.
    Prints to the console if any arguments are invalid
    Removes duplicates from list of split arguments

    Returns list of split arguments
    '''
    splitOptions = []
    splitArgs = arg.lower().split(',')
    for split in splitArgs:
        if split == 'all':
            splitOptions.extend(['mile','segment','resume','kilometer'])
        elif split == 'pause':
            splitOptions.append('resume')
        elif split in ('custom','mile','segment','kilometer'):
            splitOptions.append(split)
        else:
            print("Invalid split argument: " + split)
    return(list(dict.fromkeys(splitOptions)))


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
    config.read(progDir + "/config.txt")

    logger.info('WorkoutAnalyze Start')

    tempDir = config['wrkt_analyze_inputs']['temp_dir']
    outDir = config['wrkt_analyze_outputs']['dir']

    customSplit = False
    splitOptions = []
    filename = ''

    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=", "odir=", "split="])
    except getopt.GetoptError:
        printArgumentsHelp()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            printArgumentsHelp()
            sys.exit()
        elif opt in ("-i", "--ifile"):
            filename = arg
        elif opt in ("-o", "--odir"):
            outDir = arg
        elif opt in ('--split'):
            splitOptions = getSplitOptions(arg)
    if splitOptions == []:
        splitOptions = config['wrkt_analyze']['dflt_split_opt'].split(',')

    if filename == '':
        filename = os.path.join(config['rungap']['backup_dir'], fao.getLatestFile(config['rungap']['backup_dir']))
    logger.info('Input file: ' + filename)
    logger.info('Split arguments: ' + str(splitOptions))

    fao.extract_files(filename, tempDir)

    data = fao.get_workout_data(tempDir)

    actv_df = rgNorm.normalize_activity(data)

    # if customSplit:
    #     cust_splits_df = custSplits(actv_df, tempDir)
    #     fao.save_df(cust_splits_df, outDir,'custom_split', frmt=['csv','pickle'])

    '''
    Group activities by different splits
    '''
    splitDict = {}
    for split in splitOptions:
        if split == 'custom':
            splitDict['custom'] = custSplits(actv_df, tempDir)
        else:
            splitDict[split] = rgNorm.group_actv(actv_df, split)

    '''
    # Export data frames to files for review
    '''
    for split in splitOptions:
        fao.save_df(splitDict[split], outDir, split + '_split', frmt=['csv','pickle'])

    # Always save the activity dataframe
    fao.save_df(actv_df, outDir,'activity', frmt=['csv','pickle'])

    fao.clean_dir(tempDir)

    if 'segment' in splitOptions:
        summarizeWrkoutSegments(splitDict['segment'])

    logger.info('WorkoutAnalyze End')


if __name__ == '__main__':
	main(sys.argv[1:])
