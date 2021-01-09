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

config = configparser.ConfigParser()
logging.config.fileConfig('logging.conf')
logger = logging.getLogger()
createWrktSheet.logger = logger
exSheetDao.logger = logger

def processUpdates(scpt, nbrRows, wsConfig):
    '''
    Gets number of workouts passed and send them to database using create workout sheet api.
    Arguments
        scpt - initialized applescript for connecting to numbers spreadsheet
        nbrRows - number of rows to read from spreadsheet
    Returns result of update webservice call
    '''
    logger.info('processUpdates: ' + str(nbrRows))
    wrktLst = exSheetDao.getRecentWrkts(scpt, nbrRows)
    r = createWrktSheet.create(wrktLst, wsConfig)
    return r


def main():
    '''
    MAIN
    '''
    logger.info('Start UpdtRecentWrkts')

    # Get config details
    progDir = os.path.dirname(os.path.abspath(__file__))
    config.read(progDir + "/config.txt")

    sheetName = config['applescript']['sheet_name']

    scpt = exSheetDao.initializeAppleScriptFunc( os.path.join(config['applescript']['script_path'], config['applescript']['script_name']), sheetName)

    processUpdates(scpt, config['update_workouts']['nbr_records'], config['webservices'])

    exSheetDao.closeSheet(scpt, config['applescript']['close_sheet'])

    logger.info('End UpdtRecentWrkts')

if __name__ == '__main__':
    main()
