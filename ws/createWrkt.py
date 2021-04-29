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
    server = wsConfig['server']
    port = wsConfig['port']
    token = wsConfig['token']

    # Convert ExerciseInfo object to Dictionary
    for ex in exLst:
        wrkt = ex.to_psite_dict()
        wrktLst.append(wrkt)

    # wrktLst
    logger.debug(wrktLst)

    token = '+Wrh9wG5rXXAfh551ATvSkiJlbWTKQba'

    # Call webservice
    r = requests.post(server + ':' + port + '/api/workout', json=wrktLst, headers={'Authorization':'Bearer ' + token})
    logger.info(r)

    return r
    # return None
