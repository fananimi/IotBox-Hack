import os
import sys
import signal
import logging

from PyQt4 import QtCore, QtGui

from addons.hw_proxy.controllers.main import drivers
from odoo.thread import WebThread
from odoo.ui import SystemTrayIcon
from static.images import xpm
from ui.main import Ui_Dialog

from config import Config
__config = Config.getInstance()


__is_frozen__ = getattr(sys, 'frozen', False)
if __is_frozen__:
    BASE_PATH = os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def setup_log():
    logformat = '%(asctime)s - %(funcName)s - %(levelname)s: %(message)s'

    if __is_frozen__ is False:
        logging.basicConfig(
            format=logformat,
            level=__config.get_log_level(),
            handlers=[logging.StreamHandler()]
        )
    else:
        logpath = os.path.join(BASE_PATH, 'logs')
        if not os.path.exists(logpath):
            os.makedirs(logpath)
        logfile = os.path.join(logpath, __config.get_log_name())

        logging.basicConfig(
            format=logformat,
            level=__config.get_log_level(),
            filename=logfile,
            filemode='a'
        )


class LinkBox(QtGui.QDialog, Ui_Dialog):

    def __init__(self, config, parent=None):
        super(LinkBox, self).__init__(parent)
        self.setupUi(self)

        self.web_thread = WebThread()
        self.web_thread.start()

        # run all driver
        for key in drivers.keys():
            drivers[key].start()


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtGui.QApplication(sys.argv)

    # show system try icon
    systemTryIcon = SystemTrayIcon(QtGui.QIcon(QtGui.QPixmap(xpm.icon_64)))
    systemTryIcon.show()
    # ui dialog
    dialog = LinkBox(__config)
    dialog.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    setup_log()
    main()

