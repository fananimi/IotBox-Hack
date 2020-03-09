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

from config import StateManagement
__config = StateManagement.getInstance()


def setup_log():
    logformat = '%(asctime)s - %(funcName)s - %(levelname)s: %(message)s'

    if __config.is_frozen is False:
        logging.basicConfig(
            format=logformat,
            level=__config.get_log_level(),
            handlers=[logging.StreamHandler()]
        )
    else:
        logging.basicConfig(
            format=logformat,
            level=__config.get_log_level(),
            filename=__config.get_log_file(),
            filemode='a'
        )


class LinkBox(QtGui.QDialog, Ui_Dialog):

    def __init__(self, config, parent=None):
        super(LinkBox, self).__init__(parent)
        self.config = config
        self.setupUi(self)

        self.web_thread = WebThread()
        self.web_thread.start()

        # run all driver
        for key in drivers.keys():
            drivers[key].start()

        # update status
        self.update_status()

        # register signal
        self.btnClose.clicked.connect(self.on_click_button)
        self.btnApply.clicked.connect(self.on_click_button)
        self.btnReload.clicked.connect(self.on_click_button)

    def update_status(self):
        self.txtPort.setText('%d' % self.config.get_service_port())

    def on_click_button(self):
        btn_name = self.sender().objectName()
        if btn_name == 'btnClose':
            self.hide()
            return
        if btn_name == 'btnApply':
            return
        if btn_name == 'btnReload':
            return


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

