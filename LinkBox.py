import os
import sys
import signal
import logging
import ConfigParser

from PyQt4 import QtCore, QtGui

from addons.hw_proxy.controllers.main import drivers
from odoo.thread import WebThread
from odoo.ui import SystemTrayIcon
from static.images import xpm
from ui.main import Ui_Dialog


__is_frozen__ = getattr(sys, 'frozen', False)


if __is_frozen__:
    BASE_PATH = os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_PATH, 'config.ini')


_config = ConfigParser.RawConfigParser()


def _create_log():
    with open(CONFIG_FILE, "wb") as config_file:
        _config.write(config_file)


try:
    _config.readfp(open(CONFIG_FILE))
except ConfigParser.ParsingError:
    _create_log()
    _config.readfp(open(CONFIG_FILE))
except IOError:
    _create_log()
    _config.readfp(open(CONFIG_FILE))


def setup_log():
    logformat = '%(asctime)s - %(funcName)s - %(levelname)s: %(message)s'

    def write_log(section, option, value):
        with open(CONFIG_FILE, "wb") as config_file:
            _config.set(section, option, value)
            _config.write(config_file)

    def get_log_level():
        loglevel = 'ERROR'
        try:
            loglevel = _config.get('LOG', 'level')
            all_levels = [fmt for fmt in logging._levelNames if isinstance(fmt, str)]
            if loglevel.upper() not in all_levels:
                loglevel = 'ERROR'
                write_log('LOG', 'level', loglevel)
        except ConfigParser.NoSectionError:
            _config.add_section('LOG')
            write_log('LOG', 'level', loglevel)
        except ConfigParser.NoOptionError:
            write_log('LOG', 'level', loglevel)

        return loglevel

    def get_log_name():
        logname = 'odoo.log'
        try:
            logname = _config.get('LOG', 'name')
        except ConfigParser.NoSectionError:
            _config.add_section('LOG')
            write_log('LOG', 'name', logname)
        except ConfigParser.NoOptionError:
            write_log('LOG', 'name', logname)

        return logname

    if __is_frozen__ is False:
        logging.basicConfig(
            format=logformat,
            level=get_log_level(),
            handlers=[logging.StreamHandler()]
        )
    else:
        logpath = os.path.join(BASE_PATH, 'logs')
        if not os.path.exists(logpath):
            os.makedirs(logpath)
        logfile = os.path.join(logpath, get_log_name())

        logging.basicConfig(
            format=logformat,
            level=get_log_level(),
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
    dialog = LinkBox(_config)
    dialog.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    setup_log()
    main()

