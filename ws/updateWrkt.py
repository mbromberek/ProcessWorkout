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
    '''
    Returns: dictionary
        result = webservice result
        wrktNotUpdtLst = workouts not found
        wrktUpdtLst = update results for workouts
    '''
    wrktLst = []
    wrktNotUpdtLst = []
    server = wsConfig['server']
    port = wsConfig['port']
    token = wsConfig['token']

    # Convert ExerciseInfo object to Dictionary
    for ex in exLst:
        wrkt = ex.to_psite_dict()
        wrkt_id = getWrktId(wrkt['wrkt_dttm'], wsConfig)
        if wrkt_id == None:
            logger.error('No match for workout date: ' + wrkt['wrkt_dttm'])
            wrktNotUpdtLst.append(wrkt)
        else:
            wrkt['id'] = wrkt_id
            wrktLst.append(wrkt)

    logger.debug(wrktLst)

    # Call webservice
    r = requests.put(server + ':' + port + '/api/workout', json=wrktLst, headers={'Authorization':'Bearer ' + token}, verify=wsConfig['verifyCert'] == 'Y')
    logger.info("Update Result: " + str(r))
    # logger.info(r.status_code)
    # logger.info(r.json())
    update_result = {'result':r, 'wrktNotUpdtLst': wrktNotUpdtLst, 'wrktUpdtLst': r.json()}

    return update_result
    # return None

def getWrktId(dttm_str, wsConfig):
    r = requests.get(wsConfig['server'] + ':' + wsConfig['port'] + '/api/workouts/' + dttm_str, headers={'Authorization':'Bearer ' + wsConfig['token']}, verify=wsConfig['verifyCert'] == 'Y')
    if r.status_code == 200:
        data = r.json()
        return data[0]['id']
    else:
        return None

def uploadFile(wrkt_id, ex, wsConfig, monitorDir):
    fileToUpload = ex.metadataFile.split('.')[0] + '.zip'
    fileToUploadPath = os.path.join(monitorDir,fileToUpload)
    logger.debug(fileToUploadPath)

    server = wsConfig['server']
    port = wsConfig['port']
    token = wsConfig['token']

    files = {'file': open(fileToUploadPath,'rb')}
    values = {'workout_id': wrkt_id}
    # r = requests.post(url, files=files, data=values)
    r = requests.put(server + ':' + port + '/api/generate_workout', headers={'Authorization':'Bearer ' + token}, verify=wsConfig['verifyCert'] == 'Y', files=files, data=values)

    if r.status_code == 400:
        logger.info('Error with uploadFile')
    if r.status_code == 401:
        logger.error('Unauthorized Access')

    return r
