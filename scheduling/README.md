# ProcessWorkout Scheduling

Use Launch Agent plist file to schedule the job to run when a file is put in the monitored directory. 


### Manually load the launch agent
`launchctl load ~/Dropbox/code/python/ProcessWorkout/scheduling/local.mdb.ProcessWorkout.plist`

### See launch agents that are loaded
`launchctl list`

### Unload launch agent
`launchctl unload ~/Dropbox/code/python/ProcessWorkout/scheduling/local.mdb.ProcessWorkout.plist`

### To load agent on boot u put the plist file in this directory
`~/Library/LounchAgents`
