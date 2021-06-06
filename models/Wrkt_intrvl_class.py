

class Workout_interval:
    # pause | segment | mile | kilometer | custom
    break_type = ''
    interval_order = 0
    interval_desc = None
    dur_sec = 0
    dist_mi = 0
    hr = None
    ele_up = None
    ele_down = None
    notes = None

    def __init__(self):
        self.dur_sec = 0

    def __repr__(self):
        return '<Interval order {} for {}>'.format( self.interval_order, self.break_type)

    def __lt__(self, other):
        if self.break_type != other.break_type:
            return self.break_type < other.break_type
        return self.interval_order < other.interval_order

    def from_df_dict(self, data, break_type):
        print(data)

        self.break_type = break_type
        self.interval_order = data['interval']
        self.dur_sec = int(data['dur_sec'])
        self.dist_mi = float(data['dist_mi'])
        self.hr = int(data['avg_hr'])
        self.ele_up = float(data['ele_up'])
        self.ele_down = float(data['ele_down'])

    def to_dict(self):
        data = {
            'break_type': self.break_type,
            'interval_order': self.interval_order,
            'dur_sec': self.dur_sec,
            'dist_mi': str(self.dist_mi),
        }
        if self.interval_desc != None:
            data['interval_desc'] = self.interval_desc
        if self.hr != None:
            data['hr'] = str(self.hr)
        if self.ele_up != None:
            data['ele_up'] = str(self.ele_up)
        if self.ele_down != None:
            data['ele_down'] = str(self.ele_down)
        if self.notes != None:
            data['notes'] = self.notes

        return data
