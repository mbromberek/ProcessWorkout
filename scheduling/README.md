# ProcessWorkout Scheduling

Use Launch Agent plist file to schedule the job to run when a file is put in the monitored directory. 
- The plist runs the script Run_ProcessRunGap.zsh as a bash script since Mojave does not seem to be able to run a zsh script from launchd. 
- Script Run_ProcessRunGap.zsh runs the applescript file Run_ProcessRunGap.app. This is done to try and get Catalina to use the .app program for permissions but currently that is not working. And I cannot get launchd to automatically run the .app program either. So not sure if it is needed. 
- Run_ProcessRunGap.app then sets up the zsh environment and runs ProcessRunGap.py to actually process the workout file and update the Exercise spreadsheet. 


### Manually load the launch agent
`launchctl load ~/Dropbox/code/python/ProcessWorkout/scheduling/local.mdb.ProcessWorkout.plist`

### See launch agents that are loaded
`launchctl list`

### Unload launch agent
`launchctl unload ~/Dropbox/code/python/ProcessWorkout/scheduling/local.mdb.ProcessWorkout.plist`

### Manually run the Agent
`launchctl start local.mdb.ProcessWorkout`

### To load agent on boot u put the plist file in this directory
`~/Library/LaunchAgents`

#### Aliases to make loading and unloading easier since I got tired of using history to get to these
`alias load='launchctl load /Users/mikeyb/Dropbox/code/python/ProcessWorkout/scheduling/local.mdb.ProcessWorkout.plist'`

`alias unload='launchctl unload /Users/mikeyb/Dropbox/code/python/ProcessWorkout/scheduling/local.mdb.ProcessWorkout.plist'`

`alias list='launchctl list | grep local'`
