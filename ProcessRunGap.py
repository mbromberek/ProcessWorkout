#! /Users/mikeyb/Applications/python3
# -*- coding: utf-8 -*-

# First party classes
import os,glob,shutil
import sys
import re
import datetime
import math
import configparser
import requests # For API call

import zipfile
import json

# 3rd party classes
import applescript
import pandas

# Custom Classes
sys.path.insert(1, 'models') # Add to sys.path the directory with custom classes
# Import customer classes that are in models directory
from ExerciseInfo_Class import ExerciseInfo
from Weather_Class import WeatherInfo
import util.timeConv as tc
import models.WrktSplits as wrktSplits

config = configparser.ConfigParser()

#######################################################
# get full directory path for files in passed directory
#######################################################
def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]


#######################################################
# determineGear(exercise details)
#######################################################
def determineGear(ex):
    gearConfigs = config['gear']
    gear = ''
    try:
        if ex.type == 'Running':
            primaryDays = config['running']['primary_days'].split(',')
            if ex.startTime.strftime('%A') in primaryDays:
                gear = gearConfigs['default_shoe_primary']
            else:
                gear = gearConfigs['default_shoe_secondary']
        else:
            gear = gearConfigs['default_' + ex.type]
    except:
        gear = ''

    return gear

#######################################################
# API call
#######################################################
def apiCall(url):
    r = requests.get(url)
    data = r.json()
    return data


#######################################################
# Get Weather from dark sky for the passed latitude,
# longitude, and time.
# Creates a weather object with returned data and returns
# it.
#######################################################
def getWeather(lat, lon, tm):
    darkSkyBaseURL = config['dark_sky']['base_url']
    darkSkyKey = config['dark_sky']['key']

    darkSkyUrl = darkSkyBaseURL + darkSkyKey + '/' + str(lat) + ',' + str(lon) + ',' + tm.strftime('%Y-%m-%dT%H:%M:%S')

    w = WeatherInfo()
    weatherData = apiCall(darkSkyUrl)
    w.temp = weatherData['currently']['temperature']
    w.apparentTemp = weatherData['currently']['apparentTemperature']
    w.humidity = weatherData['currently']['humidity']
    w.windSpeed = weatherData['currently']['windSpeed']
    w.summary = weatherData['currently']['summary']
    w.windGust = weatherData['currently']['windGust']

    if (config['dark_sky']['save_weather'] == 'Y'):
        with open('/tmp/weatherData' + tm.strftime('%Y%m%dT%H%M%S') + '.txt', 'w') as outfile:
            json.dump(weatherData, outfile)

    return w

def generateUserNotes(w):
    """
    Generates notes for User Notes field of Exercise spreadsheet.
    Puts all the text into an array that is joined into the returned string.
    """
    txtLst = []
    txtLst.append(w.position)
    txtLst.append(': {0:.{1}f}'.format(w.temp,0))
    txtLst.append(' degrees ')
    txtLst.append(w.summary)
    txtLst.append(', ')
    txtLst.append('{0:.{1}f}'.format(w.humidity*100,0))
    txtLst.append(' percent humidity, wind speed ')
    txtLst.append('{0:.{1}f}'.format(w.windSpeed,2))
    txtLst.append(' mph, wind gust ')
    txtLst.append('{0:.{1}f}'.format(w.windGust,2))
    txtLst.append('mph, feels like ')
    txtLst.append('{0:.{1}f}'.format(w.apparentTemp,0))
    txtLst.append(' degrees. ')
    txtLst.append('\n')
    return ''.join(txtLst)


#######################################################
# MAIN
#######################################################
def main():
    print('Start Python')

    # Get config details
    progDir = os.path.dirname(os.path.abspath(__file__))
    config.read(progDir + "/config.txt")

    pathToAppleScript = config['applescript']['script_path']
    appleScriptName = config['applescript']['script_name']
    sheetName = config['applescript']['sheet_name']

    runGapConfigs = config['rungap']
    monitorDir = runGapConfigs['monitor_dir']
    print('monitorDir:' + monitorDir)
    tempDir = runGapConfigs['temp_dir']
    print('tempDir: ' + tempDir)
