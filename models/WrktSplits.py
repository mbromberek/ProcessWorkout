# 3rd party classes
import numpy as np
import pandas as pd

# custom classes
import dao.files as fao
# import util.timeConv as tc
import rungap.normWrkt as rgNorm

def breakDownWrkt(dirName, splitBy='segment'):
    '''
    WrktSplits.breakDownWrkt(dirName=<class 'str'>, splitBy='segment')

    Takes passed in directory from dirName to get workout data
    normalizes the workout data
    groups the workout data by the splitBy
    returns a List of Dictionary values for the workout based on the splitBy

    Parameters: dirName: directory with workout files to process
                splitBy: str{'segment','mile','kilometer','resume'}
    '''
    data = fao.get_workout_data(dirName)
    actv_df = rgNorm.normalize_activity(data)
    df = rgNorm.group_actv(actv_df, splitBy)
    return df.to_dict(orient='records')

def calcTrngType(wrktSegments):
    if len(wrktSegments) in (3, 4):
        return 'Tempo'
    else:
        return 'Workout'
