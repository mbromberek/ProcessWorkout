# ProcessWorkout

Exercise data is exported in JSON format to iCloud using the app RunGap on my iPhone. This program reads the JSON file to get the details about an exercises (type, duration, distance, start time, end time, start and end GPS coordinates).

Stores the information about the exercise in Apple Numbers spreadsheet. The path is configurable.
Based on the day of the week the script predicts what category the exercise should be (long run, easy run, training) and the Gear being used (name of shoes used or bike used).  

### Technolgies
- Uses API calls to DarkSky gets the weather conditions for the start and end of the exercise.
- Uses AppleScript to update the Apple Numbers spreadsheet.
- Run_ProcessRunGap.applescript will setup the environment and run the Python script.


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


Had to run the install certificates in the install directory for Python to get the HTTPS connections to DarkSkies work
```
cd /Applications/Python\ 3.8/
./Install\ Certificates.command
```

Need to specify the path to the ProcessRunGap.py script in the `Run_ProcessRunGap.applescript script. ``

Create Virtual Environment and install libraries
```
mkvirtualenv ProcessWorkout
pip install -r requirements.txt
deactivate
workon ProcessWorkout #Activate ProcessWorkout Virtual Environment
workon #See all projects
```

# WorkoutAnalyze
Reads workout details of an exercise from the app RunGap.
The workout data is stored in two files *.rungap.json and *.metadata.json. The rungap file has the GPS locations and updates for the workout stats each second of the workout.
Both files store the data in JSON format.

The program WorkoutAnalyze can be run to process a specific file or the rungap/normWrkt function normalize_activity can be called passing it the rungap data to be normalized into a summary of the activity to export to a CSV or group by splits like mile or pauses.

## Arguments
```
WorkoutAnalyze.py -i <inputfile> -o <outputdir>
-i, --ifile arg  : Input filename to process
--idir arg       : Input directory with file name
-o, --odir arg   : Output directory for results
--osplit arg     : Segments to generate in file, default is all (CURRENTLY NOT SETUP)
                    options are mile, segment, kilometer, pause, all
```
