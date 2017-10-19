#!/usr/bin/python

"""
This is a script to parse emails that are piped to it
from postfix.  This creates a file called "outqueue"
in your maildir directory which contains outgoing
emails that are queued to be sent by sailmail.
"""

import sys
import email
import pickle
import os

from sailmail import OutQueue

if __name__ == "__main__":

    q = OutQueue()
    q.put(email.message_from_string(sys.stdin.read()))
    q.save()

