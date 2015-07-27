import Tkinter as tk
from Tkconstants import *
import ttk

import json

from icom import radio
from widgets import LabeledEntry

import matplotlib.pyplot as plt
import threading

class AppFax(ttk.Frame):

    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        self.pack(fill=BOTH, expand=1)

        self.currentStation = 0
        self.currentFrequency = 0
        self.radioFrequency = 0
        self.connectType = 0
        self.readStationInfo()

        self.drawMenu()

    def updateMenus(self):
        self.stationDropDown.current(self.currentStation)
        self.freqDropDown['values'] = ['%.01f'%(f) for f in self.get_frequencies()]
        self.freqDropDown.current(self.currentFrequency)
        
    def drawMenu(self):
        stationFrame = tk.Frame(self, relief=RIDGE, borderwidth=2)
        stationFrame.pack(fill=X, expand=1)

        self.stationDropDown = ttk.Combobox(stationFrame, validatecommand = self.listLink, validate = 'all', values = self.get_stations())
        self.stationDropDown.current(self.currentStation)
        self.stationDropDown.state(['readonly'])
        self.stationDropDown.pack(side=LEFT)

        self.freqDropDown = ttk.Combobox(stationFrame, validatecommand = self.setFrequency, validate = 'all', values = ['%.01f'%(f) for f in self.get_frequencies()] )
        self.freqDropDown.current(self.currentFrequency)
        self.freqDropDown.state(['readonly'])
        self.freqDropDown.pack(side=RIGHT)

        self.button_connect = tk.Button(self, text="Connect", command=self.connect)
        self.button_connect.pack(side=LEFT)
        self.button_disconnect = tk.Button(self, text="Disconnect",command=self.disconnect)
        self.button_disconnect.pack(side=RIGHT)

    def setConnectType(self):
        if not self.connectDropDown.current() == self.connectType:
            self.connectType = self.connectDropDown.current()
            if self.connectType == 1:
                self.stationDropDown.state(['!disabled'])
                self.freqDropDown.state(['!disabled'])
                radio.start_radio()
                radio.remote(True)
                self.setFrequency()
            else:
                self.stationDropDown.state(['disabled'])
                self.freqDropDown.state(['disabled'])
                radio.remote(False)
                radio.close()
        return True

    def setFrequency(self):
        self.currentFrequency = self.freqDropDown.current()
        freq = int(self.get_current_frequency()*10) - 19
        if not self.radioFrequency == freq:
            self.radioFrequency = freq
            resp = radio.setFrequency(freq)
        return True

    def showText(self, text, index='500000.0'):
        self.textbox.insert(index,text+'\n')
        self.textbox.see(index)

    def disconnect(self):
        self.showText('Disconnecting')
        return None

    def connect(self):
        self.showText('Connecting')
        return None

    def readStationInfo(self):
        f = open('stations.txt','r')
        d = json.load(f)
        f.close()
        self.stations = d['wxfax']['stations']
        self.frequencies = d['wxfax']['frequencies']
        return None

    def listLink(self):
        if not self.stationDropDown.current() == self.currentStation:
            self.currentStation = self.stationDropDown.current()
            self.freqDropDown['values'] = ['%.01f'%(f) for f in self.get_frequencies()]
            self.freqDropDown.current(0)
            self.setFrequency()
        return True

    def get_stations(self):
        return ['%s: %s'%(i[0], i[1].split(';')[-1]) for i in self.stations.items()]

    def get_frequencies(self):
        station = self.stations.keys()[self.currentStation]
        return self.frequencies[station]

    def get_current_frequency(self):
        return self.get_frequencies()[self.freqDropDown.current()]
