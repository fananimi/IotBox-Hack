import sys

from bottle import route, run

from PyQt4.QtCore import QThread
from PyQt4.QtGui import QApplication, QMainWindow


class PrintingThread(QThread):
    pass


class WebThread(QThread):

    @staticmethod
    @route('/hello')
    def hello():
        return "Hello World!"

    def run(self):
        run(host='localhost', port=8080, debug=True)


class OPrint(QMainWindow):

    def __init__(self, parent=None):
        super(OPrint, self).__init__(parent)

        self.web_thread = WebThread()
        self.web_thread.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OPrint()
    window.show()
    app.exec_()
