import os
import sys
import operator
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

    def _build_config(self, instance, sections):
        for section in sections.keys():
            if section not in self.sections():
                self.add_section(section)
            for data in sections[section]:
                option = data[0]
                type = data[1]
                default_value, value = (data[2], None)
                is_error = False
                try:
                    if type == int:
                        value = self.getint(section, option)
                    else:
                        value = self.get(section, option)
                    # in case we have validation on class
                    validation_func = 'validate_%s' % option
                    if hasattr(instance, validation_func):
                        func = getattr(instance, validation_func)
                        # call the function
                        func(value)
                except (ConfigParser.NoOptionError, ValueError):
                    is_error = True
                    self._write_config(section, option, default_value)
                finally:
                    setattr(instance, option, default_value if is_error else value)
        return instance

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

            def validate_level(self, value):
                allowed_values = []
                for level in logging._levelNames.keys():
                    if isinstance(level, str):
                        allowed_values.append(level)
                if value not in allowed_values:
                    raise ValueError('level must be %s' % str(allowed_values))

                return value

        log = Log(self.base_path)
        sections = {'LOG': [('level', str, 'ERROR'), ('name', str, 'odoo.log')]}
        return self._build_config(log, sections)

    @property
    def web_service(self):
        '''
        short-cut of get_web_service function
        :return: WebService object
        '''
        return self.get_web_service()

    def get_web_service(self):
        '''
        :return: WebService object
        '''
        class WebService:
            def __init__(self):
                self.port = None

            def validate_port(self, value):
                if not 1024 <= value <= 65535:
                    raise ValueError('port must be 1024-65535')

                return value

        webservice = WebService()
        sections = {'SERVICE': [('port', int, 8080)]}
        return self._build_config(webservice, sections)
