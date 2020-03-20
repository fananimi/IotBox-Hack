from devices.printer.exceptions import Error


class BarcodeTypeError(Error):

    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 10

    def __str__(self):
        return "No Barcode type is defined"


class BarcodeSizeError(Error):

    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 20

    def __str__(self):
        return "Barcode size is out of range"


class BarcodeCodeError(Error):

    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 30

    def __str__(self):
        return "Code was not supplied"


class ImageSizeError(Error):

    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 40

    def __str__(self):
        return "Image height is longer than 255px and can't be printed"


class TextError(Error):

    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 50

    def __str__(self):
        return "Text string must be supplied to the text() method"


class CashDrawerError(Error):

    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 60

    def __str__(self):
        return "Valid pin must be set to send pulse"
