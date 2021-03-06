#! /Users/mikeyb/Applications/python3
# -*- coding: utf-8 -*-

'''
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
'''

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
import logging
import logging.config

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
import util.WrktSummary as wrktSum
import dao.files as fao
import ws.createWrktFromSheet as createWrktSheet
import ws.createWrktFromBrkdn as createWrktBrkdn
import UpdtRecentWrkts as updtRecentWrkts
import dao.exerciseSheet as exSheetDao

config = configparser.ConfigParser()
logging.config.fileConfig('logging.conf')
logger = logging.getLogger()
createWrktSheet.logger = logger
createWrktBrkdn.logger = logger
exSheetDao.logger = logger

def determineGear(ex):
    '''
    determines gear based on the type of workout and if workout is a Run it looks at the category to determine shoes.
    Returns the determined Gear
    '''
    gear = ''
    try:
        if ex.type == 'Running':
            if config.has_option('gear','shoe_' + ex.category.replace(' ','_').lower()):
                gear = config['gear']['shoe_' + ex.category.replace(' ','_').lower()]
            else:
                gear = config['gear']['shoe_default']
        else:
            gear = config['gear']['default_' + ex.type]
    except:
        gear = ''

    return gear

def determineCategory(ex):
    '''
    Using passed in exercise information determine the category for the exercise.
    '''
    cat = ''
    categoryConfigs = ''
    if ex.type == 'Running':
        categoryConfigs = config['run_category']
        # Get day of the exercise
        if ex.startTime.strftime('%A') in categoryConfigs:
            dayCat = categoryConfigs[ex.startTime.strftime('%A')]
            if len(dayCat.split(',')) >1:
                # print('Time: ' + str((ex.secTot + ex.minTot*60 + ex.hourTot*60*60)))
                # print('Distance: ' + str(ex.distTot))
                # print('Pace:' + str((ex.secTot + ex.minTot*60 + ex.hourTot*60*60) / ex.distTot))
                for catOption in dayCat.split(','):
                    if catOption.replace(' ','_').lower() + '_max_pace' in categoryConfigs:
                        if float(categoryConfigs[catOption.replace(' ','_').lower() + '_max_pace']) > (ex.secTot + ex.minTot*60 + ex.hourTot*60*60) / ex.distTot:
                            cat = catOption
                            break
                    elif catOption.replace(' ','_').lower() + '_min_dist' in categoryConfigs:
                        if float(categoryConfigs[catOption.replace(' ','_').lower() + '_min_dist']) < ex.distTot:
                            cat = catOption
                            break
                if cat == '':
                    cat = dayCat.split(',')[-1]
            else:
                cat = dayCat

    else:
        cat = 'Easy'
    return cat

#######################################################
# API call
#######################################################
def apiCall(url):
    r = requests.get(url)
    data = r.json()
    return data

def getWrktWeather(ex, data):
    '''
    Get weather data using passed in data
    Store weather in Exercise object and return it
    '''
    laps = data['laps']
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

    ex.userNotes = ex.userNotes + generateWeatherUserNotes(ex.startWeather)
    ex.userNotes = ex.userNotes + generateWeatherUserNotes(ex.endWeather)

    return ex

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
    w.lat = lat
    w.lon = lon
    w.time = tm

    if (config['dark_sky']['save_weather'] == 'Y'):
        with open('/tmp/weatherData' + tm.strftime('%Y%m%dT%H%M%S') + '.txt', 'w') as outfile:
            json.dump(weatherData, outfile)

    return w

def generateWeatherUserNotes(w):
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

