'''
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
'''
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

# Custom Classes
import util.timeConv as tc
import util.nbrConv as nConv

logging.config.fileConfig('logging.conf')
logger = logging.getLogger()



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
    wrkt_tot_dist = nConv.convert(wrkt_df['dist_mi'].sum())
    wrkt_tot_dur = nConv.convert(wrkt_df['dur_sec'].sum())
    wrkt_tot_pace = wrkt_tot_dur / wrkt_tot_dist
    wrkt_tot_ele = nConv.convert(wrkt_df['sum_ele'].sum())
    wrkt_tot_ele_up = nConv.convert(wrkt_df['ele_up'].sum())
    wrkt_tot_ele_down = nConv.convert(wrkt_df['ele_down'].sum())

    # if wrktCat.replace(' ','_').lower() == 'Training':
    # wrkt_df['interval'].iloc[[0]] = 'Warm Up'
    # wrkt_df['interval'].iloc[[wrkt_df.index[-1]]] = 'Cool Down'

    # Calculate summary of intervals portion
    intvl_tot_dist = nConv.convert(wrkt_df['dist_mi'].iloc[1:-1].sum())
    intvl_tot_dur = nConv.convert(wrkt_df['dur_sec'].iloc[1:-1].sum())
    if intvl_tot_dist == 0:
        intvl_tot_pace = 0
    else:
        intvl_tot_pace = intvl_tot_dur / intvl_tot_dist
    intvl_tot_ele = nConv.convert(wrkt_df['sum_ele'].iloc[1:-1].sum())
    intvl_tot_ele_up = nConv.convert(wrkt_df['ele_up'].iloc[1:-1].sum())
    intvl_tot_ele_down = nConv.convert(wrkt_df['ele_down'].iloc[1:-1].sum())

    intvl_avg_dist = nConv.convert(wrkt_df['dist_mi'].iloc[1:-1].mean())
    intvl_avg_dur = nConv.convert(wrkt_df['dur_sec'].iloc[1:-1].mean())
    intvl_avg_pace = intvl_avg_dur / intvl_avg_dist
    intvl_avg_ele = nConv.convert(wrkt_df['sum_ele'].iloc[1:-1].mean())
    intvl_avg_ele_up = nConv.convert(wrkt_df['ele_up'].iloc[1:-1].mean())
    intvl_avg_ele_down = nConv.convert(wrkt_df['ele_down'].iloc[1:-1].mean())

    # if wrktCat.replace(' ','_').lower() == 'long_run':
    # Calculate summary of first and second halves of workout
    frst_half_intrvl = round(wrkt_df.shape[0]/2)
    wrkt_half_1_dist = nConv.convert(wrkt_df['dist_mi'].iloc[0:frst_half_intrvl].sum())
    wrkt_half_1_dur = nConv.convert(wrkt_df['dur_sec'].iloc[0:frst_half_intrvl].sum())
    if wrkt_half_1_dist == 0:
        wrkt_half_1_pace = 0
    else:
        wrkt_half_1_pace = wrkt_half_1_dur / wrkt_half_1_dist
    wrkt_half_1_ele = nConv.convert(wrkt_df['sum_ele'].iloc[0:frst_half_intrvl].sum())
    wrkt_half_1_ele_up = nConv.convert(wrkt_df['ele_up'].iloc[0:frst_half_intrvl].sum())
    wrkt_half_1_ele_down = nConv.convert(wrkt_df['ele_down'].iloc[0:frst_half_intrvl].sum())

    wrkt_half_2_dist = \
        nConv.convert(wrkt_df['dist_mi'].iloc[frst_half_intrvl:wrkt_df.shape[0]].sum())
    wrkt_half_2_dur = \
        nConv.convert(wrkt_df['dur_sec'].iloc[frst_half_intrvl:wrkt_df.shape[0]].sum())
    wrkt_half_2_pace = wrkt_half_2_dur / wrkt_half_2_dist
    wrkt_half_2_ele = nConv.convert(wrkt_df['sum_ele'].iloc[frst_half_intrvl:wrkt_df.shape[0]].sum())
    wrkt_half_2_ele_up = nConv.convert(wrkt_df['ele_up'].iloc[frst_half_intrvl:wrkt_df.shape[0]].sum())
    wrkt_half_2_ele_down = nConv.convert(wrkt_df['ele_down'].iloc[frst_half_intrvl:wrkt_df.shape[0]].sum())

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
            {'dist_mi': nConv.convert(wrkt_df['dist_mi'].iloc[0]), 'dur_sec':nConv.convert(wrkt_df['dur_sec'].iloc[0]), 'dur_str':wrkt_df['dur_str'].iloc[0], 'pace_sec':nConv.convert(wrkt_df['pace'].iloc[0]), 'pace_str': wrkt_df['pace_str'].iloc[0], 'sum_ele': wrkt_df['sum_ele'].iloc[0], 'ele_up':wrkt_df['ele_up'].iloc[0], 'ele_down':wrkt_df['ele_down'].iloc[0]}\
        , 'cool_down': \
            {'dist_mi': nConv.convert(wrkt_df['dist_mi'].iloc[-1]), 'dur_sec':nConv.convert(wrkt_df['dur_sec'].iloc[-1]), 'dur_str':wrkt_df['dur_str'].iloc[-1], 'pace_sec':nConv.convert(wrkt_df['pace'].iloc[-1]), 'pace_str': wrkt_df['pace_str'].iloc[-1], 'sum_ele': wrkt_df['sum_ele'].iloc[-1], 'ele_up':wrkt_df['ele_up'].iloc[-1], 'ele_down':wrkt_df['ele_down'].iloc[-1]}\
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
