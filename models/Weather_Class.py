'''
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
'''

class WeatherInfo:
    temp = -999
    apparentTemp = -999
    humidity = -999
    windSpeed = ''
    windGust = ''
    summary = ''

    lat = -999
    lon = -999
    time = ''


    def __init__(self):
        self.temp = -999

    def from_dict(self, data):
        self.temp = data['temp']
        self.apparentTemp = data['temp_feels_like']
        self.humidity = data['hmdty']
        self.windSpeed = data['wind_speed']
        self.windGust = data['wind_gust']
        self.summary = data['wethr_cond']
