#! /Users/mikeyb/Applications/python3
# -*- coding: utf-8 -*-


import zipfile
import json
import os,glob,shutil
import re
import datetime
import math
import applescript
import configparser


#For API call
import requests

# Add to sys.path the directory with custom classes
import sys
sys.path.insert(1, 'models')
# Import customer classes that are in models directory
from ExerciseInfo_Class import ExerciseInfo
from Weather_Class import WeatherInfo


config = configparser.ConfigParser()

def breakTimeFromSeconds(totTimeSec):
	hourTot = math.floor(totTimeSec/60/60)
	minTot = math.floor((totTimeSec/60/60 - hourTot) * 60)
	secTot = math.floor(((totTimeSec/60/60 - hourTot) * 60 - minTot) *60)
	return hourTot, minTot, secTot
def formatNumbersTime(h, m, s):
	durTotNumbers = str(h) + 'h ' + str(m) + 'm ' + str(s) + 's'
	return durTotNumbers
def formatSheetsTime(h, m, s):
	durTotSheets = str(h) + ':' + str(m) + ':' + str(s)
	return durTotSheets


#######################################################
# get full directory path for files in passed directory
#######################################################
def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]


#######################################################
# determineGear(exercise details)
#######################################################
def determineGear(ex):
	gearConfigs = config['gear']
	gear = ''
	try:
		if ex.type == 'Running':
			primaryDays = config['running']['primary_days'].split(',')
			if ex.startTime.strftime('%A') in primaryDays:
				gear = appleScriptName = gearConfigs['default_shoe_primary']
			else:
				gear = appleScriptName = gearConfigs['default_shoe_secondary']
		else:
			gear = gearConfigs['default_' + ex.type]
	except:
		gear = ''
	
	return gear

#######################################################
# API call
#######################################################
def apiCall(url):
	r = requests.get(url)
	data = r.json()
	return data


#######################################################
# Get Weather from dark sky for the passed latitude,
# longitude, and time. 
# Creates a weather object with returned data and returns
# it. 
#######################################################
def getWeather(lat, lon, tm):
	darkSkyBaseURL = config['dark_sky']['base_url']
	darkSkyKey = config['dark_sky']['key']
	
	darkSkyUrl = darkSkyBaseURL + darkSkyKey + '/' + str(lat) + ',' + str(lon) + ',' + tm.strftime('%Y-%m-%dT%H:%M:%S')
	
	w = WeatherInfo()
				
	weatherData = apiCall(darkSkyUrl)
	w.temp = weatherData['currently']['temperature']
	w.apparentTemp = weatherData['currently']['apparentTemperature']
	w.humidity = weatherData['currently']['humidity']
	
	return w


#######################################################
# MAIN
#######################################################
def main():
	# Get config details
	progDir = os.path.dirname(os.path.abspath(__file__))	
# 	config = configparser.ConfigParser()
	config.read(progDir + "/config.txt")
	
	pathToAppleScript = config['applescript']['script_path']
	appleScriptName = config['applescript']['sheet_name']

	runGapConfigs = config['rungap']
	monitorDir = runGapConfigs['monitor_dir']
	print('monitorDir:' + monitorDir)
	tempDir = runGapConfigs['temp_dir']
	print('tempDir: ' + tempDir)
# 	dateTimeSheetFormat = runGapConfigs['date_time_sheet_format']
	dateTimeSheetFormat = '%m/%d/%Y %H:%M:%S'

	compressFileRegex = re.compile(r'(.zip|.gz)$')
	jsonFileRegex = re.compile(r'(metadata.json)$')
	jsonExtRegex = re.compile(r'(.json)$')

	# ) Read applescript file for reading and updating exercise spreadseeht
