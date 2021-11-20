# -*- coding: utf-8 -*-
'''
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
'''
# First party classes
from datetime import datetime

# Custom Classes
from Weather_Class import WeatherInfo
from Wrkt_intrvl_class import Workout_interval
import util.timeConv as tc

METERS_TO_FEET = 3.28084

class ExerciseInfo:
    eDate = ''
    type = ''
    startTime = ''
    endTime = ''
    distTot = ''
    distUnit = ''

    durTot = ''
    hourTot = ''
    minTot = ''
    secTot = ''
    totTmSec = 0

    rating = ''

    calTot = ''
    avgHeartRate = ''
    userNotes = ''

    temperature = ''

    gear = ''
    category = ''
    training_type = ''

    source = ''

    # Filename the data came from or link to data
    originLoc = ''

    elevationGain = ''
    elevationLoss = ''

    startLat = ''
    startLon = ''
    endLat = ''
    endLon = ''

    startWeather = WeatherInfo()
    endWeather = WeatherInfo()

    clothes = ''

    wrktSegments = None
    mileSplits = []
    intrvlSplits = []
    pauseSplits = []
    lapSplits = []

    warmUpTotDistMi = 0
    warmUpTotDurSec = 0
    warmUpTotPaceSec = 0
    coolDnTotDistMi = 0
    coolDnTotDurSec = 0
    coolDnTotPaceSec = 0

    intvlTotDistMi = 0
    intvlTotDurSec = 0
    intvlTotPaceSec = 0
    intvlTotEleUp = 0
    intvlTotEleDown = 0
    intvlAvgDistMi = 0
    intvlAvgDurSec = 0
    intvlAvgPaceSec = 0
    intvlAvgEleUp = 0
    intvlAvgEleDown = 0


    def __init__(self):
        self.epName = ''

