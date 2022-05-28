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
import datetime, time, pytz
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

    hourTot = math.floor(totTimeSec / SECONDS_IN_HOUR)
    minTot = math.floor((totTimeSec % SECONDS_IN_HOUR) / SECONDS_IN_MINUTE)
    secTot = round((totTimeSec % SECONDS_IN_HOUR) % SECONDS_IN_MINUTE)


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

def time_str_to_sec(tm_str):
    '''
    Convert passed in time string from format ##h ##m ##s to seconds
    '''

    hours_sec = int(re.search('(\d*)h', tm_str).group(1))*SECONDS_IN_HOUR if re.search('(\d*)h', tm_str) else 0
    minutes_sec = int(re.search('(\d*)m', tm_str).group(1))*SECONDS_IN_MINUTE if re.search('(\d*)m', tm_str) else 0
    seconds = int(re.search('(\d*)s', tm_str).group(1)) if re.search('(\d*)s', tm_str) else 0

    tm_sec = hours_sec + minutes_sec + seconds

    return tm_sec

def adjustAppleNumbersTimeForDst(dttm):
    '''
    This is needed since Numbers AppleScript is returning entries that were in DST with an hour later if pulled during ST. So adjusting the time to handle it.

    If passed in datetime is in DST and current date is not in DST then
        decrement passed datetime by one hour
    If passed in datetime is not in DST and current date is in DST then
        increment passed datetime by one hour
    Else
        return unmodified dttm
    '''
    # Set timezone to US/Central
    tz_str = 'US/Central'

    # Get current date and time and set timezone
    curr_dttm = datetime.datetime.now()
    curr_dttm_tz = pytz.timezone(tz_str).localize(curr_dttm)

    # Set timezone for passed in datetime
    dttmtz = pytz.timezone(tz_str).localize(dttm)

    if bool(dttmtz.dst()) and not bool(curr_dttm_tz.dst()):
        dttm_mod = dttm - datetime.timedelta(hours=1)
        return dttm_mod
    elif not bool(dttmtz.dst()) and bool(curr_dttm_tz.dst()):
        dttm_mod = dttm + datetime.timedelta(hours=1)
        return dttm_mod
    else:
        return dttm
