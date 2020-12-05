#!/usr/bin/env python
# coding: utf-8
"""
Functions for normalizing the workout from RunGap JSON files
Uses pandas and numpy to process and normalize the data.
"""

# First party classes
import os,glob,shutil
import re
import datetime, time

# 3rd party classes
import numpy as np
import pandas as pd

# custom classes
import util.timeConv as tc

def group_actv(df, group_by_field):
    '''
    Group activity in the passed df Data Frame. Will perform group by
     on the group_by_field.
    Will calculate the below fields
    '''

    df['ele_up'] = df[df['ele_ft_delta']>0]['ele_ft_delta']
    df['ele_down'] = df[df['ele_ft_delta']<0]['ele_ft_delta']

    grouped_df = (df.groupby([group_by_field])
        .agg(max_time=('dur_sec', 'max')
             , min_time=('dur_sec', 'min')
             , avg_hr = ('hr', 'mean')
             , ele_up = ('ele_up','sum')
             , ele_down = ('ele_down','sum')
             , sum_ele = ('ele_ft_delta','sum')
             , max_dist = ('dist_mi','max')
             , min_dist = ('dist_mi','min')
        )
        .reset_index()
    )

    grouped_df['dur_sec'] = grouped_df['max_time'] - grouped_df['min_time']
    grouped_df['dist_mi'] = grouped_df['max_dist'] - grouped_df['min_dist']

    grouped_df['pace'] = grouped_df['dur_sec'] / grouped_df['dist_mi']
    grouped_df['pace'] = grouped_df['pace'].replace(np.inf, 0)

    grouped_df['dur_str'] = tc.seconds_to_time_str(grouped_df, 'dur_sec', 'hms')
    grouped_df['pace_str'] = tc.seconds_to_time_str(grouped_df, 'pace', 'hms')

    grouped_df['dist_mi'] = grouped_df['dist_mi'].round(2)
    grouped_df['avg_hr'] = grouped_df['avg_hr'].round(2)
    grouped_df['ele_up'] = grouped_df['ele_up'].round(2)
    grouped_df['ele_down'] = grouped_df['ele_down'].round(2)
    grouped_df['sum_ele'] = grouped_df['sum_ele'].round(2)

    # grouped_df = tc.break_up_time(grouped_df,'duration')
    # grouped_df = tc.break_up_time(grouped_df, 'pace')

    return grouped_df[[group_by_field,'dur_sec', 'dur_str', 'dist_mi' \
        , 'pace', 'pace_str' \
        , 'avg_hr' \
        , 'ele_up', 'ele_down', 'sum_ele' \
        , 'min_time','max_time','min_dist', 'max_dist' \
        ]]

def normalize_activity(dataRaw):
    '''
    Normalize the activity based on the passed in raw workout data
    Return dataframe of the normalized workout data
    '''
    activityPts = dataRaw['laps'][0]['points']
    eventTyps = dataRaw['events']

    # Initialize Pandas DataFrames
    df_events = pd.DataFrame(eventTyps)
    df_activity = pd.DataFrame(activityPts)

    return(merge_evnts_to_actv(df_activity, df_events))

def clean_events(df_orig):
    """
    Rename and remove columns in passed DataFrame

    """
    events_clean = df_orig.copy()

    # Create columns for start/end in datetime
    events_clean['start_dttm'] = pd.to_datetime(events_clean['start'], unit='s')
    events_clean['end_dttm'] = pd.to_datetime(events_clean['end'], unit='s')

    # Split up the metadata column into new columns and drop the metadata column
    events_clean = pd.concat([events_clean.drop(['metadata'], axis=1), events_clean['metadata'].apply(pd.Series)], axis=1)

    # change column _HKPrivateMetadataSplitMeasuringSystem to dist_uom
    # Rename split measuring system column to dist_uom and rename values in the column
    events_clean.rename(columns={'_HKPrivateMetadataSplitMeasuringSystem': 'dist_uom',
                                 '_HKPrivateWorkoutSegmentIndex':'segment_index',
                                 '_HKPrivateMetadataSplitActiveDurationQuantity':'dur_sec',
                                 '_HKPrivateMetadataSplitDistanceQuantity':'dist_meters'}, inplace=True)
    events_clean.dist_uom.replace(['1','2'],['kilometers','miles'], inplace=True)

    if 'segment_index' in events_clean.columns:
        events_clean['segment_index'].fillna(-1, inplace=True)
        events_clean['segment_index'] = events_clean['segment_index'].astype('int64')
    else:
        events_clean['segment_index'] = 0

    # drop column named 0, not sure where it came from
    events_clean.drop([0], axis=1, inplace=True)

    return events_clean


