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
        import zpl
        import qrcode
        import time

        # for i in range(1, 30):
        i = 30
        width = 74
        height = 52
        dpmm = 8
        zero_pint = [4, 2]
        margin = 2

        l = zpl.Label(height, width, dpmm=dpmm)

        x = zero_pint[0]
        y = zero_pint[1]
        l.origin(x, y)
        # BORDER FULL
        l.draw_box((width * dpmm) - (2.5 * margin * dpmm), (height * dpmm) - (1.5 * margin * dpmm), thickness=3)
        l.endorigin()

        # TITLE
        l.origin(x, y + 1.5)
        l.write_text("INFORMASI SERVIS KENDARAAN", char_height=3, char_width=3, justification='C', line_width=width-5)
        l.endorigin()

        # HEADERR
        l.origin(x, y + 5)
        l.draw_box((width * dpmm) - (2.5 * margin * dpmm), 15 * dpmm, thickness=3)
        l.endorigin()

        # LEFT HEADERR
        l.origin(x, y + 6.5)
        l.write_text("OM JON", char_height=4, char_width=4, justification='C', line_width=16)
        l.endorigin()

        l.origin(x, y + 10.5)
        l.write_text("Family General", char_height=2, char_width=2, justification='C', line_width=15)
        l.endorigin()

        l.origin(x, y + 12.5)
        l.write_text("Service", char_height=2, char_width=2, justification='C', line_width=15)
        l.endorigin()

        l.origin(x, y + 15.5)
        l.write_text("085853575796", char_height=2.5, char_width=2.5, justification='C', line_width=16)
        l.endorigin()

        l.origin(x + 15, y + 5)
        l.draw_box(0, 15 * dpmm, thickness=3)
        l.endorigin()

        # # RIGHT HEADER
        l.origin(x + 15, y + 10)
        l.draw_box(54 * dpmm, 0, thickness=3)
        l.endorigin()

        l.origin(x + 17, y + 6.5)
        l.write_text("Customer :", char_height=2.5, char_width=2.5, justification='L')
        l.endorigin()

        l.origin(x + 15, y + 11.5)
        l.write_text("No Pol", char_height=2.5, char_width=2.5, justification='C', line_width=20)
        l.endorigin()

        l.origin(x + 35, y + 10)
        l.draw_box(0, 10 * dpmm, thickness=3)
        l.endorigin()

        l.origin(x + 35, y + 11.5)
        l.write_text("KM Mesin", char_height=2.5, char_width=2.5, justification='C', line_width=20)
        l.endorigin()

        l.origin(x + 55, y + 10)
        l.draw_box(0, 10 * dpmm, thickness=3)
        l.endorigin()

        l.origin(x + 55, y + 11.5)
        l.write_text("Tanggal", char_height=2.5, char_width=2.5, justification='C', line_width=15)
        l.endorigin()

        l.origin(x + 59.5, y + 15)
        l.draw_box(0, 5 * dpmm, thickness=3)
        l.endorigin()

        l.origin(x + 64.5, y + 15)
        l.draw_box(0, 5 * dpmm, thickness=3)
        l.endorigin()

        l.origin(x + 15, y + 15)
        l.draw_box(54 * dpmm, 0, thickness=3)
        l.endorigin()

        # BODY 1
        y += 20
        l.origin(x + 35, y)
        l.draw_box(0, 29 * dpmm, thickness=3)
        l.endorigin()

        l.origin(x, y + 1.5)
        l.write_text("STATUS SERVIS", char_height=2.5, char_width=2.5, justification='C', line_width=35)
        l.endorigin()

        l.origin(x + 35, y + 0.5)
        l.write_text("Ganti Oli Berikutnya", char_height=2, char_width=2, justification='C', line_width=35)
        l.endorigin()

        l.origin(x + 35, y + 2.5)
        l.write_text("KM Mesin", char_height=2.5, char_width=2.5, justification='C', line_width=20)
        l.endorigin()

        l.origin(x + 48, y + 2.5)
        l.write_text("/", char_height=2.5, char_width=2.5, justification='C', line_width=15)
        l.endorigin()

        l.origin(x + 55, y + 2.5)
        l.write_text("Tanggal", char_height=2.5, char_width=2.5, justification='C', line_width=15)
        l.endorigin()

        l.origin(x + 55, y + 5)
        l.draw_box(0, 5 * dpmm, thickness=3)
        l.endorigin()

        l.origin(x + 60, y + 5)
        l.draw_box(0, 5 * dpmm, thickness=3)
        l.endorigin()

        l.origin(x + 65, y + 5)
        l.draw_box(0, 5 * dpmm, thickness=3)
        l.endorigin()

        l.origin(x, y + 5)
        l.draw_box((width * dpmm) - (2.5 * margin * dpmm), 0, thickness=3)
        l.endorigin()

        l.origin(x + 35, y + 9.8)
        l.draw_box((34 * dpmm), 0, thickness=3)
        l.endorigin()


        # BODY 2
        y += 5
        l.origin(x + 1, y + 1.5)
        l.write_text("Oli Mesin :", char_height=2, char_width=2, justification='L', line_width=35)
        l.endorigin()

        l.origin(x, y + 4.75)
        l.draw_box((35 * dpmm), 0, thickness=3)
        l.endorigin()

        y += 4.75
        l.origin(x + 1, y + 1.5)
        l.write_text("Oli Perseneling :", char_height=2, char_width=2, justification='L', line_width=35)
        l.endorigin()

        l.origin(x, y + 4.75)
        l.draw_box((35 * dpmm), 0, thickness=3)
        l.endorigin()

        y += 4.75
        l.origin(x + 1, y + 1.5)
        l.write_text("Oli Gardan :", char_height=2, char_width=2, justification='L', line_width=35)
        l.endorigin()

        l.origin(x, y + 4.75)
        l.draw_box((35 * dpmm), 0, thickness=3)
        l.endorigin()

        y += 4.75
        l.origin(x + 1, y + 1.5)
        l.write_text("Filter Oli :", char_height=2, char_width=2, justification='L', line_width=35)
        l.endorigin()

        l.origin(x, y + 4.75)
        l.draw_box((35 * dpmm), 0, thickness=3)
        l.endorigin()

        y += 4.75
        l.origin(x + 1, y + 1.5)
        l.write_text("Minyak Rem :", char_height=2, char_width=2, justification='L', line_width=35)
        l.endorigin()

        # QR CODE
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=4,
        )
        data = "WO-" + str(i).rjust(5, "0")
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        image_width = 25
        l.origin(x + 40, y - 17.25)
        image_height = l.write_graphic(
            img,
            image_width)
        l.endorigin()

        l.origin(x + 40, y - 15)
        l.write_text(data, char_height=2, char_width=2, justification='C', line_width=19, orientation='B', font='1')
        l.endorigin()

    # x = 4
    # y = 2
    # for c in range(1, 9):
    #     l.origin(x, y)
    #     l.write_text(str(c), char_height=2, char_width=2, justification='C', line_width=10)
    #     l.endorigin()
    #
    #     l.origin(x, y)
    #     l.draw_box(1, height * dpmm, thickness=3)
    #     l.endorigin()
    #     x += 10
    #
    # # LINE OF PRODUCT DESCRIPTION
    # x = 4
    # y = 2
    # for r in range(1, 7):
    #     l.origin(x, y)
    #     l.write_text(str(r), char_height=2, char_width=2, justification='C', line_width=10)
    #     l.endorigin()
    #
    #     l.origin(x, y)
    #     l.draw_box(width * dpmm, 1, thickness=3)
    #     l.endorigin()
    #     y += 10

        eprint.send_job(l.dumpZPL())
            # time.sleep(2)


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
