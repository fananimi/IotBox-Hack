import release
from PyQt4 import QtCore, QtGui


class SystemTrayIcon(QtGui.QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        super(SystemTrayIcon, self).__init__(parent)

        QtGui.QSystemTrayIcon.__init__(self, icon, parent)
        menu = QtGui.QMenu(parent)
        # add menu
        versionAction = menu.addAction("LinkBox %s" % release.version)
        menu.addSeparator()
        quitAction = menu.addAction("Quit LinkBox")
        self.setContextMenu(menu)
        # register signal
        QtCore.QObject.connect(quitAction,QtCore.SIGNAL('triggered()'), self.quit)

    def quit(self):
        QtCore.QCoreApplication.exit()
