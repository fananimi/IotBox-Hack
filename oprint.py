import sys
import time
import json
import usb

from escpos.printer import Usb
from bottle import response, request, route, run, hook
from tinydb import TinyDB, Query

from PyQt4.QtCore import QThread, SIGNAL
from PyQt4.QtGui import QApplication, QMainWindow


class Printer:

    VENDOR      = 'vendor'
    PRODUCT     = 'product'
    NAME        = 'name'
    CONNECTED   = 'connected'
    SELECTED    = 'selected'

    def __init__(self):
        self.db = TinyDB('printer.json')

    @staticmethod
    def keys():
        return [Printer.VENDOR, Printer.PRODUCT, Printer.NAME, Printer.CONNECTED, Printer.SELECTED]

    def bundle_data(self, vendor_id, product_id, **kwargs):
        data = {Printer.VENDOR: vendor_id, Printer.PRODUCT: product_id}
        for key, value in kwargs.items():
            if not data.has_key(key):
                data[key] = value
        return data

    def all(self):
        return self.db.all()

    def purge_db(self):
        self.db.purge()

    def remove_device(self, vendor_id, product_id):
        return self.db.remove((Query()[Printer.VENDOR] == vendor_id) & (Query()[Printer.PRODUCT] == product_id))

    def find_device(self, vendor_id, product_id):
        try:
            return self.db.search((Query()[Printer.VENDOR] == vendor_id) & (Query()[Printer.PRODUCT] == product_id))[0]
        except IndexError:
            return {}

    def add_device(self, vendor_id, product_id, **kwargs):
        data = self.bundle_data(vendor_id, product_id, **kwargs)
        for key in Printer.keys():
            if key not in data.keys():
                data[key] = self.get_default_value(key)
        self.db.insert(data)
        return self.find_device(vendor_id, product_id)

    def update_device(self, vendor_id, product_id, **kwargs):
        data = self.bundle_data(vendor_id, product_id, **kwargs)
        # remove unique data for querying
        data.pop(Printer.VENDOR)
        data.pop(Printer.PRODUCT)

        self.db.update(data, (Query()[Printer.VENDOR] == vendor_id) & (Query()[Printer.PRODUCT] == product_id))
        return self.find_device(vendor_id, product_id)

    def get_or_create_device(self, vendor_id, product_id, **kwargs):
        record = self.find_device(vendor_id, product_id)
        if not record:
            # create new record
            record = self.add_device(vendor_id, product_id, **kwargs)

        data = self.bundle_data(vendor_id, product_id, **kwargs)
        validities = []
        for key in Printer.keys():
            if record.has_key(key) and data.has_key(key):
                validities.append(record[key] == data[key])
        if not all(validities):
            # update record
            record = self.update_device(vendor_id, product_id, **kwargs)

        return record

    def get_default_value(self, key):
        default_value = {
            Printer.NAME: "Unknown printer",
            Printer.CONNECTED: True,
            Printer.SELECTED: False
        }
        try:
            value = default_value[key]
            return value
        except KeyError:
            pass

    def get_default_printer(self):
        try:
            return self.db.search(Query()[Printer.SELECTED] == True)[0]
        except IndexError:
            return {}

    def set_default_printer(self, vendor_id, product_id):
        self.db.update(
            {Printer.SELECTED: False},
            Query()[Printer.SELECTED] == True
        )
        self.db.update(
            {Printer.SELECTED: True},
            (Query()[Printer.VENDOR] == vendor_id) & (Query()[Printer.PRODUCT] == product_id)
        )


class PrintingThread(QThread):

    def __init__(self, parent=None):
        super(PrintingThread, self).__init__(parent)
        self.printer = Printer()

    def check_listed_device(self):
        for record in self.printer.all():
            connected = False
            try:
                usb = Usb(record[Printer.VENDOR], record[Printer.PRODUCT])
                connected = True
                del usb
            except AttributeError:
                pass
            finally:
                if record[Printer.CONNECTED] != connected:
                    # update record
                    self.printer.update_device(record[Printer.VENDOR], record[Printer.PRODUCT], connected=connected)

    def get_connected_usb_devices(self):

        # printers can either define bDeviceClass=7, or they can define one of
        # their interfaces with bInterfaceClass=7. This class checks for both.
        class FindUsbClass(object):
            def __init__(self, usb_class):
                self._class = usb_class

            def __call__(self, device):
                # first, let's check the device
                if device.bDeviceClass == self._class:
                    return True
                # transverse all devices and look through their interfaces to
                # find a matching class
                for cfg in device:
                    intf = usb.util.find_descriptor(cfg, bInterfaceClass=self._class)

                    if intf is not None:
                        return True

                return False

        # check listed printers
        self.check_listed_device()

        # find connected printer
        connected = []
        printers = usb.core.find(find_all=True, custom_match=FindUsbClass(7))

        '''
        # if no printers are found after this step we will take the
        # first epson or star device we can find.
        # epson
        if not printers:
            printers = usb.core.find(find_all=True, idVendor=0x04b8)
        # star
        if not printers:
            printers = usb.core.find(find_all=True, idVendor=0x0519)
        '''

        for printer in printers:
            vendor = product = name = None
            try:
                vendor  = usb.util.get_string(printer, printer.iManufacturer)
                product = usb.util.get_string(printer, printer.iProduct)
                name    = vendor + " " + product
            except Exception as e:
                name = 'Unknown printer'

            if all([vendor, product, name]):
                data = self.printer.get_or_create_device(printer.idVendor, printer.idProduct, name=name, connected=True)
                connected.append(data)

        if not self.printer.get_default_printer():
            for printer in self.printer.all():
                self.printer.set_default_printer(printer[Printer.VENDOR], printer[Printer.PRODUCT])
                break
        return connected

    def run(self):
        self.printer.purge_db()
        while True:
            self.get_connected_usb_devices()
            time.sleep(5)


class WebThread(QThread):


    @staticmethod
    @hook('after_request')
    def enable_cors():
        '''Add headers to enable CORS'''
        response.headers['Access-Control-Allow-Origin'] = "*"
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept, X-Debug-Mode'

    @staticmethod
    @route('/', method='OPTIONS')
    @route('/<path:path>', method='OPTIONS')
    def options_handler(path=None):
        return

    @staticmethod
    @route('/hw_proxy/hello')
    def hello():
        return "ping"

    @staticmethod
    @route('/hw_proxy/handshake', method='POST')
    def handshake():
        content_type = 'application/json'
        response.content_type = content_type

        data = {
            "jsonrpc": "2.0",
        }

        if request.content_type == content_type:
            data["id"] = request.json.get('id')
            data["result"] = True
        else:
            data["result"] = False
            response.status = 400

        return json.dumps(data)

    @staticmethod
    @route('/hw_proxy/status_json', method='POST')
    def status_json():
        content_type = 'application/json'
        response.content_type = content_type

        data = {
            "jsonrpc": "2.0",
        }

        if request.content_type == content_type:
            data["id"] = request.json.get('id')
        else:
            data["result"] = False
            response.status = 400

        return json.dumps(data)

    def run(self):
        run(host='localhost', port=8080, debug=True)


class OPrint(QMainWindow):

    def __init__(self, parent=None):
        super(OPrint, self).__init__(parent)

        # web service
        self.web_thread = WebThread()
        self.web_thread.start()

        # printing service
        self.print_thread = PrintingThread()
        self.print_thread.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OPrint()
    window.show()
    app.exec_()
