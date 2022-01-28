#!/usr/bin/env python
# coding: utf-8
'''
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
'''

# First party classes
from datetime import datetime, timedelta
from typing import Dict, Union, Optional,Tuple
import math

# 3rd party classes
import pandas as pd
import numpy as np
import fitdecode

# The names of the columns we will use in our points DataFrame. For the data we will be getting
# from the FIT data, we use the same name as the field names to make it easier to parse the data.
POINTS_COLUMN_NAMES = ['latitude', 'longitude', 'lap', 'altitude', 'timestamp', 'heart_rate', 'cadence', 'speed', 'distance']

# The names of the columns we will use in our laps DataFrame.
LAPS_COLUMN_NAMES = ['number', 'start_time', 'total_distance',
    'total_elapsed_time', 'avg_heart_rate', 'total_descent', 'total_ascent']
    # 'max_speed', 'max_heart_rate',

MILES_IN_KILOMETERS = 0.621371
METERS_IN_KILOMETERS = 1000
METERS_TO_FEET = 3.28084
ONE_SECOND = timedelta(0,1) # days, seconds


def get_fit_lap_data(frame: fitdecode.records.FitDataMessage) -> Dict[str, Union[float, datetime, timedelta, int]]:
    """Extract some data from a FIT frame representing a lap and return
    it as a dict.
    """

    data: Dict[str, Union[float, datetime, timedelta, int]] = {}

    for field in LAPS_COLUMN_NAMES[1:]:  # Exclude 'number' (lap number) because we don't get that
                                        # from the data but rather count it ourselves
        if frame.has_field(field):
            data[field] = frame.get_value(field)

    return data

def get_fit_point_data(frame: fitdecode.records.FitDataMessage) -> Optional[Dict[str, Union[float, int, str, datetime]]]:
    """Extract some data from an FIT frame representing a track point
    and return it as a dict.
    """

    data: Dict[str, Union[float, int, str, datetime]] = {}

    if (frame.has_field('position_lat') and frame.has_field('position_long') ) and frame.get_value('position_lat') != None and frame.get_value('position_long') != None:
        data['latitude'] = frame.get_value('position_lat') / ((2**32) / 360)
        data['longitude'] = frame.get_value('position_long') / ((2**32) / 360)
    # else:
        # Frame does not have any latitude or longitude data. We will ignore these frames in order to keep things
        # simple, as we did when parsing the TCX file.
        # return None

    # print(frame.fields)
    for field in POINTS_COLUMN_NAMES[3:]:
        if frame.has_field(field):
            data[field] = frame.get_value(field)

    return data



