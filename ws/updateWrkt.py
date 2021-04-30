# First party classes
import os, sys
import logging
import logging.config

# Third party classes
import configparser
import requests

# Custom classes
from ExerciseInfo_Class import ExerciseInfo

def update(exLst, wsConfig):
    wrktLst = []
    server = wsConfig['server']
    port = wsConfig['port']
    token = wsConfig['token']

    # Convert ExerciseInfo object to Dictionary
    for ex in exLst:
        wrkt = ex.to_psite_dict()
        wrkt_id = getWrktId(wrkt['wrkt_dttm'], wsConfig)
        if wrkt_id == None:
            logger.error('No match for workout date: ' + wrkt['wrkt_dttm'])
        else:
            wrkt['id'] = wrkt_id
            wrktLst.append(wrkt)

    logger.debug(wrktLst)

    # Call webservice
    r = requests.put(server + ':' + port + '/api/workout', json=wrktLst, headers={'Authorization':'Bearer ' + token})
    # logger.info(r)

    return r
    # return None

def getWrktId(dttm_str, wsConfig):
    r = requests.get(wsConfig['server'] + ':' + wsConfig['port'] + '/api/workouts/' + dttm_str, headers={'Authorization':'Bearer ' + wsConfig['token']})
    if r.status_code == 200:
        data = r.json()
        return data[0]['id']
    else:
        return None
