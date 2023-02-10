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
import configparser
import logging
import logging.config

# 3rd party classes
import applescript

# Custom Classes
sys.path.insert(1, 'models') # Add to sys.path the directory with custom classes
import ws.createWrktFromSheet as createWrktSheet
import util.timeConv as tc
import dao.exerciseSheet as exSheetDao
from ExerciseInfo_Class import ExerciseInfo
from Weather_Class import WeatherInfo
import ws.updateWrkt as updateWrkt
import ws.createWrkt as createWrkt
import ws.getWrkt as getWrkt

config = configparser.ConfigParser()
logging.config.fileConfig('logging.conf')
logger = logging.getLogger()
createWrktSheet.logger = logger
exSheetDao.logger = logger
updateWrkt.logger = logger
createWrkt.logger = logger
getWrkt.logger = logger


def processUpdates(scpt, nbrRows, wsConfig):
    '''
    Gets number of workouts passed and send them to database using create workout sheet api.
    Arguments
        scpt - initialized applescript for connecting to numbers spreadsheet
        nbrRows - number of rows to read from spreadsheet
    Returns result of update webservice call
    '''
    logger.info('processUpdates: ' + str(nbrRows))
    sheetWrktLst = exSheetDao.getRecentWrkts(scpt, nbrRows)
    logger.debug(sheetWrktLst)
    # r = createWrktSheet.create(sheetWrktLst, wsConfig)
    wrktLst = calcWrktFieldsFromSheet(sheetWrktLst)
    r = updateWrkt.update(wrktLst, wsConfig)
    return r

def calcWrktFieldsFromSheet(sheetWrktLst):
    updtWrktLst = []
    for wrkt in sheetWrktLst:
        logger.debug('Workout for ' + str(wrkt['wrkt_dt']))
        ex = ExerciseInfo()
        ex.from_dict(wrkt)
        notes_dict = breakupNotes(ex.userNotes)
        ex.userNotes = notes_dict['notes']
        ex.clothes = notes_dict['clothes']
        # For now will ignore the weather from Notes
        ex.startWeather = WeatherInfo()
        ex.startWeather.from_dict(notes_dict['weatherStart'])
        # ex.endWeather =  notes_dict['weatherEnd']
        ex.endWeather = WeatherInfo()
        ex.endWeather.from_dict(notes_dict['weatherEnd'])
        cat_split = ex.category.split(' - ')
        ex.category = cat_split[0]
        if len(cat_split) >1:
            ex.training_type = cat_split[1]

        logger.info(ex)
        updtWrktLst.append(ex)
    return updtWrktLst

def breakupNotes(rec):
    '''
    Use regular expression patterns to get the start, end, and clothes from passed in record.
    Gets the last position of the sections broken out to get the remainder of the notes.
    Returns dictionary of the pulled values. Any sections not found will have an empty string.
        Return dictionary keys are weatherStart, weatherEnd, clothes, remainingNotes
    '''
    logger.debug('Input Record:' + str(rec))
    d = {}
    if rec == None:
        return None

    oldRecPattern = r'^[\d|:](.*?)[am|pm] '
    weatherPattern = r'^\d(.*?)(\. |\n)'
    weatherStartPattern = r'Start:(.*?)([a-z]\.|\n)'
    weatherEndPattern = r'End:(.*?)([a-z]\.|\n)'
    clothesPattern = r'(Shorts|Tights)(.{0,125}?)(\.|\n)'

    matchWeatherStart = re.search(weatherStartPattern, rec, flags=re.IGNORECASE)
    matchWeather = re.search(weatherPattern, rec, flags=re.IGNORECASE)
    endMatchPos = 0
    if matchWeatherStart:
        weatherStart = matchWeatherStart.group(0).strip()
        endMatchPos = max(endMatchPos, matchWeatherStart.end(0))
    elif matchWeather:
        weatherStart = matchWeather.group(0).strip()
        endMatchPos = max(endMatchPos, matchWeather.end(0))
    else:
        d['weatherStart'] = ''
        weatherStart = ''
    matchWeatherEnd = re.search(weatherEndPattern, rec, flags=re.IGNORECASE)
    if matchWeatherEnd:
        weatherEnd = matchWeatherEnd.group(0).strip()
        endMatchPos = max(endMatchPos, matchWeatherEnd.end(0))
    else:
        weatherEnd = ''
    matchClothes = re.search(clothesPattern,rec, flags=re.IGNORECASE)
    if matchClothes:
        d['clothes'] = matchClothes.group(0).strip()
        endMatchPos = max(endMatchPos, matchClothes.end(0))
    else:
        d['clothes'] = ''

    d['notes'] = rec[endMatchPos:].strip()

    d['weatherStart'] = splitWeather(weatherStart)
    d['weatherEnd'] = splitWeather(weatherEnd)
    logger.debug('Weather Start: ' + str(d['weatherStart']))
    logger.debug('Weather End: ' + str(d['weatherEnd']))

    return d

