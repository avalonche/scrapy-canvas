import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import re
class Calendar:
    def __init__(self, unitcodes, certificate='Certificates.cer'):
        self.url = "https://web.timetable.usyd.edu.au"
        self.certificate = certificate
        self.unitcodes = unitcodes
        self.session = None
    def login(self, username, password):
        timetable_url = self.url
        s = requests.session()
        r = s.get(timetable_url, verify=self.certificate)
        soup = BeautifulSoup(r.text, features="lxml")
        form = soup.find("form", {"name" : "loginForm"})
        data = {}
        for input in soup.find_all("input"):
            data[input.get("name")] =  input.get("value")
        data["credential_0"] = username
        data["credential_1"] = password
        r = s.post(r.url, data=data, verify=self.certificate)
        self.session = s
    def get_calendar(self):
        calender_link = self.url + '/calendar.jsp'
        r = self.session.get(calender_link, verify=self.certificate)
        soup = BeautifulSoup(r.text, features="lxml")
        # finding tags with the month
        expression = '(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)\s+\d{4}'
        table_tag = soup.find_all('th', text=re.compile(r'%s'%(expression)))
        tables = []
        calendar = {}
        for table in table_tag:
            table = table.parent.parent
            # only include month if it is during the semester 
            if table.find('td', {'class' : 'cal week'}, text=re.compile(r'^[0-9]+$')):
                tables.append(table)
        for table in tables:
            date_range = []
            sections = table.find_all('tr')
            month, year = sections[0].text.split()[0], sections[0].text.split()[1]
            for i in range(2, len(sections)):
                if sections[i].find('td', {'class' : 'cal week'}, text=re.compile(r'^[0-9]+$')):
                    dates = sections[i].find_all('td', {'class':re.compile(r'(?!\bholiday)')})
                    week = "Week " + dates[0].text
                    startday = dates[1].text
                    endday = dates[-1].text
                    starts = startday + month + year
                    ends = endday + month + year
                    startdate = datetime.strptime(starts, '%d%B%Y')
                    enddate = datetime.strptime(ends, '%d%B%Y')
                    enddate += timedelta(days=1)
                    if week in calendar.keys():
                        calendar[week][1] = enddate
                    else:
                        calendar[week] = [startdate, enddate]
        return calendar
    def get_course_calendar(self, s):
        classes = {}
        for unitcode in self.unitcodes:
            uos_link = self.url + "/chooseLabel.jsp"
            r = self.session.get(uos_link)
            soup = BeautifulSoup(r.text, features="lxml")
            form = soup.find('form')
            tt_link = self.url + "/%s"%(form.get('action'))
            course_input = form.find('input').get('name')
            params = {course_input : unitcode}
            r = self.session.get(tt_link, params=params)
            soup = BeautifulSoup(r.text, features='lxml')
            heading = soup.find('div', {'class' : 'heading'})
            if "Choose an option" in heading.text:
                print("%s could not be found" % unitcode)
                continue
            table = soup.find('table', id="TblPartsAndclasses")
            tr_tags = table.find_all('tr', recursive=False)
            for i in range(len(tr_tags)):
                tr_id = tr_tags[i].get('id')
                if tr_id != None:
                    class_type = tr_id
                    classes[tr_id] = {}
                    j = i + 2
                    while j < len(tr_tags) and tr_tags[j].get('id') == None:
                        td_tags = tr_tags[j].find_all('td', recursive=False)
                        if '∗' in td_tags[1].text:
                            break
                        if j < len(tr_tags)-1 and tr_tags[j+1].get('class') != None:
                            break
                        class_id = td_tags[1].text.strip()
                        class_times = re.findall(r'(?:Mon|Tue|Wed|Thu|Fri)\s(?:[01]\d|2[0-3]):(?:[0-5]\d)-?(?:[01]\d|2[0-3])?:?(?:[0-5]\d)?', td_tags[3].text)
                        if class_times != []:
                            classes[tr_id][class_id] = class_times
                        j += 1
                    i = j
        return classes
    def enter_preferences(self, timetable):
        root_url = "https://www.timetable.usyd.edu.au"
        r = self.session.get(root_url + "/personaltimetable")
        soup = BeautifulSoup(r.text, "lxml")
        login = soup.find('a', {'class' : 'button submit-button'}).get('href')
        r = self.session.get(login)
        soup = BeautifulSoup(r.text, "lxml")
        for item in soup.find_all('a'):
            if 'preferences' in item.text:
                preferences = root_url + item.get('href')
        r = self.session.get(preferences)
        soup = BeautifulSoup(r.text, "lxml")

        # entering preferences from timetable 
    def check_timetable(self, timetable):
        # check that the existing timetable is the same as the proposed one
        # check the class times are the same 
        pass