def mark_segments(activity_df, event_segments, segment_name):
    """
    activity_df - dataframe to add new column named segment_name
     that will contain segments based on event_segments start and end times
    """



def add_intervals_to_activity(actv_df, intvl_lst):
    """
    Takes activity in actv_df and array of events to create new intervals in activity.
    intvl_lst contains an array of dictionaries for intervals to create
        Expected keys in dictionary
        evnt_df = event data frame
        new_field = field name to create based on data from evnt_df
        evnt_field = field name with number to use for setting intervals
    """
    actv_mod = actv_df.copy()
    for intvl_typ in intvl_lst:
        actv_mod = add_interval_to_activity(
            actv_mod, intvl_typ['evnt_df'],
            intvl_typ['new_field'], intvl_typ['evnt_field'],
            actv_mod.loc[actv_mod.index[0], 'time']
        )
    return actv_mod



# Add the mile for each row in activity
def add_interval_to_activity(actv, events, new_actv_field, evnt_field, min_time = 0):
    """
    Add value for evnt_field from events df to actv df with field name of new_actv_field
    If events is empty return add the new_actv_field with a value of 0 and return actv with the new field
    """
    # print('add_interval_to_activity new_actv_field:' + new_actv_field)
    max_time = 9999999999

    if events.size == 0:
        actv[new_actv_field] = 0
        return actv

    # print(events[[evnt_field,'start','end']])
    # Add an extra row at the end to catch any actv records where time is greater than the last end event
#     last_row_end = events.loc[events.index[-1], 'end']
    last_row_end = events['end'].max()
    # print('last_row_end: ' + str(last_row_end))
    if last_row_end < max_time:
        new_row = pd.DataFrame([[last_row_end, max_time, np.nan]],
                               columns=['start','end',evnt_field])
        events_2 = events.append(new_row, ignore_index=True, sort=True)
        # print('new_row')
    else:
        events_2 = events
        # print('no new_row')
    # print(events_2[[evnt_field,'start','end']])

    first_row_start = events.loc[events.index[0], 'start']
    if first_row_start > min_time:
        new_row = pd.DataFrame([[min_time, first_row_start, '0']],
                               columns=['start','end',evnt_field])
#         events_2 = events_2.append(new_row, ignore_index=True, sort=True)
        events_2 = pd.concat([new_row, events_2], ignore_index=True, sort=True)

#     print(events_2.sort_values(['start']).head(20))

    s = pd.IntervalIndex.from_arrays(events_2.start,
                                     events_2.end , closed='left')
    actv[new_actv_field]=events_2.set_index(s).loc[actv.time][evnt_field].values

    if (events_2[evnt_field].dtypes == np.int64 or events_2[evnt_field].dtypes == np.float64):
        # actv[new_actv_field] = actv[new_actv_field].replace(np.nan, actv[new_actv_field].max()+1)
        actv[new_actv_field] = actv[new_actv_field].replace(np.nan, actv[new_actv_field].max())

    return actv


def merge_start_end_for_events(events_clean):
    '''
    Takes each segment and adds the start and end time by comparing to other segments
    Return: Empty DataFrame if there are no records with type == marker in the passed events_clean DF
            New DF with markers broken up by start and end time
    '''
    marker_events = events_clean.loc[events_clean['type'] == 'marker'].copy()

    if marker_events.size == 0:
        return pd.DataFrame()

    # Creates prevSegmentIndex for merging rows
    marker_events['prevSegmentIndex'] = marker_events['segment_index']-1
    marker_events['prevSegmentIndex'] = marker_events['prevSegmentIndex'].astype('int64')

    # Merge marker_events with itself on the segment_index and the prev_segmentIndex to
    #  get the start and end time on one row for each segment
    marker_events = pd.merge(marker_events[['end','prevSegmentIndex', 'end_dttm']],
                             marker_events[['start','segment_index', 'start_dttm']],
                             how='left',
                             left_on='prevSegmentIndex', right_on='segment_index')

    marker_events['start'].fillna(0, inplace=True)
    marker_events['start'] = marker_events['start'].astype('int64')
    marker_events['start_dttm'].fillna(pd.to_datetime(marker_events['start'], unit='s'), inplace=True)

    newRow = pd.DataFrame({"end":[4000000000],
                           "start":[marker_events.loc[marker_events.index[-1],'end']],
                           "start_dttm":[marker_events.loc[marker_events.index[-1],'end_dttm']],
                           "end_dttm": pd.to_datetime(4000000000, unit='s')
                          })
    marker_events = marker_events.append(newRow, ignore_index=True, sort=True)
    marker_events['interval_nbr'] = np.arange(len(marker_events)) # Add segment numbers

    marker_events.drop(['prevSegmentIndex','segment_index'], axis=1, inplace=True)

    return marker_events