def splitWeather(wethrStr, keySuffix=''):
    '''
    Splits up weather from passed in string.
    Returns a dictionary of weather values.
    Key names can have the keySuffix appended to the end of each name. Default is no suffix
    '''

    wethrDict = {}

    if wethrStr == '':
        return wethrDict

    wethrLst = wethrStr.split(',')
    if len(wethrLst) == 5:
        wethrDict['temp' + keySuffix] = wethrLst[0].strip().split(' ')[1]
        wethrDict['wethr_cond' + keySuffix] = ' '.join(wethrLst[0].strip().split(' ')[3:])
        wethrDict['hmdty' + keySuffix] = wethrLst[1].strip().split(' ')[0]
        wethrDict['wind_speed' + keySuffix] = wethrLst[2].strip().split(' ')[2]
        wethrDict['wind_gust' + keySuffix] = wethrLst[3].strip().split(' ')[2].split('mph')[0]
        wethrDict['temp_feels_like' + keySuffix] = wethrLst[4].strip().split(' ')[2]
    elif len(wethrLst) == 3:
        wethrDict['temp' + keySuffix] = wethrLst[0].strip().split(' ')[1]
        wethrDict['hmdty' + keySuffix] = wethrLst[1].strip().split(' ')[0]
        wethrDict['temp_feels_like' + keySuffix] = wethrLst[2].strip().split(' ')[2]
    elif len(wethrLst) == 1:
        wethrLst = wethrStr.split(' ')
        if wethrLst[0].isdigit() == False:
            wethrDict['temp' + keySuffix] = wethrLst[1].strip()
            if len(wethrLst) > 3:
                wethrDict['hmdty' + keySuffix] = wethrLst[3].strip()
            if len(wethrLst) >= 8:
                wethrDict['temp_feels_like' + keySuffix] = wethrLst[8].strip()
        elif len(wethrLst) == 5:
            wethrDict['temp' + keySuffix] = wethrLst[0].strip()
            if wethrLst[2].isdigit():
                wethrDict['hmdty' + keySuffix] = wethrLst[2].strip()
            else:
                wethrDict['temp_feels_like' + keySuffix] = wethrLst[4].strip()
        elif len(wethrLst) == 2:
            wethrDict['temp' + keySuffix] = wethrLst[0].strip()

    return wethrDict

