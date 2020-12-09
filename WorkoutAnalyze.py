#!/usr/bin/env python
# coding: utf-8

# First party classes
import os,glob,shutil
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
import rungap.normWrkt as rgNorm

tempDir = '/tmp/' #default to /tmp
logging.config.fileConfig('logging.conf')
logger = logging.getLogger('root')

def custSplits(actv_df):
    '''
    Create a CSV file with a custom split column for the passed in activity. User can then add the split marks in the CSV and resave it as CSV with the same name.
    Job will use the splits in the custom column to create a new grouping of splits that those.
    Each entry in CSV file should be unique
    '''
    df = actv_df.copy()
    # 1) Add Empty Custom_Split column to passed in DataFrame
    df['custom'] = np.nan
    df.loc[0,'custom'] = 1

    # 2) Export DF to CSV and Pickle (Pickle is not needed at this time)
    fao.save_df(df, tempDir,'temp_custom_split', frmt=['csv','pickle'])

    # 3) Pause job for user input
    # 4) Open CSV on users system
    # 5) User enters data to custom columns of spreadsheet and saves it to CSV of same name (maybe keep the file in Numbers)
    input("Update the temp_custom_split.csv file with custom splits. Then Press Enter to continue")

    # 6) Read updated CSV file (and original pickle if needed)
    edit_df = pd.read_csv(os.path.join(tempDir,'temp_custom_split.csv'))
    cust_df = edit_df[['date_time','custom']].copy()
    cust_df['date_time'] = cust_df['date_time'].astype('datetime64')

    # 7) Update DF custom column with value from custom column in CSV
    df.drop(['custom'], axis=1, inplace=True)
    actv_cust_df = pd.merge(df, cust_df, how='left', on='date_time')

    # 8) In DF fillna based on the split data provided in the custom column
    actv_cust_df['custom'].fillna(method='ffill', inplace=True)

    # 9) Group using custom column
    return rgNorm.group_actv(actv_cust_df, 'custom')

