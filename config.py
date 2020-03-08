# the singleton config class
class Config:
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if Config.__instance is None:
            Config()
        return Config.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if Config.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Config.__instance = self

    def get_service_port(self):
        raise NotImplemented()

    def get_log_level(self):
        raise NotImplemented()

    def get_log_name(self):
        raise NotImplemented()
