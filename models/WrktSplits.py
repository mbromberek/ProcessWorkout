'''
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
'''
# First party classes
import logging
import logging.config

# 3rd party classes
import numpy as np
import pandas as pd

# custom classes
import dao.files as fao
import rungap.normWrkt as rgNorm

def breakDownWrkt(dirName, fName = '', splitBy='segment'):
    '''
    WrktSplits.breakDownWrkt(dirName=<class 'str'>, splitBy='segment')

    Takes passed in directory from dirName to get workout data
    normalizes the workout data
    groups the workout data by the splitBy
    returns a List of Dictionary values for the workout based on the splitBy

    Parameters: dirName: directory with workout files to process
                splitBy: str{'segment','mile','kilometer','resume'}
    '''
    if fName == '':
        data = fao.get_workout_data(dirName)
    else:
        data = fao.get_workout_data_from_file(dirName + '/' + fName)

    actv_df = rgNorm.normalize_activity(data)
    df = rgNorm.group_actv(actv_df, splitBy)
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
