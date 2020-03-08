import os
import logging
import ConfigParser


# the singleton config class
class Config(ConfigParser.RawConfigParser):
    __instance = None
    __config_file = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if Config.__instance is None:
            Config()
        return Config.__instance

    def __init__(self):
        ConfigParser.RawConfigParser.__init__(self)
        self.__config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
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
