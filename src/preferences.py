"""
Entering timetable preferences. 
"""
import calendar
import scheduler
import config
calendar = calendar.Calendar(courses)
calendar.login()
data = calendar.get_course_calendar()
schedule = scheduler.Scheduler(data)
timetable = schedule.generate_timetable()
schedule.plot_timetable()
