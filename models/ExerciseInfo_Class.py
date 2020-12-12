# -*- coding: utf-8 -*-
from Weather_Class import WeatherInfo

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
