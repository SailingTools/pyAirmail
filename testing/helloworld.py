"""
Simple example of Qt4 interface, more here:
/usr/share/doc/python-qt4-doc/examples
"""

import sys
from PyQt4.QtGui import *
app = QApplication(sys.argv)
button = QPushButton("Hello World", None)
button.show()
app.exec_()

