#!/usr/bin/python

import Tkinter as tk
from Tkconstants import *
import ttk
import tkMessageBox as tMB
import json

import serial
import time
import os
import re

import threading
from datetime import datetime
import pytz

from widgets import LabeledEntry
from icom import radio

from scheduleApp import AppScheduler
from scannerApp import AppScanner
from sailmailApp import AppEmail

#modem = serial.Serial(port='/dev/modemSCS', baudrate=57600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=10, xonxoff=True)

def setPath(obj, path, value):
    pp = path.split('.')
    if len(pp) > 1:
        setPath(getattr(obj, pp[0]), '.'.join(pp[1:]), value)
    else:
        setattr(obj, pp[0], value)
    return None

class Application(ttk.Frame):
    """ Top level class; creates root window"""

    def __init__(self, master=None):
        ttk.Frame.__init__(self, master, width = 800, height = 600)
        self.grid_propagate(0)

        self.nb = ttk.Notebook(self)
        self.nb.grid()
        self.nb.pack(fill=BOTH, expand=1)

        self.nb.scheduler = AppScheduler(self.nb)
        self.nb.add(self.nb.scheduler, text="Scheduler")

        self.nb.email = AppEmail(self.nb)
        self.nb.add(self.nb.email, text="Sailmail")

        self.nb.scanner = AppScanner(self.nb)
        self.nb.add(self.nb.scanner, text="Scanner")

        self.menubar = AppMenuBar(self.winfo_toplevel())

        self.toggleRemote = ttk.Button(self, text="Remote Toggle", command=self.toggle_remote)
        self.toggleRemote.pack(side=LEFT)

        self.channel = LabeledEntry(self, labelText = "Channel:", entryWidth = 8, entryValidateStr = r'^[0-9]*\.?[0-9]?$')
        self.channel.set('0.0')
        self.channel.pack(side=LEFT)

        self.setChannel = ttk.Button(self, text="Set", command=self.setChannel)
        self.setChannel.pack(side=LEFT)

        self.clock = ttk.Label(self, text="--")
        self.clock.pack(fill=X, side=RIGHT)
        self.clockThread = threading.Thread(target=self.runClock)
        self.clockThread.daemon = True
        self.clockThread.start()

        # Load prior settings and update menu selections
        self.loadSettings()
        self.nb.email.updateMenus()
        self.nb.scheduler.start_jobList()

        self.bind('<Destroy>', self.saveSettings)

    def toggle_remote(self):
        if radio.is_remote():
            radio.remote(False)
        else:
            radio.remote(True)

    def setChannel(self):
        radio.setFrequency(int(float(self.channel.get())*10))

    def runClock(self):
        timezone = pytz.timezone('utc')
        while True:
            utctime = datetime.now(tz=timezone)
            self.clock['text'] = "%s utc"%(utctime.strftime("%H:%M:%S"))
            time.sleep(1)

    def saveSettings(self, args):
        print('Saving settings...')
        settings = {'nb.email': {
                        'currentStation': self.nb.email.currentStation,
                        'currentFrequency': self.nb.email.currentFrequency
                        },
                    'nb.scheduler': {
                        'jobList': self.nb.scheduler.make_jobList()
                        }
                    }
        f = open('pyPaclink.ini', 'w')
        json.dump(settings, f, indent=1)
        f.close()
        print('Quitting...')
        return None

    def setFromDict(self, d, parent=''):
        for (key, value) in d.items():
            path = "%s.%s"%(parent, key) if parent else key
            if type(value) == dict:
                self.setFromDict(value, parent=path)
            else:
                setPath(self, path, value)
        return None

    def loadSettings(self):
        try:
            f = open('pyPaclink.ini', 'r')
            settings = json.load(f)
            f.close()
            print('Found .ini file.  Loading settings.')
        except:
            settings = None
            print('No .ini file found.')
        if settings:
            self.setFromDict(settings)
        return None

class AppMenuBar(tk.Menu):
    """Creates menu bar for toplevel window with File and Help choices"""
    
    def __init__(self, top):
        tk.Menu.__init__(self, top)
        self.top = top
        self.top['menu'] = self

        # add 'File' menu
        self.fileMenu = tk.Menu(self, tearoff = 0)
        self.add_cascade(label = 'File', menu = self.fileMenu)
        self.fileMenu.add_command(label = 'Open...', command = self.__placeholder)
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label = 'Quit', command = self.__quitHandler)

        # add 'Help' menu
        self.helpMenu = tk.Menu(self, tearoff = 0)
        self.add_cascade(label = 'Help', menu = self.helpMenu)
        self.helpMenu.add_command(label = 'About', command = self.__aboutHandler)

    def __quitHandler(self):
        self.top.destroy()

    def __aboutHandler(self):
        aboutStr = ('pyPaclink v0.1: Python Controller for ICOM-M802 radio & SCS PTC-IIex PACTOR modem.\n')
        aboutStr += 'Use at your own risk!\n'
        tMB.showinfo('About pyPaclink', aboutStr, icon = tMB.INFO)

    def __placeholder(self):
        print("Function not yet implemented")

if __name__ == '__main__':
    root = tk.Tk()
    app = Application(root)
    app.grid()
    app.mainloop()
