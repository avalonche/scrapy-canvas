"""
Module to interact with the canvas api
"""
import os
import json
import requests
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime, timezone
from dateutil import tz
import dateutil.parser
import time
# need to put in type checks 
class Canvas:
    # logging into canvas website manually
    def __init__(self, url):
        self.url = url 
        self.access_token = None
        self.due_dates = None
    def weblogin(self, username, password):
        s = requests.Session()
        r = s.get(self.url+"/login")
        soup = BeautifulSoup(r.text, features="lxml")
        login_url = soup.find('form',{'id':'options'}).get("action")
        data = {
            'UserName': 'shared\\' + username,
            'Password': password,
            'AuthMethod': 'FormsAuthentication'
        }
        r = s.post(login_url, data=data)
        if not r.ok:
            print("Username/Password incorrect")
            return
        soup = BeautifulSoup(r.text, features="lxml")
        saml_url = soup.find('form').get('action')
        data = {
            'SAMLResponse': soup.find('input').get('value')
        }
        r = s.post(saml_url, data=data)
        config = open("config.py", 'r')
        if "access_token" not in config.readlines()[-1]:
            cookies = r.cookies.get_dict()
            auth_token = urllib.parse.unquote(cookies['_csrf_token'])
            token_url = self.url+"/profile/tokens"
            data = {
                'utf8':'',
                'authenticity_token':auth_token,
                'purpose': 'purpose',
                'access_token[purpose]': 'course_export',
                'expires_at': '',
                'access_token[expires_at]': '',
                '_method':'post'
            }
            r = s.post(token_url, data=data)
            token = json.loads(r.text)
            config = open("config.py", 'a')
            config.write("\naccess_token = \"%s\""%(token["visible_token"]))
            self.access_token = token["visible_token"]
            # retrieve access token   
        return s
    # logging into canvas through api and token
    def tokenlogin(self, access_token):
        self.access_token = access_token
    # get all courses student currently enrolled in and create a folder for it
    def __apirequest(self,api,features,params={}):
        page = 1
        data = []
        while page == 1 or r.text != '[]':
            headers = {'Authorization': 'Bearer ' + self.access_token}
            params["page"] = page
            params["per_page"] = 500
            r = requests.get(api, params=params, headers=headers)
            time.sleep(1)
            items = json.loads(r.text)
            for item in items:
                temp = {}
                for feature in features:
                    temp[feature] = item[feature]
                data.append(temp)
            page += 1
        return data
    def __writefile(self, r, dir_path, file_name):
        if r.ok:
            if "/" in file_name:
                file_name = "_".join(file_name).split("/")
            file_path = os.path.join(dir_path, file_name)
            if 'text/html' in r.headers['content-type']:
                print("Error writing file", file_name)
                return
            if not os.path.exists(file_path):
                with open(file_path, 'wb') as f:
                    f.write(r.content)
                print("Downloaded ", file_name)
    def __getcourses(self, dir_path, api_url):
        current_courses = []
        page = 1
        course_url = api_url + '/users/self/courses'
        features = ["term","name","id"]
        params = {"include":"term"}
        courses = self.__apirequest(course_url, features, params)
        for course in courses:
            if course["term"]["end_at"] != None:
                if dateutil.parser.parse(course["term"]["end_at"]) > datetime.now(timezone.utc):
                    unitcode = course["name"].split()[0]
                    course_id = course["id"]
                    # if "/" in name, replace with underscore, bad practice to name folders with forward slash
                    if "/" in unitcode:
                        unitcode = "_".join(unitcode.split("/"))
                    # create directory if it does not exist
                    course_path = os.path.join(dir_path, unitcode)
                    if not os.path.exists(course_path):
                        os.makedirs(course_path)
                    temp = {
                        "unitcode":unitcode,
                        "id": course_id
                        }
                    current_courses.append(temp)
        return current_courses
    # download assignments and create and download the folders in that specific course
    def __assignments(self, cur_course, dir_path, api_url):
        due_dates = [] # store due dates as dict list
        assignment_url = api_url + "/courses/%s/assignments"%(cur_course["id"])
        features = ["description","name","due_at","id"]
        assignments = self.__apirequest(assignment_url,features)
        for assignment in assignments:
            # if submitted then should not be on the due list
            due_date = {}
            if assignment["description"] != None:
                soup = BeautifulSoup(assignment["description"], features='lxml')
                file_links = soup.find_all("a", {"class":"instructure_file_link instructure_scribd_file"})
                if file_links != []:
                    # create assignment folder if not exist 
                    assignments_folder = dir_path + "/%s/Assignments"%(cur_course["unitcode"])
                    if not os.path.exists(assignments_folder):
                        os.makedirs(assignments_folder)
                    assignment_folder = os.path.join(assignments_folder, assignment["name"])
                    if not os.path.exists(assignment_folder):
                        # only add due date if the assignment has not been created before
                        os.makedirs(assignment_folder)
                        due_date["unitcode"] = cur_course["unitcode"]
                        due_date["name"] = assignment["name"]
                        if assignment["due_at"] != None:
                            date = dateutil.parser.parse(assignment["due_at"])
                            from_zone = tz.tzutc()
                            to_zone = tz.tzlocal()
                            if date > datetime.now(timezone.utc):
                                # explicitly state assignment is in utc
                                utc = date.replace(tzinfo=from_zone)
                                # convert to local time
                                local = date.astimezone(to_zone)
                                due_date["due_at"] = local
                                due_dates.append(due_date)
                    for link in file_links:
                        # some assignments had incorrect file names and could not be retrieved 
                        # have to go to the assignment to retrieve the correct link 
                        assignment_name = link.get("title")
                        file = requests.get(link.get("href"))
                        time.sleep(1)
                        self.__writefile(file, assignment_folder, assignment_name)
                        if not file.ok:
                            # file was deleted/could not be found, need to go into the assignment page 
                            assignment_api_link = assignment_url + "/" + str(assignment["id"])
                            headers = {'Authorization': 'Bearer ' + self.access_token}
                            r = requests.get(assignment_api_link, headers=headers)
                            assignment = json.loads(r.text)
                            soup = BeautifulSoup(assignment["description"], "lxml")
                            file_link = soup.find("a", {"title":assignment_name})
                            file = requests.get(file_link.get("href"))
                            time.sleep(1)
                            # try to write the file again
                            self.__writefile(file, assignment_folder, assignment_name)
                            if not file.ok:
                                # if still not ok, file can not be found, most likely deleted
                                print("Error: %s could not be downloaded"%(assignment["name"]))
                                print("The file has most probably been deleted")
        self.due_dates = due_dates
        # returns a list of due dates of assignments 
    # downloads all the modules, listed by the folder the instructor has placed
    # this is the place where all the course content is  
    def __getmodules(self, cur_course, dir_path, api_url):
        # if there are no modules, check ed
        course_folder = os.path.join(dir_path, cur_course["unitcode"])
        modules_url = api_url + "/courses/%s/modules"%(cur_course["id"])
        features = ["name","items","id"]
        params = {
            "include" : "items"
        }
        modules = self.__apirequest(modules_url,features, params)
        for module in modules:
            # if modules do not list all items, need to query the item api
            """items_url = module["items_url"]
            features = ["content_id", "url", "type", "title"]
            items = self.__apirequest(items_url, features)"""
            # create folders, but only make them if a file exists in a module
            module_folder = os.path.join(course_folder, module["name"])
            items = module["items"]
            for item in items:
                if "url" in item:
                    headers = {'Authorization': 'Bearer ' + self.access_token}
                    link = item["url"]
                    r = requests.get(link, headers=headers)
                    time.sleep(1)
                    if r.ok:
                        item_content = json.loads(r.text)
                        if item["type"] == "Page":
                            # make module folder, page folder, then write to file (if any)
                            page_folder = os.path.join(module_folder, item_content["title"])
                            content = item_content["body"]
                            if content != None:
                                soup = BeautifulSoup(content, "lxml")
                                file_links = soup.find_all("a", {"class":"instructure_file_link instructure_scribd_file"})
                                if file_links != []:
                                    if not os.path.exists(module_folder):
                                        os.makedirs(module_folder)
                                    if not os.path.exists(page_folder):
                                        os.makedirs(page_folder)
                                    for link in file_links:
                                        file_name = link.get("title")
                                        r = requests.get(link.get("href"))
                                        time.sleep(1)
                                        self.__writefile(r, page_folder, file_name)
                                        if not r.ok:
                                            print("Error: Could not download", link.get("title"))
                        if item["type"] == "File":
                            if not os.path.exists(module_folder):
                                os.makedirs(module_folder)
                            download_url = item_content["url"]
                            r = requests.get(download_url)
                            time.sleep(1)
                            self.__writefile(r, module_folder, item_content["filename"])
                            if not r.ok:
                                print("Error: Could not download ", item_content["filename"])
    # get all files in assignments and modules, folder sorted by each course
    # specify what directory user wants to save the files in 
    def downloadfiles(self, dir_name):
        api_url = self.url + '/api/v1'
        courses = self.__getcourses(dir_name, api_url)
        for course in courses:
            print("Generating files to ", course["unitcode"])
            print("Getting assignments to ", course["unitcode"])
            self.__assignments(course, dir_name, api_url)
            print("Getting modules to ", course["unitcode"])
            self.__getmodules(course, dir_name, api_url) 
        # if no assignments or modules, check check in ed (another api)