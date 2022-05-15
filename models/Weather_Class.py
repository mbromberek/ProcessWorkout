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
    dewPoint = ''
    position = ''


    def __init__(self):
        self.temp = -999

    def from_dict(self, data):
        if 'temp' in data:
            self.temp = float(data['temp'])
        if 'temp_feels_like' in data:
            self.apparentTemp = float(data['temp_feels_like'])
        if 'hmdty' in data:
            self.humidity = float(data['hmdty'])
        if 'wind_speed' in data:
            self.windSpeed = float(data['wind_speed'])
        if 'wind_gust' in data:
            self.windGust = float(data['wind_gust'])
        if 'wethr_cond' in data:
            self.summary = data['wethr_cond']
        if 'dew_point' in data:
            self.dewPoint = float(data['dew_point'])

    def generateWeatherUserNotes(self, position=''):
        """
        Generates notes for User Notes field of Exercise spreadsheet.
        Puts all the text into an array that is joined into the returned string.
        """

        txtLst = []
        if position != '':
            txtLst.append(position)
        elif self.position != '':
            txtLst.append(self.position)
        txtLst.append(': {0:.{1}f}'.format(self.temp,0))
        txtLst.append(' degrees ')
        txtLst.append(self.summary)
        txtLst.append(', ')
        txtLst.append('{0:.{1}f}'.format(self.humidity,0))
        txtLst.append(' percent humidity, wind speed ')
        txtLst.append('{0:.{1}f}'.format(self.windSpeed,2))
        txtLst.append(' mph, wind gust ')
        txtLst.append('{0:.{1}f}'.format(self.windGust,2))
        txtLst.append('mph, feels like ')
        txtLst.append('{0:.{1}f}'.format(self.apparentTemp,0))
        txtLst.append(' degrees. ')
        txtLst.append('\n')
        return ''.join(txtLst)