def calcWrktSummary(splits_df, wrktCat='Training'):
    '''
    splits_df = DataFrame of workout that is grouped by mile, kilometers, pauses, or segments
    wrktCat is the category for the workout, values can be Training or 'Long Run'
    Calculate summary of workout based on Category of workout.
    For Training calculate the Workout portions for Time, Distance, and avg Pace
    For Long Run calculate First Half and Second Half Time, Distance, and avg Pace
    '''
    wrkt_df = splits_df[['interval','avg_hr','dur_sec','dist_mi','pace','dur_str','pace_str','sum_ele','ele_up','ele_down']].copy()

    # Calculate summary of total workout
    wrkt_tot_dist = wrkt_df['dist_mi'].sum()
    wrkt_tot_dur = wrkt_df['dur_sec'].sum()
    wrkt_tot_pace = wrkt_tot_dur / wrkt_tot_dist
    wrkt_tot_ele = wrkt_df['sum_ele'].sum()
    wrkt_tot_ele_up = wrkt_df['ele_up'].sum()
    wrkt_tot_ele_down = wrkt_df['ele_down'].sum()

    # if wrktCat.replace(' ','_').lower() == 'Training':
    # wrkt_df['interval'].iloc[[0]] = 'Warm Up'
    # wrkt_df['interval'].iloc[[wrkt_df.index[-1]]] = 'Cool Down'

    # Calculate summary of intervals portion
    intvl_tot_dist = wrkt_df['dist_mi'].iloc[1:-1].sum()
    intvl_tot_dur = wrkt_df['dur_sec'].iloc[1:-1].sum()
    intvl_tot_pace = intvl_tot_dur / intvl_tot_dist
    intvl_tot_ele = wrkt_df['sum_ele'].iloc[1:-1].sum()
    intvl_tot_ele_up = wrkt_df['ele_up'].iloc[1:-1].sum()
    intvl_tot_ele_down = wrkt_df['ele_down'].iloc[1:-1].sum()

    intvl_avg_dist = wrkt_df['dist_mi'].iloc[1:-1].mean()
    intvl_avg_dur = wrkt_df['dur_sec'].iloc[1:-1].mean()
    intvl_avg_pace = intvl_avg_dur / intvl_avg_dist
    intvl_avg_ele = wrkt_df['sum_ele'].iloc[1:-1].mean()
    intvl_avg_ele_up = wrkt_df['ele_up'].iloc[1:-1].mean()
    intvl_avg_ele_down = wrkt_df['ele_down'].iloc[1:-1].mean()

    # if wrktCat.replace(' ','_').lower() == 'long_run':
    # Calculate summary of first and second halves of workout
    frst_half_intrvl = round(wrkt_df.shape[0]/2)
    wrkt_half_1_dist = wrkt_df['dist_mi'].iloc[0:frst_half_intrvl].sum()
    wrkt_half_1_dur = wrkt_df['dur_sec'].iloc[0:frst_half_intrvl].sum()
    wrkt_half_1_pace = wrkt_half_1_dur / wrkt_half_1_dist
    wrkt_half_1_ele = wrkt_df['sum_ele'].iloc[0:frst_half_intrvl].sum()
    wrkt_half_1_ele_up = wrkt_df['ele_up'].iloc[0:frst_half_intrvl].sum()
    wrkt_half_1_ele_down = wrkt_df['ele_down'].iloc[0:frst_half_intrvl].sum()

    wrkt_half_2_dist = \
        wrkt_df['dist_mi'].iloc[frst_half_intrvl:wrkt_df.shape[0]].sum()
    wrkt_half_2_dur = \
        wrkt_df['dur_sec'].iloc[frst_half_intrvl:wrkt_df.shape[0]].sum()
    wrkt_half_2_pace = wrkt_half_2_dur / wrkt_half_2_dist
    wrkt_half_2_ele = wrkt_df['sum_ele'].iloc[frst_half_intrvl:wrkt_df.shape[0]].sum()
    wrkt_half_2_ele_up = wrkt_df['ele_up'].iloc[frst_half_intrvl:wrkt_df.shape[0]].sum()
    wrkt_half_2_ele_down = wrkt_df['ele_down'].iloc[frst_half_intrvl:wrkt_df.shape[0]].sum()

    # The * is needed for tc.breakTimeFromSeconds to expand the three fields being returned
    wrkt_dict = {\
        'intvl_tot': \
            {'dist_mi': intvl_tot_dist, 'dur_sec':intvl_tot_dur, 'dur_str':tc.formatNumbersTime(*tc.breakTimeFromSeconds(intvl_tot_dur)), 'pace_sec':intvl_tot_pace, 'pace_str': tc.formatNumbersTime(*tc.breakTimeFromSeconds(intvl_tot_pace)), 'sum_ele': intvl_tot_ele, 'ele_up':intvl_tot_ele_up, 'ele_down':intvl_tot_ele_down}\
        , 'intvl_avg': \
            {'dist_mi': intvl_avg_dist, 'dur_sec':intvl_avg_dur, 'dur_str':tc.formatNumbersTime(*tc.breakTimeFromSeconds(intvl_avg_dur)), 'pace_sec':intvl_avg_pace, 'pace_str': tc.formatNumbersTime(*tc.breakTimeFromSeconds(intvl_avg_pace)), 'sum_ele': intvl_avg_ele, 'ele_up':intvl_avg_ele_up, 'ele_down':intvl_avg_ele_down}\
        , 'wrkt_tot':\
            {'dist_mi': wrkt_tot_dist, 'dur_sec':wrkt_tot_dur, 'dur_str':tc.formatNumbersTime(*tc.breakTimeFromSeconds(wrkt_tot_dur)), 'pace':wrkt_tot_pace, 'pace_str': tc.formatNumbersTime(*tc.breakTimeFromSeconds(wrkt_tot_pace)), 'sum_ele': wrkt_tot_ele, 'ele_up':wrkt_tot_ele_up, 'ele_down':wrkt_tot_ele_down}\
        , 'frst_half': \
            {'dist_mi': wrkt_half_1_dist, 'dur_sec':wrkt_half_1_dur, 'dur_str':tc.formatNumbersTime(*tc.breakTimeFromSeconds(wrkt_half_1_dur)), 'pace_sec':wrkt_half_1_pace, 'pace_str': tc.formatNumbersTime(*tc.breakTimeFromSeconds(wrkt_half_1_pace)), 'sum_ele': wrkt_half_1_ele, 'ele_up':wrkt_half_1_ele_up, 'ele_down':wrkt_half_1_ele_down}\
        , 'scnd_half': \
            {'dist_mi': wrkt_half_2_dist, 'dur_sec':wrkt_half_2_dur, 'dur_str':tc.formatNumbersTime(*tc.breakTimeFromSeconds(wrkt_half_2_dur)), 'pace_sec':wrkt_half_2_pace, 'pace_str': tc.formatNumbersTime(*tc.breakTimeFromSeconds(wrkt_half_2_pace)), 'sum_ele': wrkt_half_2_ele, 'ele_up':wrkt_half_2_ele_up, 'ele_down':wrkt_half_2_ele_down}\
        , 'warm_up': \
            {'dist_mi': wrkt_df['dist_mi'].iloc[0], 'dur_sec':wrkt_df['dur_sec'].iloc[0], 'dur_str':wrkt_df['dur_str'].iloc[0], 'pace_sec':wrkt_df['pace'].iloc[0], 'pace_str': wrkt_df['pace_str'].iloc[0], 'sum_ele': wrkt_df['sum_ele'].iloc[0], 'ele_up':wrkt_df['ele_up'].iloc[0], 'ele_down':wrkt_df['ele_down'].iloc[0]}\
        , 'cool_down': \
            {'dist_mi': wrkt_df['dist_mi'].iloc[-1], 'dur_sec':wrkt_df['dur_sec'].iloc[-1], 'dur_str':wrkt_df['dur_str'].iloc[-1], 'pace_sec':wrkt_df['pace'].iloc[-1], 'pace_str': wrkt_df['pace_str'].iloc[-1], 'sum_ele': wrkt_df['sum_ele'].iloc[-1], 'ele_up':wrkt_df['ele_up'].iloc[-1], 'ele_down':wrkt_df['ele_down'].iloc[-1]}\
    }
    logger.debug(wrkt_dict)
    return wrkt_dict

