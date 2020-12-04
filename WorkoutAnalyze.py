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

def calcWrktSummary(splits_df, wrktCat='Training'):
    '''
    splits_df = DataFrame of workout that is grouped by mile, kilometers, pauses, or segments
    wrktCat is the category for the workout, values can be Training or 'Long Run'
    Calculate summary of workout based on Category of workout.
    For Training calculate the Workout portions for Time, Distance, and avg Pace
    For Long Run calculate First Half and Second Half Time, Distance, and avg Pace
    '''
    wrkt_df = splits_df[['interval','avg_hr','dur_sec','dist_mi','pace','dur_str','pace_str']].copy()

    # Calculate summary of total workout
    wrkt_tot_dist = wrkt_df['dist_mi'].sum()
    wrkt_tot_dur = wrkt_df['dur_sec'].sum()
    wrkt_tot_pace = wrkt_tot_dur / wrkt_tot_dist

    # if wrktCat.replace(' ','_').lower() == 'Training':
    # wrkt_df['interval'].iloc[[0]] = 'Warm Up'
    # wrkt_df['interval'].iloc[[wrkt_df.index[-1]]] = 'Cool Down'

    # Calculate summary of intervals portion
    intvl_tot_dist = wrkt_df['dist_mi'].iloc[1:-1].sum()
    intvl_tot_dur = wrkt_df['dur_sec'].iloc[1:-1].sum()
    intvl_tot_pace = intvl_tot_dur / intvl_tot_dist

    intvl_avg_dist = wrkt_df['dist_mi'].iloc[1:-1].mean()
    intvl_avg_dur = wrkt_df['dur_sec'].iloc[1:-1].mean()
    intvl_avg_pace = intvl_avg_dur / intvl_avg_dist

    # if wrktCat.replace(' ','_').lower() == 'long_run':
    # Calculate summary of first and second halves of workout
    frst_half_intrvl = round(wrkt_df.shape[0]/2)
    wrkt_half_1_dist = wrkt_df['dist_mi'].iloc[0:frst_half_intrvl].sum()
    wrkt_half_1_dur = wrkt_df['dur_sec'].iloc[0:frst_half_intrvl].sum()
    wrkt_half_1_pace = wrkt_half_1_dur / wrkt_half_1_dist

    wrkt_half_2_dist = \
        wrkt_df['dist_mi'].iloc[frst_half_intrvl:wrkt_df.shape[0]].sum()
    wrkt_half_2_dur = \
        wrkt_df['dur_sec'].iloc[frst_half_intrvl:wrkt_df.shape[0]].sum()
    wrkt_half_2_pace = wrkt_half_2_dur / wrkt_half_2_dist

    # The * is needed for tc.breakTimeFromSeconds to expand the three fields being returned
    wrkt_dict = {\
        'intvl_tot': \
            {'dist_mi': intvl_tot_dist, 'dur_sec':intvl_tot_dur, 'dur_str':tc.formatNumbersTime(*tc.breakTimeFromSeconds(intvl_tot_dur)), 'pace_sec':intvl_tot_pace, 'pace_str': tc.formatNumbersTime(*tc.breakTimeFromSeconds(intvl_tot_pace))}\
        , 'intvl_avg': \
            {'dist_mi': intvl_avg_dist, 'dur_sec':intvl_avg_dur, 'dur_str':tc.formatNumbersTime(*tc.breakTimeFromSeconds(intvl_avg_dur)), 'pace_sec':intvl_avg_pace, 'pace_str': tc.formatNumbersTime(*tc.breakTimeFromSeconds(intvl_avg_pace))}\
        , 'wrkt_tot':\
            {'dist_mi': wrkt_tot_dist, 'dur_sec':wrkt_tot_dur, 'dur_str':tc.formatNumbersTime(*tc.breakTimeFromSeconds(wrkt_tot_dur)), 'pace':wrkt_tot_pace, 'pace_str': tc.formatNumbersTime(*tc.breakTimeFromSeconds(wrkt_tot_pace))}\
        , 'frst_half': \
            {'dist_mi': wrkt_half_1_dist, 'dur_sec':wrkt_half_1_dur, 'dur_str':tc.formatNumbersTime(*tc.breakTimeFromSeconds(wrkt_half_1_dur)), 'pace_sec':wrkt_half_1_pace, 'pace_str': tc.formatNumbersTime(*tc.breakTimeFromSeconds(wrkt_half_1_pace))}\
        , 'scnd_half': \
            {'dist_mi': wrkt_half_2_dist, 'dur_sec':wrkt_half_2_dur, 'dur_str':tc.formatNumbersTime(*tc.breakTimeFromSeconds(wrkt_half_2_dur)), 'pace_sec':wrkt_half_2_pace, 'pace_str': tc.formatNumbersTime(*tc.breakTimeFromSeconds(wrkt_half_2_pace))}\
        , 'warm_up': \
            {'dist_mi': wrkt_df['dist_mi'].iloc[0], 'dur_sec':wrkt_df['dur_sec'].iloc[0], 'dur_str':wrkt_df['dur_str'].iloc[0], 'pace_sec':wrkt_df['pace'].iloc[0], 'pace_str': wrkt_df['pace_str'].iloc[0]}\
        , 'cool_down': \
            {'dist_mi': wrkt_df['dist_mi'].iloc[-1], 'dur_sec':wrkt_df['dur_sec'].iloc[-1], 'dur_str':wrkt_df['dur_str'].iloc[-1], 'pace_sec':wrkt_df['pace'].iloc[-1], 'pace_str': wrkt_df['pace_str'].iloc[-1]}\
    }

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

    # Calculate summary of intervals portion
    intvl_tot_dist = '=sum(B3:B' + str(wrkt_df.shape[0]) + ')'
    intvl_tot_dur = '=sum(C3:C' + str(wrkt_df.shape[0]) + ')'
    intvl_tot_pace = '"=" & name of cell 2 & "/" & name of cell 3'

    # Calculate summary of total workout
    intvl_avg_dist = '=avg(B3:B' + str(wrkt_df.shape[0]) + ')'
    intvl_avg_dur = '=avg(C3:C' + str(wrkt_df.shape[0]) + ')'
    intvl_avg_pace = '"=" & name of cell 2 & "/" & name of cell 3'

    # Calculate summary of first and second halves of workout
    frst_half_intrvl = round(wrkt_df.shape[0]/2)+1
    wrkt_half_1_dist = '=sum(B2:B' + str(frst_half_intrvl) + ')'
    wrkt_half_1_dur = '=sum(C2:C' + str(frst_half_intrvl) + ')'
    wrkt_half_1_pace = '"=" & name of cell 2 & "/" & name of cell 3'

    wrkt_half_2_dist = '=sum(B' + str(frst_half_intrvl+1) + ':B' + str(wrkt_df.shape[0]+1) + ')'
    wrkt_half_2_dur = '=sum(C' + str(frst_half_intrvl+1) + ':C' + str(wrkt_df.shape[0]+1) + ')'
    wrkt_half_2_pace = '"=" & name of cell 2 & "/" & name of cell 3'

    wrkt_dict = {\
        'intvl_tot': \
            {'dist_mi': intvl_tot_dist, 'dur_str':intvl_tot_dur, 'pace_str':intvl_tot_pace}\
        , 'intvl_avg': \
            {'dist_mi': intvl_avg_dist, 'dur_str':intvl_avg_dur, 'pace_str':intvl_avg_pace}\
        , 'wrkt_tot':\
            {'dist_mi': wrkt_tot_dist, 'dur_str':wrkt_tot_dur, 'pace_str':wrkt_tot_pace}\
        , 'frst_half': \
            {'dist_mi': wrkt_half_1_dist, 'dur_str':wrkt_half_1_dur, 'pace_str':wrkt_half_1_pace}\
        , 'scnd_half': \
            {'dist_mi': wrkt_half_2_dist, 'dur_str':wrkt_half_2_dur, 'pace_str':wrkt_half_2_pace}\

    }

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
    print(wrkt_summary)
    print('Workout Stats:')
    print('Warm Up: ' \
        + wrkt_summary['warm_up']['dur_str'] + ' total, ' \
        + str(wrkt_summary['warm_up']['dist_mi']) + ' miles, ' \
        + wrkt_summary['warm_up']['pace_str']  \
    )
    print('Intervals: ' \
        + wrkt_summary['intvl_tot']['dur_str'] + ' total, ' \
        + str(wrkt_summary['intvl_tot']['dist_mi']) + ' miles, ' \
        + wrkt_summary['intvl_tot']['pace_str']  \
    )
    print('Cool Down: ' \
        + wrkt_summary['cool_down']['dur_str'] + ' total, ' \
        + str(wrkt_summary['cool_down']['dist_mi']) + ' miles, ' \
        + wrkt_summary['cool_down']['pace_str']  \
    )

    print('')
    wrkt_sum_frmla = calcWrktSumFrmla(segments_df.rename(columns={'segment': 'interval'}, inplace=False))
    print(wrkt_sum_frmla)


if __name__ == '__main__':
	main(sys.argv[1:])