def generateBrkdnUserNotes(ex):
    '''
    Generates notes of workout break down for User Notes field of Exercise spreadsheet.
    Puts all the text into an array that is joined into the returned string.
    '''
    txtLst = []
    txtLst.append('Warm Up: ')
    txtLst.append(tc.formatNumbersTime(*tc.breakTimeFromSeconds(ex.warmUpTotDurSec)))
    txtLst.append(', ')
    txtLst.append('{0:.{1}f}'.format(ex.warmUpTotDistMi,2))
    txtLst.append(' miles, ')
    txtLst.append(tc.formatNumbersTime(*tc.breakTimeFromSeconds(ex.warmUpTotPaceSec)))
    txtLst.append(' per mile\n')

    txtLst.append('Workout: ')
    txtLst.append(tc.formatNumbersTime(*tc.breakTimeFromSeconds(ex.intvlTotDurSec)))
    txtLst.append(', ')
    txtLst.append('{0:.{1}f}'.format(ex.intvlTotDistMi,2))
    txtLst.append(' miles, ')
    txtLst.append(tc.formatNumbersTime(*tc.breakTimeFromSeconds(ex.intvlTotPaceSec)))
    txtLst.append(' per mile\n')

    txtLst.append('Cool Down: ')
    txtLst.append(tc.formatNumbersTime(*tc.breakTimeFromSeconds(ex.coolDnTotDurSec)))
    txtLst.append(', ')
    txtLst.append('{0:.{1}f}'.format(ex.coolDnTotDistMi,2))
    txtLst.append(' miles, ')
    txtLst.append(tc.formatNumbersTime(*tc.breakTimeFromSeconds(ex.coolDnTotPaceSec)))
    txtLst.append(' per mile\n')
    return ''.join(txtLst)

def uncompressMonitorToTemp(monitorDir, tempDir):
    '''
    Uncompress files from monitor directory into temp directory
    '''
    zipFiles = []
    compressFileRegex = re.compile(r'(.zip|.gz)$')
    for filename in os.listdir(monitorDir):
        # Checks if compressed file
        if compressFileRegex.search(filename):
            z = zipfile.ZipFile(monitorDir + filename,mode='r')
            z.extractall(path=tempDir)
            zipFiles.append(monitorDir + filename)

def getFiles(tempDir):
    '''
    Loop through files and load to a list
    '''
    # print(fao.listdir_fullpath(tempDir))
    filesToProcess = []
    for filename in fao.listdir_fullpath(tempDir):
        if (os.path.isfile(filename) == False and filename != '__MACOSX'):
            # print('directory')
            filesToProcess.extend(fao.listdir_fullpath(filename))
        else:
            # print('file')
            filesToProcess.append(filename)
    return filesToProcess

def getWrktBrkdnConfig(cat):
    '''
    Gets the breakdown details for the passed workout category
    '''
    if cat.replace(' ','_').lower() + '_breakdown' in config:
        exBrkdn = config[cat.replace(' ','_').lower() + '_breakdown']
    else:
        exBrkdn = None
    return exBrkdn

def processExercises(filesToProcess):
    '''
    Loop through exercise files
    filesToProcess full path to files to check for processing. Will look at files to determine if they are valid for being processed.
    Exercise list will be in ascending order by start date/time
    '''
    exLst = []
    jsonFileRegex = re.compile(r'(metadata.json)$')
    jsonExtRegex = re.compile(r'(.json)$')
    for filename in filesToProcess:
        if jsonFileRegex.search(filename):
            logger.info('Process: ' + filename)
            exLst.append(processExercise(filename))
        else:
            logger.info('Do not process: ' + filename)
    exLst.sort(key=lambda x: x.startTime, reverse=False)
    return exLst

