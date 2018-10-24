import sys

from odoo.ui import Main
from PyQt4.QtGui import QApplication


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main()
    window.show()
    app.exec_()
