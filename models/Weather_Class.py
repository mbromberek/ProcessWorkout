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


    # def __init__(self):
    #     self.temp = -999

    def from_dict(self, data):
        if 'temp' in data and data['temp'] != 'None':
            self.temp = float(data['temp'])
        if 'temp_feels_like' in data and data['temp_feels_like'] != 'None':
            self.apparentTemp = float(data['temp_feels_like'])
        if 'hmdty' in data and data['hmdty'] != 'None':
            self.humidity = float(data['hmdty'])
        if 'wind_speed' in data and data['wind_speed'] != 'None':
            self.windSpeed = float(data['wind_speed'])
        if 'wind_gust' in data and data['wind_gust'] != 'None':
            self.windGust = float(data['wind_gust'])
        if 'wethr_cond' in data and data['wethr_cond'] != None:
            self.summary = data['wethr_cond']
        if 'dew_point' in data and data['dew_point'] != 'None':
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
        if self.temp != -999:
            txtLst.append(': {0:.{1}f}'.format(self.temp,0))
            txtLst.append(' degrees ')
        if self.summary != '':
            txtLst.append(self.summary)
        if self.humidity != -999:
            txtLst.append(', ')
            txtLst.append('{0:.{1}f}'.format(self.humidity,0))
            txtLst.append(' percent humidity')
        if self.windSpeed != '':
            txtLst.append(', wind speed ')
            txtLst.append('{0:.{1}f} mph'.format(self.windSpeed,2))
        if self.windGust != '':
            txtLst.append(', wind gust ')
            txtLst.append('{0:.{1}f} mph'.format(self.windGust,2))
        if self.apparentTemp != -999:
            txtLst.append(', feels like ')
            txtLst.append('{0:.{1}f}'.format(self.apparentTemp,0))
            txtLst.append(' degrees. ')
        txtLst.append('\n')
        return ''.join(txtLst)
