class Error(Exception):

    def __init__(self, msg, status=None):
        Exception.__init__(self)
        self.msg = msg
        self.resultcode = 1
        if status is not None:
            self.resultcode = status

    def __str__(self):
        return self.msg


class NoStatusError(Error):
    
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 70

    def __str__(self):
        return "Impossible to get status from the printer: " + str(self.msg)


class TicketNotPrinted(Error):

    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 80

    def __str__(self):
        return "A part of the ticket was not been printed: " + str(self.msg)


class NoDeviceError(Error):

    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 90

    def __str__(self):
        return str(self.msg)


class HandleDeviceError(Error):

    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 100

    def __str__(self):
        return str(self.msg)
