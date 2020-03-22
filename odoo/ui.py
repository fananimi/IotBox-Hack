import release
try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    QMenu = QtWidgets.QMenu
    QSystemTrayIcon = QtWidgets.QSystemTrayIcon
except ImportError:
    from PyQt4 import QtCore, QtGui
    QMenu = QtGui.QMenu
    QSystemTrayIcon = QtGui.QSystemTrayIcon

from state import StateManager


class SystemTrayIcon(QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        super(SystemTrayIcon, self).__init__(icon, parent)

        menu = QMenu(parent)
        # add menu
        versionAction = menu.addAction("LinkBox %s" % release.version)
        QtCore.QObject.connect(versionAction, QtCore.SIGNAL('triggered()'), self.show_dialog)
        menu.addSeparator()
        quitAction = menu.addAction("Quit")
        self.setContextMenu(menu)
        # register signal
        QtCore.QObject.connect(quitAction,QtCore.SIGNAL('triggered()'), self.quit)

    def quit(self):
        QtCore.QCoreApplication.exit()

    def show_dialog(self):
        StateManager.getInstance().show_dialog()
