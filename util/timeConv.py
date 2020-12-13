#!/usr/bin/env python
# coding: utf-8
'''
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
'''

"""
Functions for converting time in seconds
"""

# First party classes
import re
import datetime, time
import math

# 3rd party classes
import numpy as np
import pandas as pd

'''
Constants
'''
SECONDS_IN_HOUR = (60*60)
SECONDS_IN_MINUTE = 60

def break_up_time(actv, time_field):
    '''
    Takes time in seconds from the time_field field of the dataframe actv.
    Breaks it up into hours, minutes, and seconds and adds those fields to the
    dataframe before returning it.
    '''
    actv[time_field + '_hours'] = (np.floor(actv[time_field] / SECONDS_IN_HOUR)
                                   .astype('int64'))
    actv[time_field + '_minutes'] = (np.floor(actv[time_field] % SECONDS_IN_HOUR /
                                              SECONDS_IN_MINUTE).astype('int64'))
    actv[time_field + '_seconds'] = (np.floor(actv[time_field] % SECONDS_IN_HOUR %
                                              SECONDS_IN_MINUTE).astype('int64'))


    return actv


# In[206]:


def seconds_to_time_str(actv, time_field, time_format = ':'):
    '''
    Takes time in seconds from the time_field field of the dataframe actv.
    Converts it into time as a string.
    Time will be in format #h #m #s or #:#:# based on time_format field, default :
    '''

    if time_format == 'hms':
        hour_sep = 'h '
        minute_sep = 'm '
        second_sep = 's'
    else:
        hour_sep = ':'
        minute_sep = ':'
        second_sep = ''

    time_str = (np.floor(actv[time_field] / SECONDS_IN_HOUR).astype('int64')).astype('str') + hour_sep +         (np.floor(actv[time_field] % SECONDS_IN_HOUR / SECONDS_IN_MINUTE).astype('int64')).astype('str') + minute_sep +         (np.floor(actv[time_field] % SECONDS_IN_HOUR % SECONDS_IN_MINUTE).astype('int64')).astype('str') + second_sep


    return time_str

def breakTimeFromSeconds(totTimeSec):
    if totTimeSec is None or math.isnan(totTimeSec):
        totTimeSec = 0
    hourTot = math.floor(totTimeSec/60/60)
    minTot = math.floor((totTimeSec/60/60 - hourTot) * 60)
    secTot = math.floor(((totTimeSec/60/60 - hourTot) * 60 - minTot) *60)
    return hourTot, minTot, secTot
def formatNumbersTime(h, m, s, forceHr=False):
    '''
    Format passed in hours, minutes, seconds into format Nh Nm Ns as a string
    Will not include hour if the value is zero unless forceHr is set to True
    '''
    durTotNumbers = ''
    if h != 0 or forceHr == True:
        durTotNumbers = str(h) + 'h '
    durTotNumbers = durTotNumbers + str(m) + 'm ' + str(s) + 's'
    return durTotNumbers
def formatSheetsTime(h, m, s):
    durTotSheets = str(h) + ':' + str(m) + ':' + str(s)
    return durTotSheets
