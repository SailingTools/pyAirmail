import Tkinter as tk
from Tkconstants import *
import ttk
import tkMessageBox as tMB

import re

class ValidEntry(ttk.Entry):
    """Creates a ttk.Entry field and accepts a regex string for validation of
    user entry. If the entry does not match the regex upon focus moving away from
    the widget, an error message will be displayed and focus will remain on the
    widget.
    """

    def __init__(self, master = None, width = 20, style = None, justify = tk.RIGHT,
            validateStr = r'^.*$', validate = 'focusout'):

        # controlVariable:
        self.cVar = tk.StringVar()

        # regex for field validation:
        self.validateStr = validateStr

        # register validation functions:
        self.validateFun = master.register(self.validateEntry)
        self.invalidFun = master.register(self.invalidEntry)

        ttk.Entry.__init__(self, master, style = style, width = width, justify = justify,
                textvariable = self.cVar, validatecommand = self.validateFun,
                invalidcommand = self.invalidFun, validate = validate)


    def validateEntry(self):
        r = re.compile(self.validateStr + '|^$', re.VERBOSE)
        if r.match(self.cVar.get()):
            return True
        else:
            return False

    def invalidEntry(self):
        message = 'Invalid entry: ' + self.cVar.get() + '\nentry must match ' + self.validateStr
        tMB.showerror('Invalid entry', message)
        self.focus_set()
        self.selection_own()


class LabeledEntry(ttk.Frame):
    """Provides a ValidEntry field, prefixed by a text label"""

    def __init__(self, master = None, labelText = "Label", entryWidth = None, entryJustify = tk.LEFT,
            entryValidateStr = r'^.*$', frameStyle = None, entryStyle = None, labelStyle = None):
        """Calls ttk.Frame contructor and then places a right-aligned label followed
        by a left-aligned ValidEntry box inside the frame.
        """
        ttk.Frame.__init__(self, master, class_ = "LabeledEntry", style = frameStyle)

        self.label = ttk.Label(self, text = labelText, justify=tk.LEFT)
        self.label.grid(row = 0, column = 0, sticky = tk.E)

        self.entry = ValidEntry(self, width = entryWidth, validateStr = entryValidateStr)
        self.entry.grid(row = 0, column = 1, sticky = tk.W)

    def set(self, text):
        self.entry.cVar.set(text)

    def get(self):
        return self.entry.cVar.get()