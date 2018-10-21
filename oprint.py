import sys
import time

from bottle import route, run

from PyQt4.QtCore import QThread, SIGNAL
from PyQt4.QtGui import QApplication, QMainWindow


class PrintingThread(QThread):

    def run(self):
        while True:
            time.sleep(1)


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

        # web service
        self.web_thread = WebThread()
        self.web_thread.start()

        # printing service
        self.print_thread = PrintingThread()
        self.print_thread.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OPrint()
    window.show()
    app.exec_()
