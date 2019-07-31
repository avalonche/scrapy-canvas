"""
Fundctionalities: 
- Download all files find in the modules of each canvas course student is currently enrolled
- Download all assignments found of canvas course student currently enrolled
- Download all assignments and files found in EdStem student currently enrolled
"""
import os
import config
import canvas
import edstem
if "main" == __name__:
    # downloading everything in canvas first 
    canvas_sync = canvas.Canvas(config.canvas_url)
    ed_sync = edstem.Edstem()
    try:
        dir_path = config.dir_path
    except AttributeError:
        print("Directory not specified")
        return
    try:
        access_token = config.access_token
    except AttributeError:
        print("Access token not found, please login using your username and password")
        try:
            username = config.username
            password = config.password
        except AttributeError:
            print("Username/Password not found, please input in config.py")
            return
        canvas_sync.weblogin(username, password)
    print("Downloading from Canvas...")
    canvas_sync.download_files(dir_path)
    email = username + "@uni.sydney.edu.au"
    ed_sync.weblogin(email, password)
    print("Downloading from EdStem...")
    ed_sync.download_files(dir_path)
    # sync the due date with the week that it's supposed to be due
    canvas_due_dates = canvas_sync.due_dates
    ed_due_dates = ed_sync.due_dates