def calcWrktSumFrmla(splits_df, wrktCat='Training'):
    '''
    Create Excel/Numbers functions for calculating workout summary
    splits_df = DataFrame of workout that is grouped by mile, kilometers, pauses, or segments
    wrktCat is the category for the workout, values can be Training or 'Long Run'
    Calculate summary of workout based on Category of workout.
    For Training calculate the Workout portions for Time, Distance, and avg Pace
    For Long Run calculate First Half and Second Half Time, Distance, and avg Pace
    '''
    wrkt_df = splits_df[['interval','avg_hr','dur_sec','dist_mi','pace','dur_str','pace_str']].copy()

    wrkt_tot_dist = '=sum(B:B)'
    wrkt_tot_dur = '=sum(C:C)'
    wrkt_tot_pace = '"=" & name of cell 2 & "/" & name of cell 3'
    wrkt_tot_ele = '=sum(F:F)'
    wrkt_tot_ele_up = '=sum(G:G)'
    wrkt_tot_ele_down = '=sum(H:H)'

    # Calculate summary of intervals portion
    intvl_tot_dist = '=sum(B3:B' + str(wrkt_df.shape[0]) + ')'
    intvl_tot_dur = '=sum(C3:C' + str(wrkt_df.shape[0]) + ')'
    intvl_tot_pace = '"=" & name of cell 2 & "/" & name of cell 3'
    intvl_tot_ele = '=sum(F3:F' + str(wrkt_df.shape[0]) + ')'
    intvl_tot_ele_up = '=sum(G3:G' + str(wrkt_df.shape[0]) + ')'
    intvl_tot_ele_down = '=sum(H3:H' + str(wrkt_df.shape[0]) + ')'

    # Calculate summary of total workout
    intvl_avg_dist = '=avg(B3:B' + str(wrkt_df.shape[0]) + ')'
    intvl_avg_dur = '=avg(C3:C' + str(wrkt_df.shape[0]) + ')'
    intvl_avg_pace = '"=" & name of cell 2 & "/" & name of cell 3'
    intvl_avg_ele = '=sum(F3:F' + str(wrkt_df.shape[0]) + ')'
    intvl_avg_ele_up = '=sum(G3:G' + str(wrkt_df.shape[0]) + ')'
    intvl_avg_ele_down = '=sum(H3:H' + str(wrkt_df.shape[0]) + ')'

    # Calculate summary of first and second halves of workout
    frst_half_intrvl = round(wrkt_df.shape[0]/2)+1
    wrkt_half_1_dist = '=sum(B2:B' + str(frst_half_intrvl) + ')'
    wrkt_half_1_dur = '=sum(C2:C' + str(frst_half_intrvl) + ')'
    wrkt_half_1_pace = '"=" & name of cell 2 & "/" & name of cell 3'
    wrkt_half_1_ele = '=sum(F2:F' + str(frst_half_intrvl) + ')'
    wrkt_half_1_ele_up = '=sum(G2:G' + str(frst_half_intrvl) + ')'
    wrkt_half_1_ele_down = '=sum(H2:H' + str(frst_half_intrvl) + ')'

    wrkt_half_2_dist = '=sum(B' + str(frst_half_intrvl+1) + ':B' + str(wrkt_df.shape[0]+1) + ')'
    wrkt_half_2_dur = '=sum(C' + str(frst_half_intrvl+1) + ':C' + str(wrkt_df.shape[0]+1) + ')'
    wrkt_half_2_pace = '"=" & name of cell 2 & "/" & name of cell 3'
    wrkt_half_2_ele = '=sum(F' + str(frst_half_intrvl+1) + ':F' + str(wrkt_df.shape[0]+1) + ')'
    wrkt_half_2_ele_up = '=sum(G' + str(frst_half_intrvl+1) + ':G' + str(wrkt_df.shape[0]+1) + ')'
    wrkt_half_2_ele_down = '=sum(H' + str(frst_half_intrvl+1) + ':H' + str(wrkt_df.shape[0]+1) + ')'

    wrkt_dict = {\
        'intvl_tot': \
            {'dist_mi': intvl_tot_dist, 'dur_str':intvl_tot_dur, 'pace_str':intvl_tot_pace, 'sum_ele': intvl_tot_ele, 'ele_up':intvl_tot_ele_up, 'ele_down':intvl_tot_ele_down}\
        , 'intvl_avg': \
            {'dist_mi': intvl_avg_dist, 'dur_str':intvl_avg_dur, 'pace_str':intvl_avg_pace, 'sum_ele': intvl_avg_ele, 'ele_up':intvl_avg_ele_up, 'ele_down':intvl_avg_ele_down}\
        , 'wrkt_tot':\
            {'dist_mi': wrkt_tot_dist, 'dur_str':wrkt_tot_dur, 'pace_str':wrkt_tot_pace, 'sum_ele': wrkt_tot_ele, 'ele_up':wrkt_tot_ele_up, 'ele_down':wrkt_tot_ele_down}\
        , 'frst_half': \
            {'dist_mi': wrkt_half_1_dist, 'dur_str':wrkt_half_1_dur, 'pace_str':wrkt_half_1_pace, 'sum_ele': wrkt_half_1_ele, 'ele_up':wrkt_half_1_ele_up, 'ele_down':wrkt_half_1_ele_down}\
        , 'scnd_half': \
            {'dist_mi': wrkt_half_2_dist, 'dur_str':wrkt_half_2_dur, 'pace_str':wrkt_half_2_pace, 'sum_ele': wrkt_half_2_ele, 'ele_up':wrkt_half_2_ele_up, 'ele_down':wrkt_half_2_ele_down}\

    }

    logger.debug(wrkt_dict)
    return wrkt_dict


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

    '''
    Setup logging
    '''

    filename = config['analyze_inputs']['file_name']
    analyzeDir = config['analyze_inputs']['analyze_dir']
    tempDir = config['analyze_inputs']['temp_dir']
    outDir = config['analyze_outputs']['dir']

    customSplit = False

    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=", "idir=", "odir=", "custom"])
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
        elif opt in ("--custom"):
            customSplit = True
    logger.info('Input file: ' + filename)
    logger.info('Input directory: ' + analyzeDir)

    fao.extract_files(filename, analyzeDir, tempDir)

    data = fao.get_workout_data(tempDir)

    actv_df = rgNorm.normalize_activity(data)

    '''
    TODO
    '''
    if customSplit:
        cust_splits_df = custSplits(actv_df)
        fao.save_df(cust_splits_df, outDir,'custom_split', frmt=['csv','pickle'])

    '''
    # Group activities by mile and segment
    '''
    miles_df = rgNorm.group_actv(actv_df, 'mile')
    kilometers_df = rgNorm.group_actv(actv_df, 'kilometer')
    segments_df = rgNorm.group_actv(actv_df, 'segment')
    resume_pause_df = rgNorm.group_actv(actv_df, 'resume')

    '''
    # Export data frames to files for review
    '''
    fao.save_df(miles_df, outDir,'miles_split', frmt=['csv','pickle'])
    fao.save_df(actv_df, outDir,'activity', frmt=['csv','pickle'])
    fao.save_df(segments_df, outDir,'segments_split', frmt=['csv','pickle'])
    fao.save_df(resume_pause_df, outDir,'pause_split', frmt=['csv'])

    fao.clean_dir(tempDir)

    '''
    Get summary of Workout
    '''
    # segments_df.rename(columns={splitBy: 'interval'}, inplace=False)
    wrkt_summary = calcWrktSummary(segments_df.rename(columns={'segment': 'interval'}, inplace=False))
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

    wrkt_sum_frmla = calcWrktSumFrmla(segments_df.rename(columns={'segment': 'interval'}, inplace=False))



if __name__ == '__main__':
	main(sys.argv[1:])
