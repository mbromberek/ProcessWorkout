# First party classes
import os, sys
import logging
import logging.config

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
    wrkt = ex.to_dict()
    logger.info(wrkt)

    # Call webservice
    

    return wrkt

# def apiCall(url):
#     r = requests.get(url)
#     data = r.json()
#     return data