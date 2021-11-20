from datetime import datetime, timedelta
from typing import Dict, Union, Optional,Tuple

import pandas as pd

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

    if not (frame.has_field('position_lat') and frame.has_field('position_long')):
        # Frame does not have any latitude or longitude data. We will ignore these frames in order to keep things
        # simple, as we did when parsing the TCX file.
        return None
    else:
        data['latitude'] = frame.get_value('position_lat') / ((2**32) / 360)
        data['longitude'] = frame.get_value('position_long') / ((2**32) / 360)

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
    laps_df.rename(columns={'avg_heart_rate': 'avg_hr','total_ascent':'ele_up', 'total_descent':'ele_down'}, inplace=True)
    laps_df.set_index('number', inplace=True)
    points_df = pd.DataFrame(points_data, columns=POINTS_COLUMN_NAMES)

    return laps_df, points_df

if __name__ == '__main__':

    from sys import argv
    fname = argv[1]  # Path to FIT file to be given as first argument to script
    laps_df, points_df = get_dataframes(fname)
    print('LAPS:')
    print(laps_df)
    print('\nPOINTS:')
    print(points_df)