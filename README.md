# scrapy-canvas
## set-up
create a config.py file with:
- courses you are doing (in a list)
- directory path where you would like to save your files 
- url to the central timetable 
- url to timetable website to enter preferences
- url to canvas 
- username
- password 
- access token to canvas (optional). this can be obtained in account -> settings -> approved integrations -> new access token
run main.py and will automatically download files from canvas and edstem. if timetabling is required, run preferences.py and a timetable plot and time will be configured to have the least numbers of days you have class (lectures are excluded). 
