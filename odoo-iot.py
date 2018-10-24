import sys
import signal

from odoo.ui import Main
from PyQt4.QtGui import QApplication


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    window = Main()
    window.show()
    app.exec_()
