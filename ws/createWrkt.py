# First party classes
import os, sys
import logging
import logging.config
import requests

# Third party classes
import configparser

# Custom classes
from ExerciseInfo_Class import ExerciseInfo

def create(exLst, wsConfig):
    wrktLst = []
    server = wsConfig['server']
    port = wsConfig['port']
    token = wsConfig['token']

    # Convert ExerciseInfo object to Dictionary
    for ex in exLst:
        wrkt = ex.to_psite_dict()
        wrktLst.append(wrkt)

    wrktLstJson = {'workouts':wrktLst}
    logger.debug(wrktLstJson)

    # Call webservice
    r = requests.post(server + ':' + port + '/api/workout', json=wrktLstJson)
    logger.info(r)

    return r

# def apiCall(url):
#     r = requests.get(url)
#     data = r.json()
#     return data
