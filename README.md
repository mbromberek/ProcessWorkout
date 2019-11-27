# ProcessWorkout

Exercise data is exported in JSON format to Dropbox using the app RunGap on my iPhone. This program reads the JSON file to get the details about an exercies (type, duration, distance, start time, end time, start and end GPS coordinates).

Stores the information about the exercise in Apple Numbers spreadsheet. The path is configurable. 
Based on the day of the week the script predicts what category the exercise should be (long run, easy run, training) and the Gear being used (name of shoes used or bike used).  

### Technolgies
- Uses API calls to DarkSky gets the weather conditions for the start and end of the exercise.
- Uses AppleScript to update the Apple Numbers spreadsheet.


### Details saved in sheet
- Date and time of start of run
- Type of Exercise
- Time/Duration
- Distance in miles
- Minutes per Mile
- Notes - Contains the start and end weather conditions
- Category
- Gear (name of shoes or bike used)
- Elevation in feet
- Heart Rate
- Calories

### Setup Environment

'''
Had to run the install certificates in the install directory for Pything to get the HTTPS connections to work
cd /Applications/Python\ 3.6/
TurnA:/Applications/Python 3.6 mikeyb$ ./Install\ Certificates.command 
'''


% mkvirtualenv ProcessWorkout

