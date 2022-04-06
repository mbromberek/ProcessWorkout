# 3rd party classes
import numpy as np
import pandas as pd



class Workout_interval:
    # pause | segment | lap | mile | kilometer | custom
    break_type = ''
    interval_order = 0
    interval_desc = None
    dur_sec = 0
    dist_mi = 0
    hear_rate = None
    ele_up = None
    ele_down = None
    notes = None
    lat = None
    lon = None

    def __init__(self):
        self.dur_sec = 0

    def __repr__(self):
        return '<Interval order {} for {}>'.format( self.interval_order, self.break_type)

    def __lt__(self, other):
        if self.break_type != other.break_type:
            return self.break_type < other.break_type
        return self.interval_order < other.interval_order

    def from_df_dict(self, data, break_type):
        self.break_type = break_type
        self.interval_order = data['interval']
        self.dur_sec = int(data['dur_sec'])
        self.dist_mi = float(data['dist_mi'])
        self.hear_rate = int(0 if np.isnan(data['avg_hr']) else data['avg_hr'])
        # self.hear_rate = int(0 if data['avg_hr'] == np.nan else data['avg_hr'])
        self.ele_up = float(data['ele_up'])
        self.ele_down = float(data['ele_down'])
        if 'lat' in data:
            self.lat = data['lat']
        if 'lon' in data:
            self.lon = data['lon']
        if 'interval_desc' in data:
            self.interval_desc = data['interval_desc']

    def to_dict(self):
        data = {
            'break_type': self.break_type,
            'interval_order': self.interval_order,
            'dur_sec': self.dur_sec,
            'dist_mi': str(self.dist_mi),
        }
        if self.interval_desc != None:
            data['interval_desc'] = self.interval_desc
        if self.hear_rate != None:
            data['hr'] = str(self.hear_rate)
        if self.ele_up != None:
            data['ele_up'] = str(self.ele_up)
        if self.ele_down != None:
            data['ele_down'] = str(self.ele_down)
        if self.notes != None:
            data['notes'] = self.notes
        if self.lat != None and not (np.isnan(self.lat)):
            data['lat'] = self.lat
        if self.lon != None and not (np.isnan(self.lon)):
            data['lon'] = self.lon

        return data
