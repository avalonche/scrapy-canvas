import re
import itertools
import numpy as np
import matplotlib.pyplot as plt
from config import *
"""
Generates timetable from the timetable website 

Features not  implemented yet:
- option to remove tutes and lectures that are not necessary 
- classes (excluding lectures) that only have one time need to be included in the set to be optimised 
dealing with classes. Currently assumes that classes with only one time slot are lectures 
- need to make sure that lectures with more than 1 time option can still fit, otherwise need to 
generate another timetable
"""
class Scheduler:
    # class blocks should be a 2D matrix, with 30 min blocks
    # starts from 8 am and ends at 9 pm
    def __init__(self, classes):
        w, h = 5, 26
        self.matrix = [[0 for x in range(w)]for y in range(h)]
        self.class_times = classes
        self.timetable = {}
    # transform the data structure to list the classes by day then time for later processing 
    def __placeinitclass(self):
        for class_, class_info in self.class_times.items():
            if len(class_info) == 1:
                for times in class_info.values():
                    for item in times:
                        day = self.__weekday_to_number(item)
                        time = self.__time_to_number(item)
                        self.__place_class(self.matrix, day, time)
                self.timetable[class_] = class_info
    # after classes with only 1 option is placed, eliminate options with other classes that will clash
    def __eliminateclashes(self, matrix, timetable, options):
        for class_ in timetable:
            if class_ in options:
                del options[class_]
        for class_ in options.values():
            for day, times in class_.items():
                for time in times:
                    if not self.__available(matrix, day, time):
                        times.remove(time)
            for day in list(class_):
                if class_[day] == []:
                    del class_[day]
    # transforming all class weekday names and times to indicies in the 2D matrix
    def __prepclasses(self):
        class_options = {}
        for class_, class_info in self.class_times.items():
            class_options[class_] = {}
            for class_code, times in class_info.items():
                for item in times:
                    day = self.__weekday_to_number(item)
                    time = self.__time_to_number(item)
                    if day not in class_options[class_].keys():
                        class_options[class_][day] = []
                    if (time[0], time[1]) not in class_options[class_][day]:
                        class_options[class_][day].append((time[0], time[1]))
        return class_options
    # weekday to number in the matrix
    def __weekday_to_number(self, class_time):
        if class_time.startswith("Mon"):
            return 0
        elif class_time.startswith("Tue"):
            return 1
        elif class_time.startswith("Wed"):
            return 2
        elif class_time.startswith("Thu"):
            return 3
        elif class_time.startswith("Fri"):
            return 4
    # time of day to number in the matrix
    def __time_to_number(self, class_time):
        time_span = []
        time = class_time.split()[1]
        periods = re.split(':|-',time)
        for i in range(0, len(periods), 2):
            position = 0
            hour = int(periods[i])
            # set back relative to 8 am 
            position += hour*2 - 16
            minutes = int(periods[i+1])
            if minutes != 0:
                position += 1
            time_span.append(position)
        if len(time_span) == 1:
            time_span.append(time_span[0]+2)
        return time_span
    # checks if a time slot is available in the timetable matrix
    def __available(self, matrix, day, time):
        for i in range(time[0], time[1]):
            if matrix[i][day] == 1:
                return False
        return True
    # places class in the matrix, 1 if occupied, 0 if free
    def __place_class(self, matrix, day, time):
        for i in range(time[0], time[1]):
            matrix[i][day] = 1
    # remove class if a class is found to clash with everything else
    def __remove_class(self, matrix, day, time):
        for i in range(time[0], time[1]):
            matrix[i][day] = 0
    # remove some unneccessary tutes, lectures etc (to be implemented)
    def remove_optional_classes(self, class_options):
        pass
    # checking if all classes have at least one class in the selected combinations of weekdays
    # this is to reduce the selection set 
    def __check_valid_days(self, options, comb):
        count = 0
        check = []
        for i in range(len(comb)):
            for code, times in options.items():
                if comb[i] in times.keys():
                    check.append(code)
        check = set(check)
        if len(check) == len(options):
            return True
        return False
    # generating all possible day combinations of the week, sorted from least to most days
    # pointless to choose days that don't cover all classes in the set
    def __day_combinations(self, options):
        # combinations of days that includes all classes
        possible_days = []
        for i in range(1,5):
            for subset in itertools.combinations(range(5), i):
                if self.__check_valid_days(options, subset):
                    possible_days.append(subset)
        return possible_days       
    # deducing the class code of a class by its day and starting time
    def __time_to_class_code(self, day, time):
        code = ''
        if day == 0:
            code += 'M'
        elif day == 1:
            code += 'T'
        elif day == 2:
            code += 'W'
        elif day == 3:
            code += 'R'
        elif day == 4:
            code += 'F'
        num = str((time[0] + 16)//2)
        if len(num) < 2:
            num = str(0) + num
        code += num
        return code   
    # returns the class, class times, and class code og timetable in a dictionary
    def generate_timetable(self):
        options = self.__prepclasses()
        self.__placeinitclass()
        self.__eliminateclashes(self.matrix, self.timetable, options)
        possible_days = self.__day_combinations(options)
        matrix = self.__test_combo(possible_days, options)
        self.matrix = [row[:] for row in matrix]
        return self.timetable
    # iterating through the sorted day combinations and return the first valid timetable
    # that has no clashes. As the day combos are sorted, the first it finds will contain 
    # the least days
    def __test_combo(self, possible_days, options):
        for i in range(len(possible_days)):
            placed_classes = {}
            test_matrix = [row[:] for row in self.matrix]
            test_options = []
            for item, info in options.items():
                temp = []
                for day, times in info.items():
                    if day in possible_days[i]:
                        for time in times:
                            temp.append((day, time, item))
                if len(temp) == 1:
                    class_code = self.__time_to_class_code(temp[0][0], temp[0][1])
                    if self.__available(test_matrix, temp[0][0], temp[0][1]):
                        self.__place_class(test_matrix, temp[0][0], temp[0][1])
                    placed_classes[temp[0][2]] = (temp[0][0], temp[0][1]) 
                    continue                 
                test_options.append(temp)
            # heuristic to have classes as compact as possible to fit in the timetable
            test_options = sorted(test_options)
            # need to test this more thououghly
            # instead of placing classes based on no. of options of a class, based on 
            # next available class to fill in the empty slot
            def combos(terms, prev):
                n = len(terms[0])
                i = 0
                while i < n:
                    day = terms[0][i][0]
                    time = terms[0][i][1]
                    class_= terms[0][i][2]
                    if self.__available(test_matrix, day, time):
                        self.__place_class(test_matrix, day, time)
                        placed_classes[class_] = (day, time)
                        prev = (day, time, class_)
                        if len(placed_classes) == len(options):
                            return
                        else:
                            return combos(terms[1:], prev)
                    i += 1
                    # means not possible to place class, there is clash 
                    if i == n and prev:
                        # remove the previous class and keep iterating
                        self.__remove_class(test_matrix, prev[0], prev[1])
            combos(test_options, None)
            if len(placed_classes) == len(options):
                break
        for k, v in placed_classes.items():
            self.timetable[k] = {}
            for class_code, class_time in self.class_times[k].items():
                day = v[0]
                time = v[1]
                selected_class_code = self.__time_to_class_code(day, time)
                if class_code.startswith(selected_class_code):
                    self.timetable[k][class_code] = class_time
        return test_matrix
    # plotting the committed timetable found
    # only have time slots, no info about what class is during that time
    def plot_timetable(self):
        H = np.array(self.matrix)
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_xticks(np.arange(0, 5, 1))
        ax.set_yticks([])
        ax.set_yticks(np.arange(-.5, 26, 2), minor=True)
        ax.set_xticks(np.arange(-.5, 5, 1), minor=True)
        xlabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        ax.set_xticklabels(xlabels)
        ylabels = []
        for i in range(8, 22):
            ylabels.append(i)
        ax.set_yticklabels('')
        ax.set_yticklabels(ylabels, minor=True)
        plt.grid(b=True, which='minor', color='black', linewidth=2.5)
        ax.imshow(H, cmap='binary')
        ax.set_aspect(0.2)
        plt.title('Timetable')
        plt.show()