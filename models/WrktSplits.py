'''
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
'''
# First party classes
import os
import logging
import logging.config

# 3rd party classes
import numpy as np
import pandas as pd

# custom classes
import dao.files as fao
import NormalizeWorkout.parse.rungapParse as rgNorm
import NormalizeWorkout.WrktSplits as splits

def breakDownWrkt(dirName, fName = '', splitBy='lap'):
    '''
    WrktSplits.breakDownWrkt(dirName=<class 'str'>, splitBy='lap')

    Takes passed in directory from dirName to get workout data
    normalizes the workout data
    groups the workout data by the splitBy
    returns a List of Dictionary values for the workout based on the splitBy

    Parameters: dirName: directory with workout files to process
                splitBy: str{'lap','mile','kilometer','resume'}
    '''
    if fName == '':
        data = fao.get_workout_data(dirName)
    else:
        if os.path.exists(dirName + '/' + fName):
            data = fao.get_workout_data_from_file(dirName + '/' + fName)
        else:
            return None

    actv_df = rgNorm.normalize_activity(data)
    df = splits.group_actv(actv_df, splitBy)
    df.rename(columns={splitBy: 'interval'}, inplace=True)
    return df

def calcTrngType(wrktSegments, wrktCat):
    if wrktCat != 'Training':
        return wrktCat

    if wrktSegments.shape[0] in (3, 4):
        # If number of records is 3 or 4the workout is likely a Tempo run
        return 'Tempo'
    else:
        return 'Workout'

def summarizeWrktSplit(actv_df, summarizeBy):
    # actv_df.rename(columns={'hr': 'avg_hr'}, inplace=True)
    actv_df['ele_up'] = actv_df[actv_df['delta_ele_ft']>0]['delta_ele_ft']
    actv_df['ele_down'] = actv_df[actv_df['delta_ele_ft']<0]['delta_ele_ft']

    df = actv_df.groupby([summarizeBy]).agg(
        max_time=('dur_sec','max')
        , min_time=('dur_sec', 'min')
        , avg_hr=('hr','mean')
        , max_dist=('dist_mi','max')
        , min_dist=('dist_mi','min')
        , ele_up = ('ele_up','sum')
        , ele_down = ('ele_down','sum')
    )
    df['dur_sec'] = df['max_time'] - df['min_time']
    df['dist_mi'] =  df['max_dist'] - df['min_dist']
    df['interval'] = df.index.values

    return df