def processExercise(filename):
    '''
    Process Exercise in passed in filename
    Store into ExerciseInfo object

    Return: ExerciseInfo object
    '''

    with open(filename) as data_file:
        data = json.load(data_file)

    ex = ExerciseInfo()

    # Get just file name before first period
    fileNameStart = filename.split('/')[-1].split('.')[0]
    srcDir = '/'.join(filename.split('/')[:-1])

    ex.source = data['source']
    ex.originLoc = filename
    ex.rungapFile = fileNameStart + '.rungap.json'
    ex.metadataFile = filename.split('/')[-1]

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

    ex.totTmSec = data['duration']
    ex.hourTot, ex.minTot, ex.secTot = tc.breakTimeFromSeconds(ex.totTmSec)
    durTotNumbers = tc.formatNumbersTime(ex.hourTot, ex.minTot, ex.secTot)
    durTotSheets = tc.formatSheetsTime(ex.hourTot, ex.minTot, ex.secTot)

    ex.durTot = durTotSheets

    ex.avgHeartRate = data['avgHeartrate']

    ex.calTot = data['calories']

    if 'elevationGain' in data:
        ex.elevationGain = data['elevationGain']
        ex.elevationLoss = data['elevationLoss']

    ex.category = determineCategory(ex)

    exBrkdn = getWrktBrkdnConfig(ex.category)

    if ex.gear == '':
        ex.gear = determineGear(ex)

    # Pull data for getting weather
    if 'displayPath' in data:
        ex = getWrktWeather(ex, data)

    # Break Down Workout
    if exBrkdn is not None and exBrkdn['generate_table'] == 'Y':
        try:
            ex.wrktSegments = wrktSplits.breakDownWrkt( \
                srcDir, fName=ex.rungapFile, \
                splitBy=exBrkdn['split_type'] \
            )
            if ex.category == 'Training':
                wrkt_summary = wrktSum.calcWrktSummary(ex.wrktSegments, ex.category)

                ex.warmUpTotDistMi = wrkt_summary['warm_up']['dist_mi']
                ex.warmUpTotDurSec = wrkt_summary['warm_up']['dur_sec']
                ex.warmUpTotPaceSec = wrkt_summary['warm_up']['pace_sec']
                ex.warmUpTotEleUp = wrkt_summary['warm_up']['ele_up']
                ex.warmUpTotEleDown = wrkt_summary['warm_up']['ele_down']
                ex.coolDnTotDistMi = wrkt_summary['cool_down']['dist_mi']
                ex.coolDnTotDurSec = wrkt_summary['cool_down']['dur_sec']
                ex.coolDnTotPaceSec = wrkt_summary['cool_down']['pace_sec']
                ex.coolDnTotEleUp = wrkt_summary['cool_down']['ele_up']
                ex.coolDnTotEleDown = wrkt_summary['cool_down']['ele_down']

                ex.intvlTotDistMi = wrkt_summary['intvl_tot']['dist_mi']
                ex.intvlTotDurSec = wrkt_summary['intvl_tot']['dur_sec']
                ex.intvlTotPaceSec = wrkt_summary['intvl_tot']['pace_sec']
                ex.intvlTotEleUp = wrkt_summary['intvl_tot']['ele_up']
                ex.intvlTotEleDown = wrkt_summary['intvl_tot']['ele_down']
                ex.intvlAvgDistMi = wrkt_summary['intvl_avg']['dist_mi']
                ex.intvlAvgDurSec = wrkt_summary['intvl_avg']['dur_sec']
                ex.intvlAvgPaceSec = wrkt_summary['intvl_avg']['pace_sec']
                ex.intvlAvgEleUp = wrkt_summary['intvl_avg']['ele_up']
                ex.intvlAvgEleDown = wrkt_summary['intvl_avg']['ele_down']

                ex.userNotes = ex.userNotes + generateBrkdnUserNotes(ex)
        except:
            print('<ERROR> Breakdown Workout Unexpected Error')
            print(sys.exc_info())
            raise

    if (config['rungap']['print_data'] == 'Y'):
        printWrktDetails(filename, ex)

    return ex



def saveExToSheet(exLst, scpt):
    '''
    6) Save Exercise to spreadsheet
    '''
    dateTimeSheetFormat = '%m/%d/%Y %H:%M:%S'

    for ex in exLst:
        startDateTime = ex.startTime.strftime(dateTimeSheetFormat)
        distance = "%.2f" % ex.distTot
        duration = tc.formatNumbersTime(ex.hourTot, ex.minTot, ex.secTot)
        exBrkdn = getWrktBrkdnConfig(ex.category)
        logger.debug('Exercise startDateTime:' + str(startDateTime))
        logger.debug('dist:' + distance + ' ' + str(ex.distTot))
        logger.debug('duration:' + str(duration))

        try:
            scpt.call('addExercise',ex.eDate, ex.type, duration, distance, ex.distUnit, ex.avgHeartRate, ex.calTot, ex.userNotes, startDateTime, ex.gear, ex.category, ex.elevationChange())
        except:
            logger.error('addExercise Unexpected Error')
            logger.error(sys.exc_info())
            raise

        if ex.wrktSegments is not None and exBrkdn is not None:
            try:
                newTblNm = wrktSplits.calcTrngType(ex.wrktSegments, ex.category) \
                    + ex.startTime.strftime(' %Y-%m-%d')
                brkdnSheetNm = exBrkdn['sheet_name']

                wrktSumFrmla = wrktSum.calcWrktSumFrmla(ex.wrktSegments)

                # print('New Table Name: ' + newTblNm)
                scpt.call('generateWrktTable' \
                    , brkdnSheetNm, newTblNm \
                    , ex.wrktSegments.to_dict(orient='records') \
                    , wrktSumFrmla
                )
            except applescript.ScriptError:
                logger.error('generateWrktTable Unexpected Error')
                logger.error(sys.exc_info())
                raise

