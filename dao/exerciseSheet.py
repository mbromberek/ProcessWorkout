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
import util.timeConv as tc

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

def closeSheet(scpt, closeSheetFlag='Y'):
    if (closeSheetFlag == 'Y'):
        scpt.call('closeSheet')

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
        exSheet['dateVal'] = tc.adjustAppleNumbersTimeForDst(exSheet['dateVal'])
        wrkt['wrkt_dttm'] = exSheet['dateVal']
        wrkt['rowVal'] = exSheet['rowVal']
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
        if type(exSheet['paceVal']) == int or type(exSheet['paceVal']) == float:
            h,m,s = tc.breakTimeFromSeconds(exSheet['paceVal'])
        else:
            h = 0
            m = 0
            s = 0
        wrkt['pace'] = str(h)+'h ' + str(m)+'m ' + str(s)+'s'
        wrkt['elevation'] = exSheet['eleVal']
        wrktLst.append(wrkt)

    wrktLst.sort(key=lambda x: x['wrkt_dttm'], reverse=False)
    return wrktLst

def updateRows(scpt, row_nbr, ex_dict):
    try:
        scpt.call('updateExercise', row_nbr, ex_dict)
    except:
        logger.error('updateExercise Unexpected Error')
        logger.error(sys.exc_info())
        raise

def getDiffWrktDict(sheet_wrkt, server_wrkt):
    sheetCompareFields = ['wrkt_dt', 'wrkt_typ', 'tot_tm', 'dist', 'hr', 'cal_burn', 'notes', 'gear', 'category', 'elevation']
    serverCompareFields = ['wrkt_dttm', 'type', 'dur_str', 'dist_mi', 'hr', 'cal_burn', 'notes', 'gear', 'category', 'elevation']
    for field_nbr in range(0, len(serverCompareFields)):
        if sheetCompareFields[field_nbr] not in sheet_wrkt:
            sheet_wrkt[sheetCompareFields[field_nbr]] = ''
        if serverCompareFields[field_nbr] not in server_wrkt:
            server_wrkt[serverCompareFields[field_nbr]] = ''

        if str(sheet_wrkt[sheetCompareFields[field_nbr]]) != str(server_wrkt[serverCompareFields[field_nbr]]):
            return 'Field {} is different between sheet ({}) and server ({})'.format(serverCompareFields[field_nbr], str(sheet_wrkt[sheetCompareFields[field_nbr]]), str(server_wrkt[serverCompareFields[field_nbr]]))

    return 'No Differences'
