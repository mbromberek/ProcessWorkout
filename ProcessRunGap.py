#! /Users/mikeyb/Applications/python3
# -*- coding: utf-8 -*-

'''
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
'''

# First party classes
import os,glob,shutil, platform
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
import ws.createWrkt as createWrkt
import ws.updateWrkt as updateWrkt
import NormalizeWorkout.parse.fitParse as fitParse

config = configparser.ConfigParser()
logging.config.fileConfig('logging.conf')
logger = logging.getLogger()
createWrktSheet.logger = logger
createWrktBrkdn.logger = logger
exSheetDao.logger = logger
createWrkt.logger = logger

METERS_TO_FEET = 3.28084

def determineGear(ex):
    '''
    determines gear based on the type of workout and if workout is a Run it looks at the category to determine shoes.
    Returns the determined Gear
    '''
    gear = ''
    try:
        if ex.type.lower() == 'running':
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
    if ex.type.lower() == 'running':
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

def weatherApiCall(url, token):
    r = requests.get(url, headers={'key':token}, verify=True)

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

    if config['weather_details']['log_details'] == 'Y':
        f = open('/tmp/weatherData' + ex.startTime.strftime('%Y%m') + '.txt', 'a')
        f.write('Start Time:' + ex.startTime.strftime('%Y-%m-%dT%H:%M:%S') + '\n')
        f.write('Lat: ' + str(ex.startLat) + ' Lon: ' + str(ex.startLon) + '\n')
        f.write(ex.startWeather.generateWeatherUserNotes('DarkSkyStart: '))
        f.write(getWeatherApi(ex.startLat, ex.startLon, roundHour(ex.startTime)).generateWeatherUserNotes('WeatherStart: '))
        f.write(ex.endWeather.generateWeatherUserNotes('DarkSkyEnd: '))
        f.write(getWeatherApi(ex.endLat, ex.endLon, roundHour(ex.endTime)).generateWeatherUserNotes('WeatherEnd: '))
        f.write('End Time:' + ex.startTime.strftime('%Y-%m-%dT%H:%M:%S') + '\n')
        f.close()

    #TODO change to use Weather_class.generateWeatherUserNotes
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
    w.humidity = weatherData['currently']['humidity']*100
    w.windSpeed = weatherData['currently']['windSpeed']
    w.summary = weatherData['currently']['summary']
    w.windGust = weatherData['currently']['windGust']
    w.lat = lat
    w.lon = lon
    w.time = tm
    w.dewPoint = weatherData['currently']['dewPoint']

    if (config['dark_sky']['save_weather'] == 'Y'):
        with open('/tmp/weatherData' + tm.strftime('%Y%m%dT%H%M%S') + '.txt', 'w') as outfile:
            json.dump(weatherData, outfile)

    return w

def getWeatherApi(lat, lon, dttm):
    baseURL = config['weather_api']['base_url']
    key = config['weather_api']['key']
    loc = str(lat) + ',' + str(lon)

    url = baseURL + '/history.json' + '?q=' + loc + '&dt=' + dttm.strftime('%Y-%m-%d') + '&hour=' + dttm.strftime('%H')

    w = WeatherInfo()
    weatherData = weatherApiCall(url, key)
    logger.info(weatherData)
    weatherHistory = weatherData['forecast']['forecastday'][0]['hour'][0]
    w.temp = weatherHistory['temp_f']
    w.apparentTemp = weatherHistory['feelslike_f']
    w.humidity = weatherHistory['humidity']
    w.windSpeed = weatherHistory['wind_mph']
    w.summary = weatherHistory['condition']['text']
    w.windGust = weatherHistory['gust_mph']
    w.dewPoint = weatherHistory['dewpoint_f']
    w.windDegree = weatherHistory['wind_degree']
    w.windChill = weatherHistory['windchill_f']
    w.lat = lat
    w.lon = lon
    w.time = weatherHistory['time']

    if (config['weather_api']['save_weather'] == 'Y'):
        with open('/tmp/weatherData' + w.tm.strftime('%Y%m%dT%H%M%S') + '.txt', 'w') as outfile:
            json.dump(weatherData, outfile)

    return w