def saveExToDb(exLst, wsConfig):
    '''
    Save passed list of exercises to database using API call
    '''
    if wsConfig['save_to_db'] == 'Y':
        createWrktBrkdn.create(exLst, wsConfig)
    else:
        logger.info('Saving to Database turned off')

def cleanProcessedFile(exLst, monitorDir, tempDir):
    '''
    Clean up processed files
    '''
    for ex in exLst:
        # Remove files from temp folder
        fileNameChunks = ex.originLoc.split('.')
        filePathStart = fileNameChunks[0]
        # print ('filePathStart:' + filePathStart)
        for fl in glob.glob(filePathStart + '*'):
            os.remove(fl)
        for filename in fao.listdir_fullpath(tempDir):
            if (os.path.isfile(filename) == False):
                shutil.rmtree(filename)
            else:
                os.remove(filename)

        # Move file from backup to monitorDir and remove from monitorDir
        fileNameStart = filePathStart.split('/')[-1]
        # print ('fileNameStart:' + fileNameStart)
        if (config['rungap']['backup_files'] == 'Y'):
            for fl in glob.glob(monitorDir + fileNameStart + '*'):
                shutil.copy(fl, config['rungap']['backup_dir'])
        if (config['rungap']['remove_files'] == 'Y'):
            for fl in glob.glob(monitorDir + fileNameStart + '*'):
                os.remove(fl)

def printWrktDetails(filename, ex):
    '''
    Prints details about workout to console
    '''
    print('filename: ' + filename)
    print('RunGap file: ' + ex.rungapFile)
    print('Metadata file: ' + ex.metadataFile)

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
    print('')

#######################################################
# MAIN
#######################################################
def main():
    logger.info('Start ProcessRunGap')

    # Get config details
    progDir = os.path.dirname(os.path.abspath(__file__))
    config.read(progDir + "/config.txt")

    sheetName = config['applescript']['sheet_name']

    runGapConfigs = config['rungap']
    monitorDir = runGapConfigs['monitor_dir']
    tempDir = runGapConfigs['temp_dir']

    scpt = exSheetDao.initializeAppleScriptFunc( os.path.join(config['applescript']['script_path'], config['applescript']['script_name']), sheetName)

    if (config['rungap']['print_data'] == 'Y'):
        logger.debug('monitorDir:' + monitorDir)
        logger.debug('tempDir: ' + tempDir)
        logger.debug('Monitor Directory Contents:')
        logger.debug(os.listdir(monitorDir))

    if (config['update_workouts']['process_with_new'] == 'Y'):
        updtRecentWrkts.processUpdates(scpt, config['update_workouts']['nbr_records'], config['webservices'])

    uncompressMonitorToTemp(monitorDir, tempDir)

    filesToProcess = getFiles(tempDir)

    exLst = processExercises(filesToProcess)

    if len(exLst) > 0:
        saveExToSheet(exLst, scpt)
        saveExToDb(exLst, config['webservices'])

    cleanProcessedFile(exLst, monitorDir, tempDir)

    if (config['applescript']['close_sheet'] == 'Y'):
        scpt.call('closeSheet')

    logger.info('End ProcessRunGap')

if __name__ == '__main__':
    main()
