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
        wrkt['dist'] = "%.2f" % self.distTot,
        wrkt['hr'] = self.avgHeartRate
        wrkt['cal_burn'] = self.calTot
        wrkt['notes'] = self.userNotes
        wrkt['gear'] = self.gear
        wrkt['category'] = self.category
        wrkt['elevation'] = self.elevationChange()
        return wrkt
