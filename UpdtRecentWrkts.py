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
# import pandas

# Custom Classes
sys.path.insert(1, 'models') # Add to sys.path the directory with custom classes
import ws.createWrktFromSheet as createWrktSheet
import util.timeConv as tc

config = configparser.ConfigParser()
logging.config.fileConfig('logging.conf')
logger = logging.getLogger()
createWrktSheet.logger = logger

def getRecentWrkts(scpt, nbrRows):
    '''
    Use AppleScript function getExercises
    Convert dictionary from AppleScript to dictionary for create workout API and return list of records read
    '''
    wrktLst = []
    dateTimeSheetFormat = '%m/%d/%Y %H:%M:%S'

    try:
        exSheetLst = scpt.call('getExercises',nbrRows)
    except:
        logger.error('getExercises Unexpected Error')
        logger.error(sys.exc_info())
        raise

    for exSheet in exSheetLst:
        wrkt = {}
        wrkt['wrkt_dt'] = exSheet['dateVal'].strftime(dateTimeSheetFormat)
        wrkt['wrkt_typ'] = exSheet['typeVal']
        h,m,s = tc.breakTimeFromSeconds(exSheet['durationVal'])
        wrkt['tot_tm'] = str(h)+'h ' + str(m)+'m ' + str(s)+'s'
        wrkt['dist'] = exSheet['distanseVal']
        wrkt['hr'] = exSheet['hrVal']
        wrkt['cal_burn'] = exSheet['caloriesVal']
        wrkt['notes'] = exSheet['noteVal']
        wrkt['gear'] = exSheet['gearVal']
        wrkt['category'] = exSheet['catVal']
        h,m,s = tc.breakTimeFromSeconds(exSheet['paceVal'])
        wrkt['pace'] = str(h)+'h ' + str(m)+'m ' + str(s)+'s'
        wrkt['elevation'] = exSheet['eleVal']
        wrktLst.append(wrkt)

    wrktLst.sort(key=lambda x: x['wrkt_dt'], reverse=False)
    return wrktLst

def initializeAppleScriptFunc(appleScriptName, sheetName):
    '''
    Read applescript file for reading and updating exercise spreadseeht
    After initializing it sets the sheetName to be updated.
    Return: AppleScript file for performing function calls
    '''
    scptFile = open(appleScriptName)
    scptTxt = scptFile.read()
    scpt = applescript.AppleScript(scptTxt)
    scpt.call('initialize',sheetName)
    return scpt


def sendUpdates(wrktLst):
    '''
    Create workouts one at a time using web service call
    '''
    logger.debug(wrktLst)

    for wrkt in wrktLst:
        createWrktSheet.create(wrkt)


def main():
    '''
    MAIN
    '''
    logger.info('Start UpdtRecentWrkts')

    # Get config details
    progDir = os.path.dirname(os.path.abspath(__file__))
    config.read(progDir + "/config.txt")

    sheetName = config['applescript']['sheet_name']

    scpt = initializeAppleScriptFunc( os.path.join(config['applescript']['script_path'], config['applescript']['script_name']), sheetName)

    wrktLst = getRecentWrkts(scpt, config['update_workouts']['nbr_records'])

    sendUpdates(wrktLst)

    if (config['applescript']['close_sheet'] == 'Y'):
        scpt.call('closeSheet')

    logger.info('End UpdtRecentWrkts')

if __name__ == '__main__':
    main()
