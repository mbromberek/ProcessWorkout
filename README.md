# ProcessWorkout

Exercise data is exported in JSON format to Dropbox using the app RunGap on my iPhone. This program reads the JSON file to get the details about an exercies (type, duration, distance, start time, end time, start and end GPS coordinates).

Stores the information about the exercise in Apple Numbers spreadsheet. The path is configurable. 
Based on the day of the week the script predicts what category the exercise should be (long run, easy run, training) and the Gear being used (name of shoes used or bike used).  

### Technolgies
- Uses API calls to DarkSky gets the weather conditions for the start and end of the exercise.
- Uses AppleScript to update the Apple Numbers spreadsheet.
- Run_ProcessRunGap.applescript will setup the environment and run run the Python script. 


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


Had to run the install certificates in the install directory for Pything to get the HTTPS connections to DarkSkies work
```
cd /Applications/Python\ 3.8/
./Install\ Certificates.command
```

Need to specify the path to the ProcessRunGap.py script in the `Run_ProcessRunGap.applescript script. ``

Create Virtual Environment and install libraries
```
mkvirtualenv ProcessWorkout
pip install -r requirements.txt
```

