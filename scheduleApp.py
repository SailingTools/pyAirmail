import Tkinter as tk
from Tkconstants import *
import ttk

import datetime
import time

from icom import radio
from widgets import LabeledEntry

from apscheduler.schedulers.background import BackgroundScheduler

class AppScheduler(ttk.Frame):

    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        self.pack(fill=BOTH, expand=1)
        
        self.jobList = []
        self.schedules = []
        self.drawMenu()

        # Set up the Background Scheduler
        self.sched = BackgroundScheduler()
        self.sched.start()

    def drawMenu(self):
        newSched = ttk.Frame(self, relief=RIDGE, borderwidth=2)
        newSched.pack(fill=X, side=TOP)
        
        self.newName = LabeledEntry(newSched, labelText = "Name", entryWidth = 30)
        self.newName.grid(row=0, column=0)
        self.newName.set('Unnamed')

        self.newHour = LabeledEntry(newSched, labelText = "Hours", entryWidth = 8)
        self.newHour.grid(row=1, column=0, sticky=tk.W)
        self.newHour.set('0-23')

        self.newMin = LabeledEntry(newSched, labelText = "Minutes", entryWidth = 8)
        self.newMin.grid(row=1, column=1, sticky=tk.W)
        self.newMin.set('0,30')

        self.newDur = LabeledEntry(newSched, labelText = "Duration [mins]", entryWidth = 8, entryValidateStr = r'^[0-9]*$')
        self.newDur.grid(row=2, column=0, sticky=tk.W)
        self.newDur.set('5')

        self.newFreq = LabeledEntry(newSched, labelText = "Frequency", entryWidth = 8, entryValidateStr = r'^[0-9]*\.?[0-9]?$')
        self.newFreq.grid(row=2, column=1, sticky=tk.W)
        self.newFreq.set('0.0')

        addButton = ttk.Button(newSched, text = "Add Schedule", width = 3, command = self.addSchedule)
        addButton.grid(row=2, column=2, sticky=tk.E)

        return None

    def addSchedule(self):
        self.schedules.append( scheduleItem(self) )

    def start_jobList(self):
        for j in self.jobList:
            self.newName.set(j['name'])
            self.newHour.set(j['hours'])
            self.newMin.set(j['mins'])
            self.newDur.set(j['duration'])
            self.newFreq.set(j['frequency'])
            self.schedules.append( scheduleItem(self) )

        # Reset to some default values
        self.newName.set('Unnamed')
        self.newHour.set('0-23')
        self.newMin.set('0,30')
        self.newDur.set('4')
        self.newFreq.set('12362.0')
        
        return None

    def make_jobList(self):
        self.jobList = []
        for s in self.schedules:
            self.jobList.append({
                    'name': s.name,
                    'hours': s.hours,
                    'mins': s.mins,
                    'duration': s.duration,
                    'frequency': s.frequency
                })
        return self.jobList

    def start_radio(self, frequency=0):
        radio.start_radio()
        if frequency:
            radio.remote(True)
            radio.setFrequency(int(frequency*10))
        return None

    def stop_radio(self):
        radio.remote(False)
        radio.close()
        return None

class scheduleItem(ttk.Frame):
    
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        self.pack(fill=X)

        self.name = master.newName.get()
        self.hours = master.newHour.get()
        self.mins = master.newMin.get()
        self.duration = int(master.newDur.get())
        self.frequency = float(master.newFreq.get())

        self.job = master.sched.add_job(self.run_job, 'cron', hour=self.hours, minute=self.mins, timezone='utc')

        self.drawMenu()

    def drawMenu(self):

        self.label = ttk.Label(self, text = '%s'%(self.name.upper()))
        self.label.grid(row = 0, column = 0, sticky = tk.W)

        self.label = ttk.Label(self, text = 'Hours: %s, Mins: %s, Duration: %i, Frequency: %.01f'%(self.hours, self.mins, self.duration, self.frequency))
        self.label.grid(row = 1, column = 0, sticky = tk.W)

        stopButton = ttk.Button(self, text = "Stop", width = 3, command = self.stopSchedule)
        stopButton.grid(row=1, column=4, sticky=tk.E)

        delButton = ttk.Button(self, text = "Del", width = 3, command = self.delSchedule)
        delButton.grid(row=1, column=5, sticky=tk.E)

        self.timeTo = ttk.Label(self, text = 'Next: %s'%(self.job.next_run_time.strftime('%H:%M:%S')))
        self.timeTo.grid(row=0, column=4, sticky=tk.E)
        return None

    def run_job(self):
        self.stopper = False
        self.timeTo['text'] = 'Running...'
        self.master.start_radio(frequency=self.frequency)
        if self.duration:
            stop_time = datetime.datetime.now() + datetime.timedelta(seconds=60*int(self.duration))
	    while (self.stopper is False) and (datetime.datetime.now() < stop_time):
            	time.sleep(1)
            self.master.stop_radio()
        time.sleep(1)
        self.timeTo['text'] = 'Next: %s'%(self.job.next_run_time.strftime('%H:%M:%S'))

    def stopSchedule(self):
	print('Stopping...')
        self.stopper = True

    def delSchedule(self):
        self.master.schedules.remove(self)
        self.job.remove()
        self.destroy()