def sheetFromServer(scpt, nbrRows, config):
    # Get last N records from spreadsheet
    sheet_wrkt_lst = exSheetDao.getRecentWrkts(scpt, nbrRows)
    # Get earliest workout date from returned records
    earliest_dt = sheet_wrkt_lst[0]['wrkt_dttm']

    # Get all workouts >= earliest workout date
    server_wrkt_json = getWrkt.get_wrkt(earliest_dt, config['webservices'])
    # TODO need to check for if there is a next to loop through reading
    #   server_wrkt_json['_links']['next']
    server_wrkt_json_lst = server_wrkt_json['items']
    server_ex_lst = []
    for server_wrkt in server_wrkt_json_lst:
        logger.info(str(server_wrkt['wrkt_dttm']))
        ex = ExerciseInfo()
        ex.startWeather = WeatherInfo()
        ex.endWeather = WeatherInfo()
        ex.from_dict(server_wrkt)
        if ex.startTime < earliest_dt:
            logger.info('Skip record for date {} since it is before {}'.format(str(ex.startTime), str(earliest_dt)))
        else:
            logger.info('Will process ' + str(ex))
            logger.info('Distance: {}, Duration: {} seconds, {}'.format(str(ex.distTot), ex.totTmSec, ex.durTot))
            ex.userNotes = ex.combinedNotes()
            server_ex_lst.append(ex)

    logger.info('\ngenerate Dictionary for updating Sheet')
    server_ex_lst_create = []
    # Update spreadsheet
    for ex_server in server_ex_lst:
        logger.info('exercise from server: ' + str(ex_server.startTime))
        match_found = False
        ex_dict = ex_server.to_psite_dict(dateTimeFormat='%m/%d/%Y %H:%M:%S')
        ex_dict['etype'] = ex_dict['type']
        # ex_dict['wrkt_dt'] = ex_dict['wrkt_dttm']
        ex_dict['dur_str'] = ex_server.dur_str(forceHr=True)
        ex_dict['category'] = ex_server.combinedCategory()

        for ex_sheet_dict in sheet_wrkt_lst:
            logger.info('exercise from sheet: ' + str(ex_sheet_dict['wrkt_dttm']))
            # ex_sheet = ExerciseInfo()
            # ex_sheet.from_dict(ex_sheet_dict)
            # if ex_sheet.startTime == ex_server.startTime:
            if ex_sheet_dict['wrkt_dt'] == ex_dict['wrkt_dttm']:
                match_found = True
                ex_sheet_dict['hr'] = int(ex_sheet_dict['hr'])
                ex_sheet_dict['cal_burn'] = int(ex_sheet_dict['cal_burn'])
                if 'notes' not in ex_sheet_dict:
                    ex_sheet_dict['notes'] = ''
                diff = exSheetDao.getDiffWrktDict(ex_sheet_dict, ex_dict)
                # diff = ex_sheet.compareFields(ex_server)
                if diff != 'No Differences':
                    logger.info('Differences: {}'.format(diff))
                    exSheetDao.updateRows(scpt, ex_sheet_dict['rowVal'], ex_dict)
                break
        if not match_found:
            server_ex_lst_create.append(ex_dict)

    # Add workouts that are not on sheet
    for server_ex_create in server_ex_lst_create:
        try:
            scpt.call('addExercise', server_ex_create['wrkt_dttm'], server_ex_create['etype'], server_ex_create['dur_str'], server_ex_create['dist_mi'], 'mile', server_ex_create['hr'], server_ex_create['cal_burn'], server_ex_create['notes'], '', server_ex_create['gear'], server_ex_create['category'], server_ex_create['elevation'])
        except:
            logger.error('addExercise Unexpected Error')
            logger.error(sys.exc_info())
            raise


def main():
    '''
    MAIN
    '''
    logger.info('Start UpdtRecentWrkts')

    # Get config details
    progDir = os.path.dirname(os.path.abspath(__file__))
    config.read(progDir + "/config.txt")

    sheetName = config['applescript']['sheet_name']

    scpt = exSheetDao.initializeAppleScriptFunc( os.path.join(os.getenv('code'), config['applescript']['script_path'], config['applescript']['script_name']), sheetName)

    result = processUpdates(scpt, config['update_workouts']['nbr_records'], config['webservices'])

    # logger.info(result['wrktNotUpdtLst'])
    # if len(result['wrktNotUpdtLst']) >0:
    #     createWrkt.create_json(result['wrktNotUpdtLst'],config['webservices'])

    exSheetDao.closeSheet(scpt, config['applescript']['close_sheet'])

    logger.info('End UpdtRecentWrkts')

if __name__ == '__main__':
    main()