def roundHour(dttm):
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    return (dttm.replace(second=0, microsecond=0, minute=0, hour=dttm.hour)
               +datetime.timedelta(hours=dttm.minute//30))

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
    txtLst.append('{0:.{1}f}'.format(w.humidity,0))
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
    ex.fitFile = fileNameStart + '.fit'
    ex.metadataFile = filename.split('/')[-1]

    ex.type = data['activityType']['sourceName'].title()

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
        if ex.source == 'Coros':
            ex.elevationGain = ex.elevationGain * METERS_TO_FEET
            ex.elevationLoss = ex.elevationLoss * METERS_TO_FEET

    ex.category = determineCategory(ex)

    exBrkdn = getWrktBrkdnConfig(ex.category)

    # Want to leave gear empty so server will determine it
    # if ex.gear == '':
    #     ex.gear = determineGear(ex)

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
            if ex.category == 'Training' and ex.wrktSegments is not None:
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
    try:
        mileSplitsDf = wrktSplits.breakDownWrkt( \
            srcDir, fName=ex.rungapFile, \
            splitBy='mile' \
        )
        ex.mileSplits = \
          ExerciseInfo.wrkt_intrvl_from_dict(mileSplitsDf.to_dict(orient='records'), 'mile')
    except:
        logger.error('<ERROR> Breakdown Workout by mile Unexpected Error')
        logger.error(sys.exc_info())
        # raise

    if os.path.exists(srcDir + '/' + ex.fitFile):
        lapsDf, pointsDf = fitParse.get_dataframes(srcDir + '/' + ex.fitFile)
        pointsEventsDf = fitParse.normalize_laps_points(lapsDf, pointsDf)

        summaryLapDf = wrktSplits.summarizeWrktSplit(pointsEventsDf, summarizeBy='lap')
        summaryMileDf = wrktSplits.summarizeWrktSplit(pointsEventsDf, summarizeBy='mile')
        summaryResumeDf = wrktSplits.summarizeWrktSplit(pointsEventsDf, summarizeBy='resume')

        if ex.category == 'Training' and summaryLapDf.shape[0] >=3:
            summaryLapDf.loc[summaryLapDf.index[0],'interval_desc'] = 'Warm Up'
            summaryLapDf.loc[summaryLapDf.index[-1],'interval_desc'] = 'Cool Down'
            summaryLapDf['interval'] = summaryLapDf['interval'] 
            summaryLapDf['interval_desc'].fillna('', inplace=True)

        #needed since old process has interval instead of mile number so starts at 0
        summaryMileDf['interval'] = summaryMileDf['interval'] -1

        ex.lapSplits = \
            ExerciseInfo.wrkt_intrvl_from_dict(summaryLapDf.to_dict(orient='records'), 'interval')
        ex.mileSplits = \
            ExerciseInfo.wrkt_intrvl_from_dict(summaryMileDf.to_dict(orient='records'), 'interval')
        ex.pauseSplits = \
            ExerciseInfo.wrkt_intrvl_from_dict(summaryResumeDf.to_dict(orient='records'), 'interval')
    try:
        intrvlSplitsDf = wrktSplits.breakDownWrkt( \
            srcDir, fName=ex.rungapFile, \
            splitBy='lap' \
        )
        if intrvlSplitsDf.shape[0] >1:
            ex.intrvlSplits = \
              ExerciseInfo.wrkt_intrvl_from_dict(intrvlSplitsDf.to_dict(orient='records'), 'lap')
    except:
        logger.error('<ERROR> Breakdown Workout by segment Unexpected Error')
        logger.error(sys.exc_info())

    try:
        resumeSplitsDf = wrktSplits.breakDownWrkt( \
            srcDir, fName=ex.rungapFile, \
            splitBy='resume' \
        )
        if resumeSplitsDf.shape[0] >1:
            ex.pauseSplits = \
              ExerciseInfo.wrkt_intrvl_from_dict(resumeSplitsDf.to_dict(orient='records'), 'resume')
    except:
        logger.error('<ERROR> Breakdown Workout by resume Unexpected Error')
        logger.error(sys.exc_info())

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
        if ex.durTot != '':
            duration = ex.durTot
        else:
            duration = tc.formatNumbersTime(ex.hourTot, ex.minTot, ex.secTot)
        if ex.userNotes == '':
            ex.userNotes = ex.combinedNotes()
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

def saveExToSite(exLst, wsConfig):
    dateTimeSheetFormat = '%Y-%m-%dT%H:%M:%S'
    createWrktResp = createWrkt.create(exLst, wsConfig)
    if createWrktResp.status_code == 201:
        # If create workout was successful upload workout file
        createWrktJson = createWrktResp.json()
        for wrkt in createWrktJson:
            # logger.debug('Create Workout {}: {}'.format(wrkt['id'],wrkt['wrkt_dttm']))
            for ex in exLst:
                exStrtTmStr = ex.startTime.strftime(dateTimeSheetFormat) + 'Z'
                # logger.debug('Exercise: ' + exStrtTmStr)
                if exStrtTmStr == wrkt['wrkt_dttm']:
                    updateWrkt.uploadFile(wrkt['id'], ex, wsConfig, config['rungap']['monitor_dir'])
        return createWrktResp.json()

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
        result = updtRecentWrkts.processUpdates(scpt, config['update_workouts']['nbr_records'], config['webservices'])

        logger.info(result['wrktNotUpdtLst'])
        if len(result['wrktNotUpdtLst']) >0:
            createWrkt.create_json(result['wrktNotUpdtLst'],config['webservices'])


    uncompressMonitorToTemp(monitorDir, tempDir)

    filesToProcess = getFiles(tempDir)

    exLst = processExercises(filesToProcess)

    if len(exLst) > 0:
        saveExToSheet(exLst, scpt)
        # saveExToDb(exLst, config['webservices'])
        saveExToSite(exLst, config['webservices'])

    cleanProcessedFile(exLst, monitorDir, tempDir)

    hostKeepOpenLst = config['applescript']['keep_sheet_open_on'].split(',')
    logger.info(str(hostKeepOpenLst))
    logger.info(platform.node())

    if (config['applescript']['close_sheet'] == 'Y' \
    and platform.node() not in hostKeepOpenLst):
        scpt.call('closeSheet')

    logger.info('End ProcessRunGap')

def process_workouts():
    logger.info('Start ProcessRunGap')

    # Get config details
    progDir = os.path.dirname(os.path.abspath(__file__))
    config.read(progDir + "/config.txt")

    sheetName = config['applescript']['sheet_name']

    runGapConfigs = config['rungap']
    monitorDir = runGapConfigs['monitor_dir']
    tempDir = runGapConfigs['temp_dir']

    scpt = exSheetDao.initializeAppleScriptFunc( os.path.join(config['applescript']['script_path'], config['applescript']['script_name']), sheetName)

    # logger.debug('monitorDir:' + monitorDir)
    # logger.debug('tempDir: ' + tempDir)
    # logger.debug('Monitor Directory Contents:')
    # logger.debug(os.listdir(monitorDir))

    if (config['update_workouts']['process_with_new'] == 'Y'):
        updtRecentWrkts.sheetFromServer(scpt, config['update_workouts']['nbr_records'], config)

    # TODO Process new files
    # Get Worktouts from files
    uncompressMonitorToTemp(monitorDir, tempDir)
    filesToProcess = getFiles(tempDir)
    newExLst = processExercises(filesToProcess)

    # Create workout on server
    if len(newExLst) > 0:
        wrkt_dict_lst = saveExToSite(newExLst, config['webservices'])
        logger.debug(str(wrkt_dict_lst))
        # Use JSON that came back from server to update spreadsheet
        exLst = ExerciseInfo.ex_lst_from_dict(wrkt_dict_lst)
        saveExToSheet(exLst, scpt)
        cleanProcessedFile(newExLst, monitorDir, tempDir)

    hostKeepOpenLst = config['applescript']['keep_sheet_open_on'].split(',')
    logger.info(str(hostKeepOpenLst))
    logger.info(platform.node())

    if (config['applescript']['close_sheet'] == 'Y' \
    and platform.node() not in hostKeepOpenLst):
        scpt.call('closeSheet')

    logger.info('End ProcessRunGap')


if __name__ == '__main__':
    # main()
    process_workouts()
