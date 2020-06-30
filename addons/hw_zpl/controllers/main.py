# -*- coding: utf-8 -*-
import time
import logging
import traceback
from threading import Lock
from queue import Queue
from PyQt5 import QtCore
import addons.hw_proxy.controllers.main as hw_proxy

try:
    import usb.core
except ImportError:
    usb = None

from devices import Printer
from devices.printer.exceptions import (NoDeviceError, NoStatusError,
                                        TicketNotPrinted, HandleDeviceError)
from odoo import http
from odoo.thread import Thread
from state import StateManager

from ..zpl.printer import Usb

_logger = logging.getLogger(__name__)

# workaround https://bugs.launchpad.net/openobject-server/+bug/947231
# related to http://bugs.python.org/issue7980
from datetime import datetime

datetime.strptime('2012-01-01', '%Y-%m-%d')


class ZPLDriver(Thread):
    printer_status_signal = QtCore.pyqtSignal(str, str)

    def __init__(self):
        Thread.__init__(self)
        self.queue = Queue()
        self.lock = Lock()
        self.status = {'status': 'connecting', 'messages': []}
        self.current_printer_status = None

    def lockedstart(self):
        with self.lock:
            if not self.isAlive():
                self.daemon = True
                self.start()

    def get_zpl_printer(self):
        printer = StateManager.getInstance().printer_zpl
        # print test request coming out
        if printer.print_test_request:
            self.push_task('printstatus')
            printer.print_test_request = False

        printer_device = None
        try:
            printer_device = Usb(printer.vendor_id, printer.product_id)
            printer.status = Printer.STATUS_CONNECTED
            return printer_device
        except usb.core.USBError:
            printer.status = Printer.STATUS_DISCONNECTED
        finally:
            if printer.status != self.current_printer_status:
                self.current_printer_status = printer.status
                if printer_device:
                    self.set_status(
                        'connected',
                        "Connected to %s (in=0x%02x,out=0x%02x)" % (printer.description,
                                                                    printer_device.in_ep,
                                                                    printer_device.out_ep)
                    )
                else:
                    self.set_status('disconnected', 'Printer Not Found')

            # update status in GUI
            self.printer_status_signal.emit(str(StateManager.ZPL_PRINTER), str(printer.status))

        return printer_device

    def get_status(self):
        return self.status

    def set_status(self, status, message=None):
        _logger.info(status + ' : ' + (message or 'no message'))
        if status == self.status['status']:
            if message != None and (len(self.status['messages']) == 0 or message != self.status['messages'][-1]):
                self.status['messages'].append(message)
        else:
            self.status['status'] = status
            if message:
                self.status['messages'] = [message]
            else:
                self.status['messages'] = []

        if status == 'error' and message:
            _logger.error('ZPL Error: ' + message)
        elif status == 'disconnected' and message:
            _logger.warning('ZPL Device Disconnected: ' + message)

    def run(self):
        while True:
            reprint = False
            printer = None
            timestamp, task, data = self.queue.get(True)
            try:
                printer = self.get_zpl_printer()

                if printer:
                    if task == 'status':
                        # nothing todo
                        continue

                    # specific done bellow
                    if task == 'label':
                        if timestamp >= time.time() - 1 * 60 * 60:
                            self.print_label(printer, data)
                    elif task == 'xml_receipt':
                        if timestamp >= time.time() - 1 * 60 * 60:
                            printer.receipt(data)
                    elif task == 'cashbox':
                        if timestamp >= time.time() - 12:
                            self.open_cashbox(printer)
                    elif task == 'printstatus':
                        self.print_status(printer)
                else:
                    if task != 'status':
                        # re-add job if exists
                        reprint = True
            except usb.core.USBError:
                reprint = True
            except Exception as e:
                self.set_status('error', str(e))
                errmsg = str(e) + '\n' + '-' * 60 + '\n' + traceback.format_exc() + '-' * 60 + '\n'
                _logger.error(errmsg)
            finally:
                if reprint:
                    self.queue.put((timestamp, task, data))
                if printer:
                    printer.close()
                # check status after complete
                self.push_task('status')
                time.sleep(0.25)

    def push_task(self, task, data=None):
        self.lockedstart()
        self.queue.put((time.time(), task, data))

    def print_label(self, eprint, zpl):
        eprint.send_job(zpl)

    def print_status(self, eprint):
        eprint.send_job('''^XA
^FO150,40^BY3
^BCN,110,Y,N,N
^FD123456^FS
^XZ ''')
        pass



driver = ZPLDriver()
driver.push_task('status')
hw_proxy.drivers['zpl'] = driver


class ZPLProxy(hw_proxy.Proxy):

    def get_zpl(self, data):
        import qrcode
        import zpl

        l = zpl.Label(72, 50)
        margin = 3
        x = y = margin

        # BORDER
        l.origin(x, y)
        l.draw_box(525, 360, thickness=3)
        l.endorigin()

        # PRODUCT DESCRIPTION
        y += 1
        l.origin(margin, y)
        l.write_text(data['name'], char_height=2, char_width=2, justification='C', line_width=42)
        l.endorigin()

        # LINE OF PRODUCT DESCRIPTION
        y += 2
        l.origin(x, y)
        l.draw_box(525, 1, thickness=3)
        l.endorigin()

        # QR CODE
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=4,
        )
        qr.add_data(data['code'])
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        image_width = 25
        y = int((l.height - image_width)/4) - 4
        l.origin(1.75, y)
        image_height = l.write_graphic(
            img,
            image_width)
        l.endorigin()

        # QR CODE TEXT
        y += image_width - margin
        l.origin(margin, y)
        l.write_text(data['code'], char_height=2, char_width=2, justification='C', line_width=22)
        l.endorigin()

        # RIGHT LINE
        l.origin(image_height, margin * 2)
        l.draw_box(1, 322, thickness=3)
        l.endorigin()

        # UoM
        y = 10
        x = image_width + 2
        l.origin(x, y)
        l.write_text("UoM:", char_height=2, char_width=2, justification='L', line_width=20)
        l.endorigin()

        x += 5
        y -= 2
        l.origin(x, y)
        l.write_text(data['uom'], char_height=5, char_width=5, justification='L', line_width=20)
        l.endorigin()

        x = image_width
        y += 5
        l.origin(x, y)
        l.draw_box(260, 1, thickness=3)
        l.endorigin()

        # LOCATIONS
        y += 2
        x = image_width + 2
        l.origin(x, y)
        l.write_text("Locations:", char_height=2, char_width=2, justification='L', line_width=20)
        l.endorigin()

        locations = data['locations']
        for location in locations:
            y += 4
            x = image_width + 2
            l.origin(x, y)
            l.write_text(location, char_height=3, char_width=3, justification='L', line_width=20)
            l.endorigin()

        return l.dumpZPL()

    @http.route('/hw_proxy/print_label', type='json', auth='none', cors='*')
    def print_label(self, data):
        _logger.info('ZPL: PRINT LABEL : ' + str(data))
        driver.push_task('label', self.get_zpl(data))

    @http.route('/hw_proxy/print_xml_label', type='json', auth='none', cors='*')
    def print_xml_receipt(self, label):
        _logger.info('ZPL: PRINT XML LABEL')
        driver.push_task('xml_label', label)