def get_dataframes(fname: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Takes the path to a FIT file (as a string) and returns two Pandas
    DataFrames: one containing data about the laps, and one containing
    data about the individual points.
    """

    points_data = []
    laps_data = []
    lap_no = 1
    with fitdecode.FitReader(fname) as fit_file:
        for frame in fit_file:
            if isinstance(frame, fitdecode.records.FitDataMessage):
                if frame.name == 'record':
                    # print(type(frame))
                    # print(dir(frame))
                    # print (frame.fields)
                    # # return

                    single_point_data = get_fit_point_data(frame)
                    if single_point_data is not None:
                        single_point_data['lap'] = lap_no
                        points_data.append(single_point_data)
                elif frame.name == 'lap':
                    single_lap_data = get_fit_lap_data(frame)
                    single_lap_data['number'] = lap_no
                    laps_data.append(single_lap_data)
                    lap_no += 1
                # else:
                    # print('other frames: ' + frame.name)

    # Create DataFrames from the data we have collected. If any information is missing from a particular lap or track
    # point, it will show up as a null value or "NaN" in the DataFrame.

    laps_df = pd.DataFrame(laps_data, columns=LAPS_COLUMN_NAMES)
    laps_df['interval'] = laps_df['number'] -1
    # Not sure if total_elapsed_time includes pauses
    laps_df['dur_sec'] = laps_df['total_elapsed_time']
    laps_df['dist_mi'] = (laps_df['total_distance'] / METERS_IN_KILOMETERS * MILES_IN_KILOMETERS).round(2)
    laps_df['ele_up'] = laps_df['total_ascent'] * METERS_TO_FEET
    laps_df['ele_down'] = laps_df['total_descent'] * METERS_TO_FEET
    laps_df.rename(columns={'avg_heart_rate': 'avg_hr'}, inplace=True)
    laps_df.set_index('number', inplace=True)
    points_df = pd.DataFrame(points_data, columns=POINTS_COLUMN_NAMES)

    return laps_df, points_df

def get_pause_sections(df):
    """
    Get the rows where a pause ends based on them having a delta_timestamp > 1 second
    Reindex the pause dataframe to get which pause section each is from
    Merge the pause section back into the passed dataframe and return it.
    """
    point_events_df = df.copy()

    # Create dataframe of sections just have pause
    pause_df = point_events_df.loc[point_events_df['delta_timestamp'] >ONE_SECOND]
    pause_df.reset_index(inplace=True, drop=True)
    pause_df['pause_section'] = pause_df.index.values+2

    pause_conditions = pause_df['timestamp'].tolist()
    pause_choices = [1]
    pause_choices.extend(pause_df['pause_section'].tolist())
    if pause_df.shape[0] <1:
        # There were no pauses during workout
        # Set whole workout to first resume section
        point_events_df['resume'] = 1
        return point_events_df
    point_pause_conditions = [point_events_df['timestamp'].lt(pause_df['timestamp'].iloc[0])]
    for i in range(pause_df.shape[0] -1):
        condition = point_events_df['timestamp'].ge(pause_conditions[i]) & point_events_df['timestamp'].lt(pause_conditions[i+1])
        point_pause_conditions.append(condition)
    point_pause_conditions.append(point_events_df['timestamp'].ge(pause_conditions[-1]))
    point_events_df['resume'] = np.select(point_pause_conditions, pause_choices)
    return point_events_df

def normalize_laps_points(lapsDf, pointsDf):
    # pointsDf = pd.read_pickle('files/points.pickle')
    # lapsDf = pd.read_pickle('files/laps.pickle')
    lapsDf['lap'] = lapsDf.index.values


    # Join lap into points
    laps_conditions = lapsDf['start_time'].tolist()
    laps_choices = lapsDf.index.values.tolist()

    point_lap_conditions = []
    for i in range(len(laps_conditions)-1):
        # print(i)
        condition = pointsDf['timestamp'].ge(laps_conditions[i]) & pointsDf['timestamp'].lt(laps_conditions[i+1])
        point_lap_conditions.append(condition)
    point_lap_conditions.append(pointsDf['timestamp'].ge(laps_conditions[-1]))
    point_events_df = pointsDf.copy()
    point_events_df['lap'] = np.select(point_lap_conditions, laps_choices)


    # point_events_df = pointsDf.merge(lapsDf[['start_time','lap']], how="left", left_on='timestamp', right_on='start_time', suffixes=('','_lap')).drop(columns=['start_time'])
    # point_events_df.at[0,'lap'] = 1
    # point_events_df['lap'].fillna(method='ffill', inplace=True)

    point_events_df['altitude_ft'] = point_events_df['altitude']*METERS_TO_FEET

    # Calculate distance in miles and kilometers from distance in meters
    point_events_df.rename(columns={'distance':'dist_m'}, inplace=True)
    point_events_df['dist_mi'] = (point_events_df['dist_m'] / METERS_IN_KILOMETERS * MILES_IN_KILOMETERS)
    point_events_df['dist_km'] = (point_events_df['dist_m'] / METERS_IN_KILOMETERS)

    # Get change in distance between rows
    point_events_df['delta_dist_mi'] = point_events_df['dist_mi']-point_events_df['dist_mi'].shift(+1)
    point_events_df['delta_dist_km'] = point_events_df['dist_km']-point_events_df['dist_km'].shift(+1)
    point_events_df['delta_ele_ft'] = point_events_df['altitude_ft'] -point_events_df['altitude_ft'].shift(+1)

    point_events_df['delta_timestamp'] = point_events_df['timestamp']-point_events_df['timestamp'].shift(+1)

    point_events_df['delta_dist_mi'].fillna(0, inplace=True)
    point_events_df['delta_dist_km'].fillna(0, inplace=True)

    # Get mile number
    # MAX_MILE_NBR = 500
    i = 1
    conditions = [point_events_df['dist_mi'].lt(i)]
    choices = [i]
    while i <= math.ceil(point_events_df['dist_mi'].max()):
        conditions.append(point_events_df['dist_mi'].ge(i) & point_events_df['dist_mi'].lt(i+1))
        choices.append(i+1)
        i=i+1
    point_events_df['mile'] = np.select(conditions, choices, default=0)

    # Get Kilometer number
    i = 1
    conditions = [point_events_df['dist_km'].lt(i)]
    choices = [i]
    while i <= math.ceil(point_events_df['dist_km'].max()):
        conditions.append(point_events_df['dist_km'].ge(i) & point_events_df['dist_km'].lt(i+1))
        choices.append(i+1)
        i=i+1
    point_events_df['kilometer'] = np.select(conditions, choices, default=0)

    point_events_df = get_pause_sections(point_events_df)

    # View rows where mile == 2
    # point_events_df[point_events_df['mile']==2]

    # Get total seconds, not positive this is the right way
    point_events_df['dur_sec'] = point_events_df.index.values

    point_events_df.rename(columns={'heart_rate':'hr'}, inplace=True)

    return point_events_df

if __name__ == '__main__':

    from sys import argv
    fname = argv[1]  # Path to FIT file to be given as first argument to script
    laps_df, points_df = get_dataframes(fname)
    print('LAPS:')
    print(laps_df)
    print('\nPOINTS:')
    print(points_df)
