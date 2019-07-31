# api for edstem
import os 
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone
from dateutil import tz
import dateutil.parser
import time
class Edstem:
    # connect via canvas, or web, finally token 
    def __init__(self):
        self.token = None
        self.url = "https://edstem.org/api"
        self.due_dates = None
    def params(self):
        params = {
            '_token' : self.token
        }
        return params
    def weblogin(self, email, password):
        token_url = self.url + "/token"
        data = {
            "login" : email,
            "password" : password
        }
        r = requests.post(token_url, json=data)
        if r.ok:
            self.token = json.loads(r.text)
            return True
        return False
    def canvaslogin(self, course_id, canvasurl, accesstoken):
        api = canvasurl + "/api/v1/courses/%s/tabs"%(course_id)
        headers = {
            'Authorization': 'Bearer ' + accesstoken
            }
        r = requests.get(api, headers=headers)
        tabs = json.loads(r.text)
        for tab in tabs:
            if tab["label"] == "Ed":
                r = requests.get(tab["url"], headers=headers)
                ed = json.loads(r.text)
                r = requests.get(ed["url"])
                soup = BeautifulSoup(r.text, "lxml")
                ed_form = soup.find('form')
                ed_connect = ed_form.get('action')
                data = {}
                inputs = ed_form.find_all('input')
                for value in inputs:
                    key = value.get('name')
                    value = value.get('value')
                    data[key] = value
                r = requests.post(ed_connect, data=data)
                soup = BeautifulSoup(r.text, "lxml")
                link = soup.find('a').get('href')
                token = link.split('_token=')[1]
                self.token = token
    def tokenlogin(self, token):
        self.token = token
    def get_courses(self):
        cur_courses = []
        user = self.url + "/user"
        params = self.params()
        r = requests.get(user, params=params)
        time.sleep(1)
        info = json.loads(r.text)
        courses = info['courses']
        for course in courses:
            cur_course = {}
            course_info = course["course"]
            if course_info["status"] == "active" and course["role"]["role"] == "student":
                cur_course["id"] = course_info["id"]
                cur_course["features"] = course_info["features"]
                if "/" in course_info["code"]:
                    cur_course["unitcode"] = "".join(course_info["code"].split("/"))
                else:
                    cur_course["unitcode"] = course_info["code"]
                cur_courses.append(cur_course)
        return cur_courses
    def get_assignemtns(self):
        due_dates = []
        courses = self.get_courses()
        for course in courses:
            print("Getting due dates from ", course["unitcode"])
            if course["features"]["assessments"] == True:
                assessment_url = "%s/courses/%s/challenges"%(self.url, course["id"])
                params = {
                    'kind' : 'assessment',
                    '_token' : self.token
                }
                r = requests.get(assessment_url, params=params)
                time.sleep(1)
                assessments = json.loads(r.text)["challenges"]
                for assessment in assessments:
                    due_date = {}
                    if assessment["status"] != "completed":
                        due_date["title"] = assessment["title"] 
                        due_date["outline"] = assessment["outline"]
                        due_date["course_id"] = course["unitcode"]
                        if assessment["due_at"] != None:
                            date = dateutil.parser.parse(assessment["due_at"])
                            from_zone = tz.tzutc()
                            to_zone = tz.tzlocal()
                            if date > datetime.now(timezone.utc):
                                # explicitly state assessment is in utc
                                utc = date.replace(tzinfo=from_zone)
                                # convert to local time
                                local = date.astimezone(to_zone)
                                due_date["due_at"] = local
                                print(str(local))
                                due_dates.append(due_date)
                                continue
                        else:
                            due_date["due_at"] = assessment["due_at"]
                            due_dates.append(due_date)
            else:
                print("No assessments available on Ed")
        self.due_dates = due_dates
    def download_files(self, dir_path):
        courses = self.get_courses()
        for course in courses:
            print("Getting files from ", course["unitcode"])
            if course["features"]["resources"] == True:
                resource_url = "%s/courses/%s/resources"%(self.url, course["id"])
                r = requests.get(resource_url, self.params())
                time.sleep(1)
                info = json.loads(r.text)
                resources = info["resources"]
                for resource in resources:
                    category = resource["category"]
                    course_folder = os.path.join(dir_path, course["unitcode"])
                    if not os.path.exists(course_folder):
                        os.makedirs(course_folder)
                    category_folder = os.path.join(course_folder, category)
                    if not os.path.exists(category_folder):
                        os.makedirs(category_folder)
                    # no default file name, make sense from the tags in returned json
                    file_name = "%s - %s%s"%(resource["session"], resource["name"], resource["extension"])
                    if resource["session"] == "":
                        file_name = resource["name"] + resource["extension"]
                    if "/" in file_name:
                        file_name = "_".join(file_name.split("/"))
                    file_path = os.path.join(category_folder, file_name)
                    download_link = "%s/resources/%s/download"%(self.url, resource["id"])
                    r = requests.post(download_link, data=self.params())
                    time.sleep(1)
                    if r.ok and r.headers["Content-Length"] != "application/json":                           
                        if not os.path.exists(file_path):
                            with open(file_path, 'wb') as f:
                                f.write(r.content)
                            print("Downloaded: ", file_name)
                    else:
                        print("Error occured while downloading ", file_name)
            else:
                print("No files available on Ed")
    # if existing token does not work, probably was renewed or changed
    def renew_token(self):
        renew_url = self.url + "/renew_token"
        params = self.params()
        r = requests.post(renew_url, params=params)
        token = json.loads(r.text)["token"]
        self.token = token
        return token