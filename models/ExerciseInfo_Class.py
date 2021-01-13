# -*- coding: utf-8 -*-
'''
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
'''
from Weather_Class import WeatherInfo
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

    wrktSegments = None

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

    def cycleDateTime():
        return self.runDate + ' ' + self.runTime

    def elevationChange(self):
        return '{0:.{1}f}'.format(self.elevationGain*METERS_TO_FEET,1) + '↑\n' + '{0:.{1}f}'.format(self.elevationLoss*METERS_TO_FEET,1) + '↓'

    def to_dict(self):
        dateTimeSheetFormat = '%m/%d/%Y %H:%M:%S'
        wrkt = {}
        wrkt['wrkt_dt'] = self.eDate + ' ' + self.startTime.strftime(dateTimeSheetFormat)
        wrkt['wrkt_typ'] = self.type
        wrkt['tot_tm'] = tc.formatNumbersTime(self.hourTot, self.minTot, self.secTot)
        wrkt['tot_tm_sec'] = self.totTmSec
        wrkt['dist'] = round(self.distTot, 2)
        wrkt['dist_mi'] = round(self.distTot, 2)
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
        wrkt['clothes'] = None

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


        return wrkt
