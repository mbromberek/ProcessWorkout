property docName : ""
property p2Cloud : (path to library folder from user domain as text) & "Mobile Documents:com~apple~"
property DATE_COL : 1
property TYPE_COL : 2
property DUR_COL : 3
property DIST_COL : 4
property PACE_COL : 5
property NOTES_COL : 6
property CATEGORY_COL : 7
property GEAR_COL : 8
property ELEVATION_COL : 9
property HR_COL : 10
property CAL_COL : 11

on addExercise(eDate, eType, eTime, eDistance, eDistanceUnit, eHeartRate, eCal, eNotes, eStartTime, eGear, eCategory, eElevation)
	set exerciseDateOrder to "desc"
	tell application "Numbers"
		activate
		set theApp to its name
		set docNamePath to p2Cloud & theApp & ":Documents:" & docName
		open file (docNamePath)
		tell document docName
			tell sheet "Exercise"
				tell table "Exercise"
					set rowCt to row count
					set firstRow to header row count + 1
					set lastRow to rowCt - footer row count
					set updateRow to -1
					
					if exerciseDateOrder = "desc" then
						add row above row firstRow
					end if
					
					repeat with i from firstRow to lastRow
						set dateVal to value of cell 1 of row i
						log (dateVal)
						if (dateVal = missing value) then
							set updateRow to i
							exit repeat
						end if
					end repeat
					--Add data to this row
					if (updateRow = -1) then
						add row below row lastRow
						set updateRow to lastRow + 1
					end if
					tell row updateRow
						set eDateTime to eDate & " " & eStartTime
						set value of cell DATE_COL to eDateTime
						set value of cell TYPE_COL to eType
						set value of cell DUR_COL to eTime
						set value of cell DIST_COL to eDistance
						set value of cell HR_COL to eHeartRate
						set value of cell CAL_COL to eCal
						set value of cell NOTES_COL to eNotes
						set value of cell GEAR_COL to eGear
						set value of cell CATEGORY_COL to eCategory
						set value of cell ELEVATION_COL to eElevation
					end tell
				end tell
			end tell
			
			save
		end tell
	end tell
end addExercise

(* readLastExercise
Reads the last exercise of type eType in the spreadsheet that is not a blank line
and returns the date for that row
Determines if it should look from the top or bottom of the list based on the 
sort order passed in exerciseDateOrder
*)
on readLastExercise(eType, exerciseDateOrder)
	--set exerciseDateOrder to "desc"
	tell application "Numbers"
		activate
		set theApp to its name
		set docNamePath to p2Cloud & theApp & ":Documents:" & docName
		open file (docNamePath)
		tell document docName
			tell sheet "Exercise"
				tell table "Exercise"
					set rowCt to row count
					set firstRow to header row count + 1
					set lastRow to rowCt - footer row count
					set updateRow to -1
					set lastDate to current date
					
					if exerciseDateOrder = "asc" then
						set startRow to lastRow
						set endRow to firstRow
						set incrementVal to -1
					else
						set startRow to firstRow
						set endRow to lastRow
						set incrementVal to 1
					end if
					
					--repeat with i from lastRow to firstRow by -1
					repeat with i from startRow to endRow by incrementVal
						set dateVal to value of cell 1 of row i
						set exerciseType to value of cell 2 of row i
						if (dateVal is not missing value and eType = exerciseType) then
							set updateRow to i
							set lastDate to dateVal
							exit repeat
						end if
					end repeat
					log ("Last Exercise date: " & lastDate & " on row : " & updateRow)
				end tell
			end tell
		end tell
	end tell
	return lastDate
end readLastExercise

on updateExercise(eRow, eDate, eType, eTime, eDistance, eDistanceUnit, eHeartRate, eCal, eNotes, eGear)
	tell application "Numbers"
		activate
		set theApp to its name
		set docNamePath to p2Cloud & theApp & ":Documents:" & docName
		open file (docNamePath)
		tell document docName
			tell sheet "Exercise"
				tell table "Exercise"
					tell row eRow
						set value of cell DATE_COL to eDate
						set value of cell TYPE_COL to eType
						set value of cell DUR_COL to eTime
						set value of cell DIST_COL to eDistance
						set value of cell HR_COL to eHeartRate
						set value of cell CAL_COL to eCal
						set value of cell NOTES_COL to eNotes
						set value of cell GEAR_COL to eGear
					end tell
				end tell
			end tell
			save
		end tell
	end tell
end updateExercise

on getExercises(numRowsToReturn)
	set exerciseDateOrder to "desc"
	tell application "Numbers"
		activate
		set theApp to its name
		set docNamePath to p2Cloud & theApp & ":Documents:" & docName
		open file (docNamePath)
		tell document docName
			tell sheet "Exercise"
				tell table "Exercise"
					set rowCt to row count
					set firstRow to header row count + 1
					set lastRow to rowCt - footer row count
					set updateRow to -1
					
					if exerciseDateOrder = "desc" then
						set lastRowToPull to firstRow + (numRowsToReturn as number)
						if lastRow > lastRowToPull then
							set lastRow to lastRowToPull
						end if
					else
						set lastRowToPull to lastRow - (numRowsToReturn as number)
						if firstRow > lastRowToPull then
							set firstRow to lastRowToPull
						end if
						
					end if
					
					set exerciseLst to {}
					
					repeat with i from firstRow to lastRow
						set dateVal to my chkMissingVal(value of cell DATE_COL of row i)
						set typeVal to my chkMissingVal(value of cell TYPE_COL of row i)
						set durVal to my chkMissingVal(value of cell DUR_COL of row i)
						set distVal to my chkMissingVal(value of cell DIST_COL of row i)
						set paceVal to my chkMissingVal(value of cell PACE_COL of row i)
						set hrVal to my chkMissingVal(value of cell HR_COL of row i)
						set calVal to my chkMissingVal(value of cell CAL_COL of row i)
						set noteVal to my chkMissingVal(value of cell NOTES_COL of row i)
						set gearVal to my chkMissingVal(value of cell GEAR_COL of row i)
						set catVal to my chkMissingVal(value of cell CATEGORY_COL of row i)
						
						set exerciseVal to {rowVal:i, dateVal:dateVal, typeVal:typeVal, durationVal:durVal, distanseVal:distVal, hrVal:hrVal, caloriesVal:calVal, noteVal:noteVal, gearVal:gearVal, catVal:catVal, paceVal:paceVal}
						log (exerciseVal)
						set exerciseLst to exerciseLst & {exerciseVal}
						(*if (dateVal = missing value) then
							set updateRow to i
							exit repeat
						end if*)
					end repeat
				end tell
			end tell
		end tell
	end tell
	log ("END")
	log (count of exerciseLst)
	(*repeat with theItem in exerciseLst
		log (theItem)
	end repeat*)
	return exerciseLst
