import os
import sys
import logging
import ConfigParser

from printer import Printer


# the singleton config class
class StateManager(ConfigParser.RawConfigParser):
    is_frozen = False
    base_path = None
    config_file = None
    dialog = None
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if StateManager.__instance is None:
            StateManager()
        return StateManager.__instance

    def __init__(self):
        ConfigParser.RawConfigParser.__init__(self)

        self.is_frozen = getattr(sys, 'frozen', False)
        if self.is_frozen:
            self.base_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))

        self.config_file = os.path.join(self.base_path, 'config.ini')
        """ Virtually private constructor. """
        if StateManager.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            try:
                if os.path.exists(self.config_file):
                    self.readfp(open(self.config_file))
                else:
                    self._create_config()
                    self.readfp(open(self.config_file))
            except ConfigParser.ParsingError:
                self._create_config()

            StateManager.__instance = self

    def _create_config(self):
        for section in self.sections():
            self._remove_section(section)
        with open(self.config_file, "wb") as config_file:
            self.write(config_file)

    def _write_config(self, section, option, value):
        with open(self.config_file, "wb") as config_file:
            self.set(section, option, value)
            self.write(config_file)

    def _remove_section(self, section):
        self.remove_section(section)

    def set_dialog(self, dialog):
        self.dialog = dialog

    def show_dialog(self):
        self.dialog.show()

    def get_service_port(self):
        serviceport = 8080
        section_key = 'SERVICE'
        if section_key not in self.sections():
            self.add_section(section_key)

        try:
            serviceport = self.getint(section_key, 'port')
            if not 1024 <= serviceport <= 65535:
                serviceport = 8080
                raise ValueError('port must be 1024-65535')
        except ConfigParser.NoOptionError:
            self._write_config(section_key, 'port', serviceport)
        except ValueError:
            self._write_config(section_key, 'port', serviceport)

        return serviceport

    @property
    def log(self):
        '''
        short-cut of get_log function
        :return: Log object
        '''
        return self.get_log()

    def get_log(self):
        '''
        :return: Log object
        '''
        class Log:
            def __init__(self, base_path):
                self.base_path = base_path
                self.level = ''
                self.name = ''

            @property
            def filename(self):
                logpath = os.path.join(self.base_path, 'logs')
                if not os.path.exists(logpath):
                    os.makedirs(logpath)
                logfile = os.path.join(logpath, self.name)
                return logfile

        log = Log(self.base_path)
        sections = {'LOG': [('level', 'ERROR'), ('name', 'odoo.log')]}
        for section in sections.keys():
            if section not in self.sections():
                self.add_section(section)
            for data in sections[section]:
                option = data[0]
                value = data[1]
                try:
                    value = self.get(section, option)
                except ConfigParser.NoOptionError:
                    self._write_config(section, option, value)
                finally:
                    setattr(log, option, value)

        return log
