from odoo.thread import WebThread
from addons.hw_proxy.controllers.main import drivers

from PyQt4 import QtCore, QtGui


class SystemTrayIcon(QtGui.QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        super(SystemTrayIcon, self).__init__(parent)

        QtGui.QSystemTrayIcon.__init__(self, icon, parent)
        menu = QtGui.QMenu(parent)
        exitAction = menu.addAction("Exit")
        self.setContextMenu(menu)
        QtCore.QObject.connect(exitAction,QtCore.SIGNAL('triggered()'), self.exit)

        self.web_thread = WebThread()
        self.web_thread.start()

        # run all driver
        for key in drivers.keys():
            drivers[key].start()

    def exit(self):
        QtCore.QCoreApplication.exit()

