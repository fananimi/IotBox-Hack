import os
import sys
import signal
import logging
import ConfigParser

from PyQt4 import QtCore, QtGui

from static.images import xpm
from odoo.ui import SystemTrayIcon


__is_frozen__ = getattr(sys, 'frozen', False)


if __is_frozen__:
    BASE_PATH = os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_PATH, 'config.ini')


def get_config():
    config = ConfigParser.RawConfigParser()
    if not os.path.exists(CONFIG_FILE):
        config.add_section('LOG')
        config.set('LOG', 'level', 'DEBUG')
        config.set('LOG', 'name', 'odoo.log')

        with open(CONFIG_FILE, "wb") as config_file:
            config.write(config_file)

    config.readfp(open(CONFIG_FILE))
    return config


def setup_log():
    config = get_config()
    logformat = '%(asctime)s - %(funcName)s - %(levelname)s: %(message)s'

    loglevel = 'ERROR'
    try:
        loglevel = config.get('LOG', 'level').upper()
        all_levels = [fmt for fmt in logging._levelNames if isinstance(fmt, str)]
        if loglevel not in all_levels:
            loglevel = 'ERROR'
    except ConfigParser.NoSectionError:
        pass

    if __is_frozen__ is False:
        logging.basicConfig(
            format=logformat,
            level=loglevel,
            handlers=[logging.StreamHandler()]
        )
    else:
        logname = 'odoo.log'
        try:
            logname = config.get('LOG', 'name')
        except ConfigParser.NoOptionError:
            pass

        logpath = os.path.join(BASE_PATH, 'logs')
        if not os.path.exists(logpath):
            os.makedirs(logpath)
        logfile = os.path.join(logpath, logname)

        logging.basicConfig(
            format=logformat,
            level=loglevel,
            filename=logfile,
            filemode='a'
        )


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtGui.QApplication(sys.argv)

    trayIcon = SystemTrayIcon(QtGui.QIcon(QtGui.QPixmap(xpm.icon_64)))
    trayIcon.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    setup_log()
    main()

