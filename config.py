import os
import sys
import logging
import ConfigParser


# the singleton config class
class Config(ConfigParser.RawConfigParser):
    is_frozen = False
    __config_file = None
    __base_path = None
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if Config.__instance is None:
            Config()
        return Config.__instance

    def __init__(self):
        ConfigParser.RawConfigParser.__init__(self)

        self.is_frozen = getattr(sys, 'frozen', False)
        if self.is_frozen:
            self.__base_path = os.path.dirname(sys.executable)
        else:
            self.__base_path = os.path.dirname(os.path.abspath(__file__))

        self.__config_file = os.path.join(self.__base_path, 'config.ini')
        """ Virtually private constructor. """
        if Config.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            try:
                self.readfp(open(self.__config_file))
            except ConfigParser.ParsingError:
                self._create_log()
                self.readfp(open(self.__config_file))
            except IOError:
                self._create_log()
                self.readfp(open(self.__config_file))

            Config.__instance = self

    def _create_log(self):
        with open(self.__config_file, "wb") as config_file:
            self.write(config_file)

    def _write_log(self, section, option, value):
        with open(self.__config_file, "wb") as config_file:
            self.set(section, option, value)
            self.write(config_file)

    def get_service_port(self):
        raise NotImplemented()

    def get_log_level(self):
        loglevel = 'ERROR'
        try:
            loglevel = self.get('LOG', 'level')
            all_levels = [fmt for fmt in logging._levelNames if isinstance(fmt, str)]
            if loglevel.upper() not in all_levels:
                loglevel = 'ERROR'
                self._write_log('LOG', 'level', loglevel)
        except ConfigParser.NoSectionError:
            self.add_section('LOG')
            self._write_log('LOG', 'level', loglevel)
        except ConfigParser.NoOptionError:
            self._write_log('LOG', 'level', loglevel)

        return loglevel

    def get_log_name(self):
        logname = 'odoo.log'
        try:
            logname = self.get('LOG', 'name')
        except ConfigParser.NoSectionError:
            self.add_section('LOG')
            self._write_log('LOG', 'name', logname)
        except ConfigParser.NoOptionError:
            self._write_log('LOG', 'name', logname)

        return logname

    def get_log_file(self):
        logpath = os.path.join(self.__base_path, 'logs')
        if not os.path.exists(logpath):
            os.makedirs(logpath)
        logfile = os.path.join(logpath, self.get_log_name())
        return logfile
