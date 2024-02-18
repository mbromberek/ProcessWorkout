# First party classes
import os, sys
import logging
import logging.config
from datetime import datetime

# Third party classes
import configparser
import requests

# Custom classes
from ExerciseInfo_Class import ExerciseInfo

def get_wrkt(dttm, wsConfig):
    logger.info('get_wrkt: ' + str(dttm))
    dateApiFormat = '%Y-%m-%d'
    dt_str = datetime.strftime(dttm, dateApiFormat)
    r = requests.get(wsConfig['server'] + ':' + wsConfig['port'] + '/api/workouts/?' + \
        'strt_dt=' + dt_str+ \
        '&type=endurance', \
        headers={'Authorization':'Bearer ' + wsConfig['token']}, \
        verify=wsConfig['verifyCert'] == 'Y')
    if r.status_code == 200:
        data = r.json()
        return data
    else:
        return None
