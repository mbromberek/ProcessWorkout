from datetime import datetime, timedelta
from typing import Dict, Union, Optional,Tuple

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

    # Calculate distance in miles from distance in meters
    point_events_df['dist_mi'] = (point_events_df['distance'] / METERS_IN_KILOMETERS * MILES_IN_KILOMETERS)

    # Get mile number
    conditions = [
        point_events_df['dist_mi'].lt(1),
        point_events_df['dist_mi'].ge(1) & point_events_df['dist_mi'].lt(2),
        point_events_df['dist_mi'].ge(2) & point_events_df['dist_mi'].lt(3),
        point_events_df['dist_mi'].ge(3) & point_events_df['dist_mi'].lt(4),
        point_events_df['dist_mi'].ge(4) & point_events_df['dist_mi'].lt(5),
        point_events_df['dist_mi'].ge(5) & point_events_df['dist_mi'].lt(6),
        point_events_df['dist_mi'].ge(6) & point_events_df['dist_mi'].lt(7),
        point_events_df['dist_mi'].ge(7) & point_events_df['dist_mi'].lt(8),
        point_events_df['dist_mi'].ge(8) & point_events_df['dist_mi'].lt(9),
        point_events_df['dist_mi'].ge(9) & point_events_df['dist_mi'].lt(10),
        point_events_df['dist_mi'].ge(10) & point_events_df['dist_mi'].lt(11),
        point_events_df['dist_mi'].ge(11) & point_events_df['dist_mi'].lt(12),
        point_events_df['dist_mi'].ge(12) & point_events_df['dist_mi'].lt(13)
    ]
    choices=[1,2,3,4,5,6,7,8,9,10,11,12,13]
    point_events_df['mile'] = np.select(conditions, choices, default=0)

    # View rows where mile == 2
    # point_events_df[point_events_df['mile']==2]

    # Get change in distance between rows
    point_events_df['delta_dist_mi'] = point_events_df['dist_mi']-point_events_df['dist_mi'].shift(+1)
    point_events_df['altitude_ft'] = point_events_df['altitude']*METERS_TO_FEET
    point_events_df['delta_ele_ft'] = point_events_df['altitude_ft'] -point_events_df['altitude_ft'].shift(+1)


    point_events_df['delta_dist_mi'].fillna(0, inplace=True)

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
