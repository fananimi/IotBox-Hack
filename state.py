import os
import sys
import logging
import configparser

from devices import Printer


# The Singleton Class to handle state of the application
class StateManager(configparser.RawConfigParser):
    ZPL_PRINTER = 0
    ESCPOS_PRINTER = 1

    is_frozen = False
    base_path = None
    config_file = None
    dialog = None
    __instance = None

    __printer_zpl = None
    __printer_escpos = None
    __web_service = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if StateManager.__instance is None:
            StateManager()
        return StateManager.__instance

    def __init__(self):
        configparser.RawConfigParser.__init__(self)

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
            except configparser.ParsingError:
                self._create_config()

            StateManager.__instance = self

    def _create_config(self):
        for section in self.sections():
            self._remove_section(section)
        with open(self.config_file, "w") as config_file:
            self.write(config_file)

    def _write_config(self, section, option, value):
        with open(self.config_file, "w") as config_file:
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
                    # in case we have validate_* function on class
                    validation_func = 'validate_%s' % option
                    if hasattr(instance, validation_func):
                        func = getattr(instance, validation_func)
                        # call the function
                        func(value)
                except (configparser.NoOptionError, ValueError):
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
                levelnames = [name[1] for name in logging._levelToName.items()]
                if value not in levelnames:
                    raise ValueError('level must be %s' % str(levelnames))

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
        if not self.__web_service:
            self.__web_service = self.__get_web_service()
        return self.__web_service

    def __get_web_service(self):
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

    @property
    def printer_zpl(self):
        if not self.__printer_zpl:
            self.__printer_zpl = self.__get_printer(StateManager.ZPL_PRINTER)
        return self.__printer_zpl

    @property
    def printer_escpos(self):
        if not self.__printer_escpos:
            self.__printer_escpos = self.__get_printer(StateManager.ESCPOS_PRINTER)
        return self.__printer_escpos

    def __get_printer(self, type):
        '''
        :param type: type of printer. ZPL_PRINTER|ESCPOS_PRINTER
        :return: Printer object
        '''
        if type not in [self.ZPL_PRINTER, self.ESCPOS_PRINTER]:
            return
        section_name = 'PRINTER_ZPL'
        if type == self.ESCPOS_PRINTER:
            section_name = 'PRINTER_ESCPOS'

        printer = Printer(0, 0, '')
        sections = {section_name: [
            ('product_id', int, 0),
            ('vendor_id', int, 0),
            ('description', str, '')
        ]}
        return self._build_config(printer, sections)

    def set_printer(self, type, printer):
        '''
        :param type: type of printer. ZPL_PRINTER|ESCPOS_PRINTER
        :param printer: Printer object
        :return: Printer Object
        '''
        if type not in [self.ZPL_PRINTER, self.ESCPOS_PRINTER]:
            return
        section_name = 'PRINTER_ZPL'
        if type == self.ESCPOS_PRINTER:
            section_name = 'PRINTER_ESCPOS'
        # remove section and then re-create
        self.remove_section(section_name)
        sections = {section_name: [
            ('product_id', int, printer.product_id),
            ('vendor_id', int, printer.vendor_id),
            ('description', str, printer.description)
        ]}
        self._build_config(printer, sections)
        if type == StateManager.ZPL_PRINTER:
            self.__printer_zpl = printer
        if type == StateManager.ESCPOS_PRINTER:
            self.__printer_escpos = printer