# In[10]:


def create_pause_df(events):
    '''
    NOT BEING USED
    1. Get pause and resume events, then reindex the pause/resume
    2. Create seperate df for pause and resume
    3. Merge pause and resume DFs using the index
    '''
    df_pause_resume = events.query('type in ("pause","resume")').copy()
    df_pause_resume.reset_index(inplace=True)

    df_pause = df_pause_resume[df_pause_resume['type'] == 'pause'].copy()
    df_pause['resume_id'] = df_pause.index.values+1
    df_resume = df_pause_resume[df_pause_resume['type'] == 'resume']

    df_pause_start_end = pd.merge(df_pause[['start','resume_id']], df_resume[['end']], how='left', left_on='resume_id', right_index=True)
    df_pause_start_end['duration'] = df_pause_start_end['end'] - df_pause_start_end['start']
    df_pause_start_end['end'] = df_pause_start_end.end.fillna(9999999999).astype('int')
    df_pause_start_end.reset_index(inplace=True, drop=True)
    df_pause_start_end['pause_section'] = df_pause_start_end.index.values+1

    return(df_pause_start_end)



def merge_start_end_rows(events, left_type, right_type):
    '''
    1. Take rows with left_type and merge with rows for right_type.
        left_type will be used for start of each row and right_type
        for end of each row
    '''
    df_pause_resume = events.query(
        'type in (\"' + left_type + '\", \"' + right_type + '\")').copy()
    df_pause_resume.reset_index(inplace=True)

    df_left = df_pause_resume[df_pause_resume['type'] == left_type].copy()
    df_left['switch_id'] = df_left.index.values+1
    df_right = df_pause_resume[df_pause_resume['type'] == right_type]

    df_start_end = pd.merge(df_left[['start','switch_id']], df_right[['end']],
                            how='left', left_on='switch_id', right_index=True)
    df_start_end['duration'] = df_start_end['end'] - df_start_end['start']
    df_start_end['end'] = df_start_end.end.fillna(9999999999).astype('int')
    df_start_end.reset_index(inplace=True, drop=True)
    df_start_end['event_section'] = df_start_end.index.values+1

    return(df_start_end)



def create_pause_resume_events(events):
    '''
    Create separate DataFrames pause and resume events and then concatenates
    the two dataframes together and returns them.
    '''
    pause_events = merge_start_end_rows(events, 'pause', 'resume')
    pause_events['type'] = 'pause'
    resume_events = merge_start_end_rows(events, 'resume', 'pause')
    resume_events['type'] = 'resume'

    pause_resume_events = pd.concat([pause_events, resume_events], ignore_index=True)

    return (pause_resume_events)



def add_splits(actv_orig, evnt_orig):
    '''
    1. Using evnt_orig create dataframe splits for events by mile, kilometer, segment, and pauses
    2. Add to activity the split for each event type
    3. Calculate duration withough pause sections
    '''
    events_clean = clean_events(evnt_orig)

    # Create event dataframe for mile markers
    mile_events = events_clean.loc[events_clean['dist_uom'] == 'miles'].copy()
    mile_events['interval_nbr'] = np.arange(len(mile_events)) # Add mile numbers

    # Create event dataframe for kilometer markers
    km_events = events_clean.loc[events_clean['dist_uom'] == 'kilometers'].copy()
    km_events['interval_nbr'] = np.arange(len(km_events)) # Add kilometer numbers

    # Create event dataframe for segments
    marker_events = merge_start_end_for_events(events_clean)

    # Create events dataframe for pause and resumes
    pause_resume_events = create_pause_resume_events(events_clean)

    '''
    2. Add to activity the split for each event type
    '''
    activity_clean = add_intervals_to_activity(actv_orig, [
        {'evnt_df': mile_events, 'new_field':'mile', 'evnt_field': 'interval_nbr'}
        , {'evnt_df': km_events, 'new_field':'kilometer', 'evnt_field': 'interval_nbr'}
        , {'evnt_df': marker_events, 'new_field':'segment', 'evnt_field': 'interval_nbr'}
        , {'evnt_df': pause_resume_events, 'new_field':'pause_resume', 'evnt_field': 'type'}
        , {'evnt_df': pause_resume_events, 'new_field':'pause_resume_section', 'evnt_field': 'switch_id'}
    ])
    activity_clean.pause_resume.replace(to_replace='0', value='resume', inplace=True)
    activity_clean['date_time'] = pd.to_datetime(activity_clean['time'], unit='s')
    activity_clean['pause_resume_section'] = activity_clean['pause_resume_section'].astype('int64')

    '''
    4. Calculate additional fields
    '''
    activity_clean = calc_values(activity_clean)

    '''
    3. Calculate duration without pause sections
    '''
    activity_resume = activity_clean[activity_clean['pause_resume'] == 'resume'].copy()
    events_pause = pause_resume_events[pause_resume_events['type'] == 'pause'].copy()

    events_pause['duration_tot'] = events_pause.duration.cumsum()
    # Incrent the switch_id for pause events to get the resume_id after each pause.
    events_pause['resume_id'] = events_pause.switch_id+1


    # Merge activity and events so each row has the number of paused seconds from before it. Then decrement that number of seconds from the run time to get the duration without pauses.
    activity_resume = pd.merge(activity_resume, events_pause[['duration_tot','resume_id']], left_on='pause_resume_section',
            right_on='resume_id', how='left', copy=True)
    activity_resume['duration_tot'].fillna(0, inplace=True)

    activity_resume['run_time_sec_resume'] = activity_resume['run_time_sec'] - activity_resume['duration_tot']

    # Remove unneeded columns from merge
    activity_resume.drop(['duration_tot','resume_id'], axis=1, inplace=True)

    activity_resume['run_time_min_resume'] = activity_resume['run_time_sec_resume'] / 60
    activity_resume['avg_pace_resume'] = activity_resume['run_time_min_resume'] / activity_resume['dist_mi']


    return activity_resume


