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
        if 'temp' in data:
            self.temp = data['temp']
        if 'temp_feels_like' in data:
            self.apparentTemp = data['temp_feels_like']
        if 'hmdty' in data:
            self.humidity = data['hmdty']
        if 'wind_speed' in data:
            self.windSpeed = data['wind_speed']
        if 'wind_gust' in data:
            self.windGust = data['wind_gust']
        if 'wethr_cond' in data:
            self.summary = data['wethr_cond']
