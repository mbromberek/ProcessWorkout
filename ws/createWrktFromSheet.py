#! /Users/mikeyb/Applications/python3
# -*- coding: utf-8 -*-

'''
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
'''

# First party classes
import os, sys
import logging
import logging.config
import requests

import configparser

# Custom classes
from ExerciseInfo_Class import ExerciseInfo

def create(exLst, wsConfig):
    server = wsConfig['server']
    port = wsConfig['port']

    wrkt = {'workouts':exLst}
    logger.debug(wrkt)

    # Call webservice
    r = requests.post(server + ':' + port + '/api/v1/wrkt_sheet', json=wrkt)
    logger.info(r)

    return r
