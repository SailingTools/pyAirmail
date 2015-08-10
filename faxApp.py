import Tkinter as tk
from Tkconstants import *
import ttk

import json
import time

from icom import radio
from modem import modem, Fax
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

        self.fax = Fax(modem)
        self.fax.gui_callback = self.buttons_update

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

        self.button_connect = tk.Button(self, text="Start FaxMode", command=self.connect)
        self.button_connect.pack(side=LEFT)

        self.button_record = tk.Button(self, text="Start Record", command=self.toggle_record)
        self.button_record.pack(side=LEFT)

        self.button_apt = tk.Button(self, text="Start APT", command=self.toggle_apt)
        self.button_apt.pack(side=LEFT)

        self.button_quit = tk.Button(self, text="Quit FaxMode", command=self.disconnect)
        self.button_quit.pack(side=RIGHT)

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

    def connect(self):
        self.fax.start()
        self.buttons_update()

    def disconnect(self):
        self.fax.quit()
        self.buttons_update()

    def toggle_connect(self):
        if self.fax.receive_flag:
            self.fax.quit()
        else:
            self.fax.start()
        self.buttons_update()
        return None

    def toggle_record(self):
        if self.fax.record_flag:
            self.fax.record_stop()
        else:
            self.fax.record_start()
        self.buttons_update()
        return None

    def toggle_apt(self):
        if self.fax.apt_flag:
            self.fax.apt_stop()
        else:
            self.fax.apt_start()
        self.buttons_update()
        return None

    def buttons_update(self):
        time.sleep(0.1)
        self.button_connect['text'] = 'Stop FaxMode' if self.fax.receive_flag else 'Start FaxMode'
        self.button_record['text'] = 'Stop Recording' if self.fax.record_flag else 'Start Recording'
        self.button_apt['text'] = 'Stop APT' if self.fax.apt_flag else 'Start APT'

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