#     def __str__(self):
#         print (epName)

    def __repr__(self):
        return '<Exercise {}: {}>'.format(self.type, self.startTime)

    def cycleDateTime():
        return self.runDate + ' ' + self.runTime

    def elevationChange(self):
        return '{0:.{1}f}'.format(self.elevationGain*METERS_TO_FEET,1) + '↑\n' + '{0:.{1}f}'.format(self.elevationLoss*METERS_TO_FEET,1) + '↓'

    @staticmethod
    def breakupElevation(ele):
        d = {}
        if ele == None:
            return None
        else:
            d['ele_up'] = float(ele.split('↑')[0])
            d['ele_down'] = float(ele.split('↑')[1].split('↓')[0])
        return d

    def to_dict(self):
        dateTimeSheetFormat = '%m/%d/%Y %H:%M:%S'
        wrkt = {}
        wrkt['wrkt_dt'] = self.eDate + ' ' + self.startTime.strftime(dateTimeSheetFormat)
        wrkt['wrkt_typ'] = self.type
        wrkt['tot_tm'] = tc.formatNumbersTime(self.hourTot, self.minTot, self.secTot)
        wrkt['tot_tm_sec'] = self.totTmSec
        wrkt['dist'] = round(self.distTot, 2)
        wrkt['dist_mi'] = round(self.distTot, 2)
        if wrkt['dist'] == 0:
            wrkt['pace'] = tc.formatNumbersTime(0,0,0)
            wrkt['pace_sec'] = 0
        else:
            wrkt['pace'] = tc.formatNumbersTime(*tc.breakTimeFromSeconds(self.totTmSec / wrkt['dist']))
            wrkt['pace_sec'] = wrkt['tot_tm_sec'] / wrkt['dist_mi']

        if self.startWeather.temp != -999:
            wrkt['wethr_start'] = {}
            wrkt['wethr_start']['temp'] = self.startWeather.temp
            wrkt['wethr_start']['temp_feels_like'] = self.startWeather.apparentTemp
            wrkt['wethr_start']['hmdty'] = self.startWeather.humidity
            wrkt['wethr_start']['lat'] = self.startWeather.lat
            wrkt['wethr_start']['lon'] = self.startWeather.lon
            wrkt['wethr_start']['wind_speed'] = self.startWeather.windSpeed
            wrkt['wethr_start']['wind_gust'] = self.startWeather.windGust
            wrkt['wethr_start']['cond'] = self.startWeather.summary
            wrkt['wethr_start']['tm'] = self.startWeather.time.strftime(dateTimeSheetFormat)
            if self.startWeather.dewPoint != '':
                wrkt['wethr_start']['dew_point'] = self.startWeather.dewPoint

            wrkt['wethr_end'] = {}
            wrkt['wethr_end']['temp'] = self.endWeather.temp
            wrkt['wethr_end']['temp_feels_like'] = self.endWeather.apparentTemp
            wrkt['wethr_end']['hmdty'] = self.endWeather.humidity
            wrkt['wethr_end']['lat'] = self.endWeather.lat
            wrkt['wethr_end']['lon'] = self.endWeather.lon
            wrkt['wethr_end']['wind_speed'] = self.endWeather.windSpeed
            wrkt['wethr_end']['wind_gust'] = self.endWeather.windGust
            wrkt['wethr_end']['cond'] = self.endWeather.summary
            wrkt['wethr_end']['tm'] = self.endWeather.time.strftime(dateTimeSheetFormat)
            if self.endWeather.dewPoint != '':
                wrkt['wethr_end']['dew_point'] = self.endWeather.dewPoint


        wrkt['hr'] = self.avgHeartRate
        wrkt['cal_burn'] = self.calTot
        wrkt['notes'] = self.userNotes
        wrkt['gear'] = self.gear
        wrkt['category'] = self.category
        wrkt['elevation'] = self.elevationChange()
        wrkt['ele_up'] = '{0:.{1}f}'.format(self.elevationGain*METERS_TO_FEET,1)
        wrkt['ele_down'] = '{0:.{1}f}'.format(self.elevationLoss*METERS_TO_FEET,1)
        # wrkt['wrkt_segments'] = self.wrktSegments
        wrkt['originLoc'] = self.originLoc
        wrkt['category'] = self.category
        wrkt['clothes'] = self.clothes

        if self.intvlTotDistMi != 0:
            wrkt['warm_up'] = {}
            wrkt['warm_up']['tot_dist_mi'] = self.warmUpTotDistMi
            wrkt['warm_up']['tot_tot_tm_sec'] = self.warmUpTotDurSec
            wrkt['warm_up']['tot_pace_sec'] = self.warmUpTotPaceSec
            wrkt['cool_down'] = {}
            wrkt['cool_down']['tot_dist_mi'] = self.coolDnTotDistMi
            wrkt['cool_down']['tot_tot_tm_sec'] = self.coolDnTotDurSec
            wrkt['cool_down']['tot_pace_sec'] = self.coolDnTotPaceSec
            wrkt['intrvl'] = {}
            wrkt['intrvl']['tot_dist_mi'] = self.intvlTotDistMi
            wrkt['intrvl']['tot_tot_tm_sec'] = self.intvlTotDurSec
            wrkt['intrvl']['tot_pace_sec'] = self.intvlTotPaceSec
            wrkt['intrvl']['tot_ele_up'] = self.intvlTotEleUp
            wrkt['intrvl']['tot_ele_down'] = self.intvlTotEleDown
            wrkt['intrvl']['avg_dist_mi'] = self.intvlAvgDistMi
            wrkt['intrvl']['avg_tot_tm_sec'] = self.intvlAvgDurSec
            wrkt['intrvl']['avg_pace_sec'] = self.intvlAvgPaceSec
            wrkt['intrvl']['avg_ele_up'] = self.intvlAvgEleUp
            wrkt['intrvl']['avg_ele_down'] = self.intvlAvgEleDown

    def to_psite_dict(self):
        dateTimeSheetFormat = '%Y-%m-%dT%H:%M:%SZ'
        wrkt = {}
        wrkt['wrkt_dttm'] = self.startTime.strftime(dateTimeSheetFormat)
        if self.type != '':
            wrkt['type'] = self.type
        if self.totTmSec >0:
            wrkt['dur_sec'] = str(round(self.totTmSec))
        if self.distTot >0:
            wrkt['dist_mi'] = str(round(self.distTot, 2))

        if self.startWeather.temp != -999:
            wrkt['wethr_start'] = {}
            wrkt['wethr_start']['temp'] = self.startWeather.temp
            if self.startWeather.apparentTemp != -999:
                wrkt['wethr_start']['temp_feels_like'] = self.startWeather.apparentTemp
            if self.startWeather.humidity != -999:
                wrkt['wethr_start']['hmdty'] = self.startWeather.humidity
            wrkt['wethr_start']['lat'] = self.startWeather.lat
            wrkt['wethr_start']['lon'] = self.startWeather.lon
            if self.startWeather.windSpeed != '':
                wrkt['wethr_start']['wind_speed'] = self.startWeather.windSpeed
            if self.startWeather.windGust != '':
                wrkt['wethr_start']['wind_gust'] = self.startWeather.windGust
            if self.startWeather.summary != '':
                wrkt['wethr_start']['wethr_cond'] = self.startWeather.summary
            if self.startWeather.time != '':
                wrkt['wethr_start']['tm'] = self.startWeather.time.strftime(dateTimeSheetFormat)
            if self.startWeather.dewPoint != '':
                wrkt['wethr_start']['dew_point'] = self.startWeather.dewPoint

            wrkt['wethr_end'] = {}
            wrkt['wethr_end']['temp'] = self.endWeather.temp
            if self.endWeather.apparentTemp != -999:
                wrkt['wethr_end']['temp_feels_like'] = self.endWeather.apparentTemp
            if self.endWeather.humidity != -999:
                wrkt['wethr_end']['hmdty'] = self.endWeather.humidity
            wrkt['wethr_end']['lat'] = self.endWeather.lat
            wrkt['wethr_end']['lon'] = self.endWeather.lon
            if self.endWeather.windSpeed != '':
                wrkt['wethr_end']['wind_speed'] = self.endWeather.windSpeed
            if self.endWeather.windGust != '':
                wrkt['wethr_end']['wind_gust'] = self.endWeather.windGust
            if self.endWeather.summary != '':
                wrkt['wethr_end']['wethr_cond'] = self.endWeather.summary
            if self.endWeather.time != '':
                wrkt['wethr_end']['tm'] = self.endWeather.time.strftime(dateTimeSheetFormat)
            if self.endWeather.dewPoint != '':
                wrkt['wethr_end']['dew_point'] = self.endWeather.dewPoint

        if self.avgHeartRate != '':
            wrkt['hr'] = self.avgHeartRate
        if self.calTot != '':
            wrkt['cal_burn'] = self.calTot
        if self.userNotes != '':
            wrkt['notes'] = self.userNotes
        if self.gear != '':
            wrkt['gear'] = self.gear
        if self.category != '':
            wrkt['category'] = self.category
        if self.elevationGain != '':
            wrkt['ele_up'] = '{0:.{1}f}'.format(self.elevationGain,1)
        if self.elevationLoss != '':
            wrkt['ele_down'] = '{0:.{1}f}'.format(self.elevationLoss,1)
        if self.originLoc != '':
            wrkt['originLoc'] = self.originLoc
        if self.category != '':
            wrkt['category'] = self.category
        if self.clothes != '':
            wrkt['clothes'] = self.clothes
        if self.training_type != '':
            wrkt['training_type'] = self.training_type

        if self.warmUpTotDistMi >0:
            wrkt['warm_up_tot_dist_mi'] = str(round(self.warmUpTotDistMi, 2))
        if self.warmUpTotDurSec >0:
            wrkt['warm_up_tot_tm_sec'] = str(round(self.warmUpTotDurSec))
        if self.coolDnTotDistMi >0:
            wrkt['cool_down_tot_dist_mi'] = str(round(self.coolDnTotDistMi, 2))
        if self.coolDnTotDurSec >0:
            wrkt['cool_down_tot_tm_sec'] = str(round(self.coolDnTotDurSec))
        if self.intvlTotDistMi >0:
            wrkt['intrvl_tot_dist_mi'] = str(round(self.intvlTotDistMi, 2))
        if self.intvlTotDurSec >0:
            wrkt['intrvl_tot_tm_sec'] = str(round(self.intvlTotDurSec))
        if self.intvlTotEleUp >0:
            wrkt['intrvl_tot_ele_up'] =            '{0:.{1}f}'.format(self.intvlTotEleUp*METERS_TO_FEET,1)
        if self.intvlTotEleDown >0:
            wrkt['intrvl_tot_ele_down'] = '{0:.{1}f}'.format(self.intvlTotEleDown*METERS_TO_FEET,1)

        if len(self.mileSplits) >0:
            wrkt['mile_splits'] = []
            for splt in self.mileSplits:
                wrkt['mile_splits'].append(splt.to_dict())

        if len(self.intrvlSplits) >0:
            wrkt['interval_splits'] = []
            for splt in self.intrvlSplits:
                wrkt['interval_splits'].append(splt.to_dict())

        if len(self.lapSplits) >0:
            wrkt['lap_splits'] = []
            for splt in self.lapSplits:
                wrkt['lap_splits'].append(splt.to_dict())

        if len(self.pauseSplits) >0:
            wrkt['pause_splits'] = []
            for splt in self.pauseSplits:
                wrkt['pause_splits'].append(splt.to_dict())


        return wrkt

    def from_dict(self, data):
        dateTimeSheetFormat = '%m/%d/%Y %H:%M:%S'
        self.startTime = datetime.strptime(data['wrkt_dt'], dateTimeSheetFormat)
        if 'wrkt_typ' in data:
            self.type = data['wrkt_typ']
        if 'tot_tm' in data:
            self.durTot = data['tot_tm']
            self.totTmSec = tc.time_str_to_sec(self.durTot)
        if 'dist' in data:
            self.distTot = data['dist']
        if 'hr' in data:
            self.avgHeartRate = data['hr']
        if 'cal_burn' in data:
            self.calTot = data['cal_burn']
        if 'notes' in data:
            self.userNotes = data['notes']
        if 'gear' in data:
            self.gear = data['gear']
        if 'category' in data:
            self.category = data['category']
        if 'elevation' in data:
            d = self.breakupElevation(data['elevation'])
            self.elevationGain = d['ele_up']
            self.elevationLoss = d['ele_down']
        else:
            if 'ele_up' in data:
                self.elevationGain = data['ele_up']
            if 'ele_down' in data:
                self.elevationGain = data['ele_down']

    @staticmethod
    def wrkt_intrvl_from_dict(data, break_type):
        splt_lst = []
        for segment in data:
            splt = Workout_interval()
            print(splt)
            splt.from_df_dict(segment, break_type)
            splt_lst.append(splt)
        return splt_lst