#     dateTimeSheetFormat = runGapConfigs['date_time_sheet_format']
    dateTimeSheetFormat = '%m/%d/%Y %H:%M:%S'

    compressFileRegex = re.compile(r'(.zip|.gz)$')
    jsonFileRegex = re.compile(r'(metadata.json)$')
    jsonExtRegex = re.compile(r'(.json)$')

    # ) Read applescript file for reading and updating exercise spreadseeht
    scptFile = open(pathToAppleScript + appleScriptName)
    scptTxt = scptFile.read()
    scpt = applescript.AppleScript(scptTxt)
    scpt.call('initialize',sheetName)

    print(os.listdir(monitorDir))
    zipFiles = []
    # Uncompress files from monitor directory into temp directory
    for filename in os.listdir(monitorDir):
        # Checks if compressed file
        if compressFileRegex.search(filename):
            z = zipfile.ZipFile(monitorDir + filename,mode='r')
            z.extractall(path=tempDir)
            zipFiles.append(monitorDir + filename)

    exLst = []
    # Loop through files and load exercise data to a list
    print(listdir_fullpath(tempDir))
    filesToProcess = []
    print(filesToProcess)
    for filename in listdir_fullpath(tempDir):
        if (os.path.isfile(filename) == False and filename != '__MACOSX'):
            print('directory')
            filesToProcess.extend(listdir_fullpath(filename))
        else:
            print('file')
            filesToProcess.append(filename)

    print(filesToProcess)
    for filename in filesToProcess:
        print(filename)
        if jsonFileRegex.search(filename):
            print('\nProcess ' + filename)
            ex = ExerciseInfo()
            ex.type = 'Running'
            with open(filename) as data_file:
                data = json.load(data_file)
                ex.source = data['source']
                ex.originLoc = filename

                ex.type = data['activityType']['sourceName']

                # Get the start time from file in UTC
                d = datetime.datetime.strptime(data['startTime']['time'],'%Y-%m-%dT%H:%M:%SZ')
                # Convert start time to current time zone
                sTime = d.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
                ex.startTime = sTime

                MILES_IN_KILOMETERS = 0.621371
                METERS_IN_KILOMETERS = 1000

                eDistanceTotMeters = data['distance']
                ex.distTot = eDistanceTotMeters / METERS_IN_KILOMETERS * MILES_IN_KILOMETERS

                ex.hourTot, ex.minTot, ex.secTot = tc.breakTimeFromSeconds(data['duration'])
                durTotNumbers = tc.formatNumbersTime(ex.hourTot, ex.minTot, ex.secTot)
                durTotSheets = tc.formatSheetsTime(ex.hourTot, ex.minTot, ex.secTot)

                ex.durTot = durTotSheets

                ex.avgHeartRate = data['avgHeartrate']

                ex.calTot = data['calories']

                if 'elevationGain' in data:
                    ex.elevationGain = data['elevationGain']
                    ex.elevationLoss = data['elevationLoss']

                if ex.gear == '':
                    ex.gear = determineGear(ex)

                categoryConfigs = ''
                if ex.type == 'Running':
                    categoryConfigs = config['run_category']
                    # Get day of the exercise
                    if ex.startTime.strftime('%A') in categoryConfigs:
                        ex.category = categoryConfigs[ex.startTime.strftime('%A')]
                else:
                    ex.category = 'Easy'

                # Pull data for getting weather
                laps = data['laps']
                if 'displayPath' in data:
                    exPath = data['displayPath']

                    lastLapStart = datetime.datetime.strptime(laps[-1]['startTime'] ,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
                    lastLapDuration = laps[-1]['duration']
                    lastLapEnd = lastLapStart + datetime.timedelta(seconds=lastLapDuration)
                    ex.endTime = lastLapEnd

                    # Get lat and long from path details
                    ex.startLat = exPath[0]['lat']
                    ex.startLon = exPath[0]['lon']
                    ex.endLat = exPath[-1]['lat']
                    ex.endLon = exPath[-1]['lon']

                    ex.startWeather = getWeather(ex.startLat, ex.startLon, ex.startTime)
                    ex.startWeather.position = 'Start'
                    ex.endWeather = getWeather(ex.endLat, ex.endLon, ex.endTime)
                    ex.endWeather.position = 'End'

                    ex.userNotes = generateUserNotes(ex.startWeather)
                    ex.userNotes = ex.userNotes + generateUserNotes(ex.endWeather)

                if (runGapConfigs['print_data'] == 'Y'):
                    print("Start Date Time: " +
                        ex.startTime.strftime('%Y-%m-%dT%H:%M:%S'))
                    print("Start Unix Time: " + str(ex.startTime.timestamp()))
                    if ex.endTime == '':
                        print("End Date Time: Unknown")
                    else:
                        print('End Date Time: ' +
                            ex.endTime.strftime('%Y-%m-%dT%H:%M:%S'))

                    print("Distance: " + str(ex.distTot))
                    print("Duration: " + ex.durTot)
                    print('Avg Heartrate: ' + str(ex.avgHeartRate))
                    print('Calories Burned: ' + str(ex.calTot))
                    print('Category: ' + ex.category)

                    print('Start Lat, Lon: ' + str(ex.startLat) + ',' + str(ex.startLon) )
                    print('End Lat, Lon: ' + str(ex.endLat) + ',' + str(ex.endLon) )
                    print('\n')
#                     print(darkSkyUrlStart)
#                     print(darkSkyUrlEnd)

                exLst.append(ex)

    # Save Exercise to spreadsheet then remove files
    for ex in exLst:
        startDateTime = ex.startTime.strftime(dateTimeSheetFormat)
        distance = "%.2f" % ex.distTot
        duration = tc.formatNumbersTime(ex.hourTot, ex.minTot, ex.secTot)

        try:
            scpt.call('addExercise',ex.eDate, ex.type, duration, distance, ex.distUnit, ex.avgHeartRate, ex.calTot, ex.userNotes, startDateTime, ex.gear, ex.category, ex.elevationChange())
        except:
            print('addExercise Unexpected Error')
            print(sys.exc_info())
            raise

        if ex.category == 'Training':
            wrktSegments_df = wrktSplits.breakDownWrkt(tempDir, 'segment')
            newTblNm = wrktSplits.calcTrngType(wrktSegments_df) \
                + datetime.date.today().strftime(' %Y-%m-%d')
            trngBrkdnSheetNm = config['workout_breakdown']['sheet_name']
            scpt.call('generateWrktTable' \
                , trngBrkdnSheetNm, newTblNm \
                , wrktSegments_df.to_dict(orient='records') \
            )

        # if ex.category == 'Long Run':
            # wrktSegments = wrktSplits.breakDownWrkt(tempDir, 'mile')
            # print('****Workout Miles****')
            # for seg in wrktSegments:
            #     print(seg)

        # Remove files from temp folder then monitor folder
        fileNameChunks = ex.originLoc.split('.')
        filePathStart = fileNameChunks[0]
        print ('filePathStart:' + filePathStart)
        for fl in glob.glob(filePathStart + '*'):
            os.remove(fl)
        for filename in listdir_fullpath(tempDir):
            if (os.path.isfile(filename) == False):
                shutil.rmtree(filename)
            else:
                os.remove(filename)

        fileNameStart = filePathStart.split('/')[-1]
        print ('fileNameStart:' + fileNameStart)
        if (runGapConfigs['backup_files'] == 'Y'):
            for fl in glob.glob(monitorDir + fileNameStart + '*'):
                shutil.copy(fl, runGapConfigs['backup_dir'])
        if (runGapConfigs['remove_files'] == 'Y'):
            for fl in glob.glob(monitorDir + fileNameStart + '*'):
                os.remove(fl)


    if (config['applescript']['close_sheet'] == 'Y'):
        scpt.call('closeSheet')

if __name__ == '__main__':
    main()