# 	scptFile = open(pathToAppleScript + 'AddExercise.txt')
	scptFile = open('./' + 'AddExercise.txt')
	scptTxt = scptFile.read()
	scpt = applescript.AppleScript(scptTxt)
	scpt.call('initialize',appleScriptName)

	print(os.listdir(monitorDir))
	zipFiles = [] 
	# Uncompress files from monitor directory into temp directory
	for filename in os.listdir(monitorDir):
		# Checks if compressed file
		if compressFileRegex.search(filename):
			z = zipfile.ZipFile(monitorDir + filename,mode='r')
			z.extractall(path=tempDir)
			zipFiles.append(monitorDir + filename)

	exLst = []
	# Loop through files and load exercise data to a list
	print(listdir_fullpath(tempDir))
	filesToProcess = []
	print(filesToProcess)
	for filename in listdir_fullpath(tempDir):
		if (os.path.isfile(filename) == False and filename != '__MACOSX'):
			print('directory')
			filesToProcess.extend(listdir_fullpath(filename))
		else:
			print('file')
			filesToProcess.append(filename)

	print(filesToProcess)	
	for filename in filesToProcess:		
		print(filename)
		if jsonFileRegex.search(filename):
			print('\nProcess ' + filename)
			ex = ExerciseInfo()
			ex.type = 'Running'
			with open(filename) as data_file:
				data = json.load(data_file)
				ex.source = data['source']
				ex.originLoc = filename
				
				ex.type = data['activityType']['sourceName']
			
				# Get the start time from file in UTC
				d = datetime.datetime.strptime(data['startTime']['time'],'%Y-%m-%dT%H:%M:%SZ')
				# Convert start time to current time zone
				sTime = d.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
				ex.startTime = sTime
	
				MILES_IN_KILOMETERS = 0.621371
				METERS_IN_KILOMETERS = 1000
	
				eDistanceTotMeters = data['distance']
				ex.distTot = eDistanceTotMeters / METERS_IN_KILOMETERS * MILES_IN_KILOMETERS

				ex.hourTot, ex.minTot, ex.secTot = breakTimeFromSeconds(data['duration'])
				durTotNumbers = formatNumbersTime(ex.hourTot, ex.minTot, ex.secTot)
				durTotSheets = formatSheetsTime(ex.hourTot, ex.minTot, ex.secTot)
			
				ex.durTot = durTotSheets	
			
				ex.avgHeartRate = data['avgHeartrate']
	
				ex.calTot = data['calories']
				
				if 'elevationGain' in data:
					ex.elevationGain = data['elevationGain']
					ex.elevationLoss = data['elevationLoss']
				
				if ex.gear == '':
					ex.gear = determineGear(ex)
				
				categoryConfigs = ''
				if ex.type == 'Running':
					categoryConfigs = config['run_category']
					# Get day of the exercise
					if ex.startTime.strftime('%A') in categoryConfigs:
						ex.category = categoryConfigs[ex.startTime.strftime('%A')]
				else:
					ex.category = 'Easy'
				
				# Pull data for getting weather
				laps = data['laps']
				if 'displayPath' in data:
					exPath = data['displayPath']

					lastLapStart = datetime.datetime.strptime(laps[-1]['startTime'] ,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
					lastLapDuration = laps[-1]['duration']
					lastLapEnd = lastLapStart + datetime.timedelta(seconds=lastLapDuration)
					ex.endTime = lastLapEnd

					# Get lat and long from path details				
					ex.startLat = exPath[0]['lat']
					ex.startLon = exPath[0]['lon']				
					ex.endLat = exPath[-1]['lat']
					ex.endLon = exPath[-1]['lon']
				
					# Get lat and long from start and end of first and last miles, does not work if using Segments in run
	# 				ex.startLat = laps[0]['startLocation']['lat']
	# 				ex.startLon = laps[0]['startLocation']['lon']				
	# 				ex.endLat = laps[-1]['endLocation']['lat']
	# 				ex.endLon = laps[-1]['endLocation']['lon']
				
					ex.startWeather = getWeather(ex.startLat, ex.startLon, ex.startTime)
					ex.endWeather = getWeather(ex.endLat, ex.endLon, ex.endTime)
				
					ex.userNotes = 'Start: {0:.{1}f}'.format(ex.startWeather.temp,0) + ' degrees ' + '{0:.{1}f}'.format(ex.startWeather.humidity*100,0) + ' percent humidity feels like ' + '{0:.{1}f}'.format(ex.startWeather.apparentTemp,0) + ' degrees. '
					ex.userNotes = ex.userNotes + 'End: {0:.{1}f}'.format(ex.endWeather.temp,0) + ' degrees ' + '{0:.{1}f}'.format(ex.endWeather.humidity*100,0) + ' percent humidity feels like ' + '{0:.{1}f}'.format(ex.startWeather.apparentTemp,0) + ' degrees.\n'
				
				if (runGapConfigs['print_data'] == 'Y'):
# 					print("Start Date Time: " + 
# 						ex.startTime.strftime('%Y-%m-%d %H:%M:%S %Z'))
					print("Start Date Time: " + 
						ex.startTime.strftime('%Y-%m-%dT%H:%M:%S'))
					print("Start Unix Time: " + str(ex.startTime.timestamp()))
					if ex.endTime == '':
						print("End Date Time: Unknown")
					else:
						print('End Date Time: ' + 
							ex.endTime.strftime('%Y-%m-%dT%H:%M:%S'))
					
					print("Distance: " + str(ex.distTot))
					print("Duration: " + ex.durTot)
					print('Avg Heartrate: ' + str(ex.avgHeartRate))
					print('Calories Burned: ' + str(ex.calTot))
					print('Category: ' + ex.category)

					print('Start Lat, Lon: ' + str(ex.startLat) + ',' + str(ex.startLon) )
					print('End Lat, Lon: ' + str(ex.endLat) + ',' + str(ex.endLon) )
# 					print(darkSkyUrlStart)
# 					print(darkSkyUrlEnd)

				exLst.append(ex)

	# Save Exercise to spreadsheet then remove files
	for ex in exLst:
		startDateTime = ex.startTime.strftime(dateTimeSheetFormat)
		distance = "%.2f" % ex.distTot
		duration = formatNumbersTime(ex.hourTot, ex.minTot, ex.secTot)
		scpt.call('addExercise',ex.eDate, ex.type, duration, distance, ex.distUnit, ex.avgHeartRate, ex.calTot, ex.userNotes, startDateTime, ex.gear, ex.category, ex.elevationChange())

		# Remove files from temp folder then monitor folder
		fileNameChunks = ex.originLoc.split('.')
		fileNameStart = fileNameChunks[0]
		for fl in glob.glob(fileNameStart + '*'):
			os.remove(fl)
		for filename in listdir_fullpath(tempDir):
			if (os.path.isfile(filename) == False):
				shutil.rmtree(filename)
			else:
				os.remove(filename)

		if (runGapConfigs['backup_files'] == 'Y'):
			for fl in glob.glob(monitorDir + fileNameStart + '*'):
				shutil.copy(fl, runGapConfigs['backup_dir'])
		if (runGapConfigs['remove_files'] == 'Y'):
			for fl in glob.glob(monitorDir + fileNameStart + '*'):
				os.remove(fl)

	if (config['applescript']['close_sheet'] == 'Y'):
		scpt.call('closeSheet')
	
if __name__ == '__main__':
	main()

