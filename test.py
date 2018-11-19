import sys
from static import images
from PyQt4 import QtGui, QtCore

class SystemTrayIcon(QtGui.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
       QtGui.QSystemTrayIcon.__init__(self, icon, parent)
       menu = QtGui.QMenu(parent)
       exitAction = menu.addAction("Exit")
       self.setContextMenu(menu)
       QtCore.QObject.connect(exitAction,QtCore.SIGNAL('triggered()'), self.exit)

    def exit(self):
      QtCore.QCoreApplication.exit()

def main():
   app = QtGui.QApplication(sys.argv)

   w = QtGui.QWidget()
   #trayIcon = SystemTrayIcon(QtGui.QIcon("printer.png"), w)
   pixmap = QtGui.QPixmap()
   pixmap.loadFromData(QtCore.QByteArray.fromBase64(images.printer_png))
   icon = QtGui.QIcon(pixmap)
   trayIcon = SystemTrayIcon(icon)

   trayIcon.show()
   sys.exit(app.exec_())

if __name__ == '__main__':
    main()
