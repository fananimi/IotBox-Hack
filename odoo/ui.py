from odoo.thread import WebThread
from addons.hw_proxy.controllers.main import drivers

from PyQt4.QtGui import QMainWindow


class Main(QMainWindow):

    def __init__(self, parent=None):
        super(Main, self).__init__(parent)

        self.web_thread = WebThread()
        self.web_thread.start()

        # run all driver
        for key in drivers.keys():
            drivers[key].start()
