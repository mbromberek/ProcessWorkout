# First party classes
import os, sys
import logging
import logging.config
import requests

# Third party classes
# from flask import Flask
# from flask import request, Response
# from flask import jsonify
# import simplejson as json
import configparser

# Custom classes
from ExerciseInfo_Class import ExerciseInfo

def create(ex):
    # Convert ExerciseInfo object to Dictionary
    wrkt = {'workout':ex.to_dict()}
    logger.info(wrkt)

    # Call webservice
    r = requests.post('http://localhost:5000/api/v1/wrkt', json=wrkt)
    logger.info(r)

    return r

# def apiCall(url):
#     r = requests.get(url)
#     data = r.json()
#     return data
