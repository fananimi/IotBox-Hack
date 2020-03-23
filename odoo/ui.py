import release

from PyQt5 import QtCore, QtGui, QtWidgets

from state import StateManager


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        super(SystemTrayIcon, self).__init__(icon, parent)
        menu = QtWidgets.QMenu(parent)
        # add menu
        self.menu_vesion = QtWidgets.QAction("LinkBox %s" % release.version)
        self.menu_quit = QtWidgets.QAction("Quit")
        menu.addAction(self.menu_vesion)
        menu.addSeparator()
        menu.addAction(self.menu_quit)
        # register signal
        self.menu_vesion.triggered.connect(self.show_dialog)
        self.menu_quit.triggered.connect(self.quit)
        self.setContextMenu(menu)

    def quit(self):
        QtCore.QCoreApplication.exit()

    def show_dialog(self):
        StateManager.getInstance().show_dialog()
