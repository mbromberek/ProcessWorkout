# First party classes
import os, sys
import logging
import logging.config

# Third party classes
import configparser
import requests

# Custom classes
from ExerciseInfo_Class import ExerciseInfo

def create(exLst, wsConfig):
    wrktLst = []

    # Convert ExerciseInfo object to Dictionary
    for ex in exLst:
        wrkt = ex.to_psite_dict()
        if ex.type != 'Strength Training':
            wrkt.pop('notes',None) #remove Notes field
        wrktLst.append(wrkt)

    r = create_json(wrktLst, wsConfig)

    return r

def create_json(wrktLst, wsConfig):
    server = wsConfig['server']
    port = wsConfig['port']
    token = wsConfig['token']
    logger.debug('create_json')
    logger.debug(wrktLst)

    # Call webservice
    r = requests.post(server + ':' + port + '/api/workout', json=wrktLst, headers={'Authorization':'Bearer ' + token}, verify=wsConfig['verifyCert'] == 'Y')
    logger.info('Create Result: ' + str(r))
    if r.status_code == 400:
        logger.info(r.json())
    if r.status_code == 201:
        logger.info("Create Workout Successful")
    if r.status_code == 401:
        logger.error('Unauthorized Access')

    return r