end getExercises

on chkMissingVal(val)
	if val is missing value then
		return ""
	else
		return val
	end if
end chkMissingVal

on initialize(documentName)
	set docName to documentName
end initialize

on closeSheet()
	tell application "Numbers"
		tell document docName
			close
		end tell
	end tell
end closeSheet

on generateWrktTable(sheetNm, tblNm, wrktData, wrktSumFrmla)
	set columnCt to 4
	set hdrRowCt to 1
	set wrktRowCt to (count of wrktData)
	set tblRowCt to (wrktRowCt + 5)
	
	set {hours:h, minutes:m, seconds:s, time:t} to (current date)
	set tm_str to (h as string) & (m as number) & s
	
	tell application "Numbers"
		activate
		tell document docName
			tell sheet sheetNm
				if (exists table tblNm) then set tblNm to tblNm & "_" & tm_str
				log ("Table Name: " & tblNm)
				
				set thisTable to make new table with properties {name:tblNm, column count:columnCt, row count:tblRowCt, header row count:hdrRowCt, header column count:1, footer row count:4}
				
				tell thisTable
					tell row 1
						set value of cell 1 to "Interval"
						set value of cell 2 to "Time"
						set value of cell 3 to "Distance"
						set value of cell 4 to "Pace"
					end tell
					
					set rowNbr to 2
					repeat with theRecord in wrktData
						tell row rowNbr
							set value of cell 1 to (interval of theRecord)
							set value of cell 2 to (dur_str of theRecord)
							set value of cell 3 to (dist_mi of theRecord)
							set value of cell 4 to (pace_str of theRecord)
						end tell
						set rowNbr to rowNbr + 1
					end repeat
					
					
					--Add summary for Total workout
					tell row (wrktRowCt + hdrRowCt + 1)
						set value of cell 1 to "Total"
						--set sumWrktDistFormula to "=sum(B:B)"
						set value of cell 2 to (dist_mi of (wrkt_tot of wrktSumFrmla))
						set value of cell 3 to (dur_str of (wrkt_tot of wrktSumFrmla))
						set value of cell 4 to "=" & name of cell 2 & "/" & name of cell 3
					end tell
					
					--Add summary for workout without warm up and cooldown
					tell row (wrktRowCt + hdrRowCt + 2)
						set value of cell 1 to "Workout"
						set value of cell 2 to (dist_mi of (intvl_tot of wrktSumFrmla))
						set value of cell 3 to (dur_str of (intvl_tot of wrktSumFrmla))
						set value of cell 4 to "=" & name of cell 2 & "/" & name of cell 3
					end tell
					
					--Add summary of first half of workout
					tell row (wrktRowCt + hdrRowCt + 3)
						set value of cell 1 to "First Half"
						set value of cell 2 to (dist_mi of (frst_half of wrktSumFrmla))
						set value of cell 3 to (dur_str of (frst_half of wrktSumFrmla))
						set value of cell 4 to "=" & name of cell 2 & "/" & name of cell 3
					end tell
					
					--Add summary of second half of workout
					tell row (wrktRowCt + hdrRowCt + 4)
						set value of cell 1 to "Second Half"
						set value of cell 2 to (dist_mi of (scnd_half of wrktSumFrmla))
						set value of cell 3 to (dur_str of (scnd_half of wrktSumFrmla))
						set value of cell 4 to "=" & name of cell 2 & "/" & name of cell 3
					end tell
				end tell
				
			end tell
		end tell
	end tell
	
end generateWrktTable

set docName to "Exercise 2017 test.numbers"
set wrktData to {{interval:0, dur_str:"0h 5m 1s", dist_mi:0.65, pace_str:"0h 7m 45s"}, {interval:1, dur_str:"0h 17m 47s", dist_mi:2.37, pace_str:"0h 7m 30s"}, {interval:2, dur_str:"0h 16m 27s", dist_mi:2.29, pace_str:"0h 7m 11s"}, {interval:3, dur_str:"0h 5m 53s", dist_mi:0.7, pace_str:"0h 8m 27s"}}
set wrktFrmla to {wrkt_tot:{distance:"=sum(B:B)", dur_str:"=sum(C:C)"}}
my generateWrktTable("2020-Fall Training", "Tempo 2020-11-24", wrktData, wrktFrmla)


--my addExercise("06/03/2016", "Running", "0h 30m 31s", "4.01", "MI", "161", "111", "Run felt good", "4:00 PM", "")
--my initialize("Exercise 2017 test.numbers")
--my readLastExercise("Running", "desc")

--my getExercises(1)
