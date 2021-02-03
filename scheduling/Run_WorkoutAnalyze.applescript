do shell script "
#!/bin/zsh

# Had to run this to set the variables for virtual environment
source ~/.zshrc

# Activate ProcessWorkout Virtual Environment. Could not get it to call workon function so had to use the activate command in the venv
source $WORKON_HOME/ProcessWorkout/bin/activate

# PROD
cd /Users/mikeyb/Dropbox/code/prod/ProcessWorkout
# TEST
# cd /Users/mikeyb/Dropbox/code/python/ProcessWorkout

python3 WorkoutAnalyze.py 

# Deactivate Virtual Environment
deactivate 

"

set nDir to "/Users/mikeyb/Library/Mobile Documents/com~apple~CloudDocs/_Runs/analyze/results/"
do shell script "open '/Users/mikeyb/Library/Mobile Documents/com~apple~CloudDocs/_Runs/analyze/results/'" 