def calc_values(actv_orig):
    '''
    3. Calculate additional values
    '''
    activity_clean = actv_orig.copy()
    METERS_TO_MILES = 0.000621371
    METERS_TO_FEET = 3.28084
    activity_clean['dist_mi'] = activity_clean['dist'] * METERS_TO_MILES
    activity_clean.rename(columns={'dist': 'dist_meters', 'ele':'ele_meters'}, inplace=True)

    # Get time into workout in seconds and minutes instead of times since epoch
    runStartTmSec = activity_clean.iloc[0]['time']
    runStartTm = datetime.datetime.fromtimestamp(runStartTmSec)

    activity_clean['run_time_sec'] = activity_clean['time'] - runStartTmSec
    activity_clean['run_time_min'] = activity_clean['run_time_sec'] / 60

    activity_clean['avg_pace'] = activity_clean['run_time_min'] / activity_clean['dist_mi']

    # Forward Fill Heart Rate
    activity_clean['hr'].fillna(method='ffill', inplace=True)

    # Get elevation change, only first record has na so replace it with zero
    activity_clean['ele_ft'] = activity_clean['ele_meters'] * METERS_TO_FEET
    activity_clean['ele_ft_delta'] = activity_clean['ele_ft'].diff().fillna(0)

    return activity_clean


def rm_unneeded_cols(actv_orig):
    '''
    4. Remove unneeded columns from activity_resume df for exporting whole workout
    '''
    actv_df = actv_orig.copy()

    # Drop unneeded fields
    actv_df.drop(['kcal','dist_meters', 'va','ha','lon','lat',
                  'pause_resume','run_time_sec','run_time_min',
                  'run_time_min_resume', 'avg_pace', 'time'],
                 axis=1, inplace=True)
    # Rename colums
    actv_df.rename(columns={'avg_pace_resume':'avg_pace'                        , 'run_time_sec_resume':'dur_sec'                        , 'pause_resume_section':'resume'                       }, inplace=True)

    # Store time values in hh mm ss format
    actv_df['dur_str'] = tc.seconds_to_time_str(actv_df, 'dur_sec', 'hms')
    # actv_df['avg_pace_str'] = tc.seconds_to_time_str(actv_df, 'avg_pace', 'hms')

    # Change typs of columns
    actv_df['mile'] = actv_df['mile'].astype('int64')
    actv_df['kilometer'] = actv_df['kilometer'].astype('int64')
    actv_df['segment'] = actv_df['segment'].astype('int64')
    actv_df['resume'] = actv_df['resume'].astype('int64')
    actv_df['dur_sec'] = actv_df['dur_sec'].astype('int64')

    # Rearrange columns
    actv_df = actv_df[['date_time', 'dist_mi', 'dur_sec', 'dur_str'
        , 'avg_pace', 'mile','kilometer','segment','resume'
        , 'hr', 'ele_ft', 'ele_ft_delta', 'runcad'
    ]]
    return actv_df


def merge_evnts_to_actv(df_activity, df_events):
    '''
    # Clean
     1. Create dataframes of events based on mile, kilometer, segment, pause/resume
     2. Add colums for mile, kilometer, segment, and pause/resume to activity.
     3. Calculate additional values
     4. Remove unneeded columns
    '''
    activity_clean = add_splits(df_activity, df_events)
    actv_df = rm_unneeded_cols(activity_clean)
    return actv_df
