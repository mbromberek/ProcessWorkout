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
# import datetime

# Third party classes
# from flask import Flask
# from flask import request, Response
# from flask import jsonify
# import simplejson as json
import configparser

# Custom classes
from ExerciseInfo_Class import ExerciseInfo

def create(ex):

    wrkt = {'workout':ex}
    logger.info(wrkt)

    # Call webservice
    r = requests.post('http://localhost:5000/api/v1/wrkt_sheet', json=wrkt)
    logger.info(r)

    return r

# def apiCall(url):
#     r = requests.get(url)
#     data = r.json()
#     return data
