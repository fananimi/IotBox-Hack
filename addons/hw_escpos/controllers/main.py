# -*- coding: utf-8 -*-
import time
import math
import logging
import netifaces
import traceback
import release
from threading import Lock
from queue import Queue
from PyQt5 import QtCore
import addons.hw_proxy.controllers.main as hw_proxy

try:
    import usb.core
except ImportError:
    usb = None

from devices import Printer

from odoo import http
from odoo.thread import Thread
from odoo.tools.translate import _
from state import StateManager

from ..escpos.printer import Usb

_logger = logging.getLogger(__name__)

# workaround https://bugs.launchpad.net/openobject-server/+bug/947231
# related to http://bugs.python.org/issue7980
from datetime import datetime

datetime.strptime('2012-01-01', '%Y-%m-%d')


class EscposDriver(Thread):
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

    def get_escpos_printer(self):
        printer = StateManager.getInstance().printer_escpos
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
            self.printer_status_signal.emit(str(StateManager.ESCPOS_PRINTER), str(printer.status))

        return printer_device

    def get_status(self):
        return self.status

    def open_cashbox(self, printer):
        printer.cashdraw(2)
        printer.cashdraw(5)

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
            _logger.error('ESC/POS Error: ' + message)
        elif status == 'disconnected' and message:
            _logger.warning('ESC/POS Device Disconnected: ' + message)

    def run(self):
        while True:
            reprint = False
            printer = None
            timestamp, task, data = self.queue.get(True)
            try:
                printer = self.get_escpos_printer()

                if printer:
                    if task == 'status':
                        # nothing todo
                        continue

                    # specific done bellow
                    if task == 'receipt':
                        if timestamp >= time.time() - 1 * 60 * 60:
                            self.print_receipt_body(printer, data)
                            printer.cut()
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
                        self.queue.put((timestamp, task, data))
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

    def print_status(self, eprint):
        eprint.text('\n')
        eprint.set(align='center', text_type='b', height=2, width=2)
        eprint.text('LinkBox Status\n')
        eprint.set(align='center')
        eprint.text("VERSION: %s\n" % release.version)
        eprint.text('________________________________\n')
        eprint.text('\n')

        ips = []
        for x in netifaces.interfaces():
            try:
                ips.append(netifaces.ifaddresses(x)[netifaces.AF_INET][0]['addr'])
            except TypeError:
                pass
            except KeyError:
                pass

        if not ips:
            eprint.set(align='center')
            eprint.text('ERROR: Could not connect to LAN.\n')
            eprint.text('\n')
            eprint.set(align='left')
            eprint.text('Please check that the LinkBox is\n')
            eprint.text('correctly connected  with a net-\n')
            eprint.text('work cable, that the LAN is set-\n')
            eprint.text('up  with  DHCP,  and  that  net-\n')
            eprint.text('work addresses are available.\n')
        else:
            eprint.set(align='center', font='b', text_type='normal')
            eprint.text('Homepage Addresses:\n\n')
            eprint.set(align='center')
            for ip in ips:
                homepage = 'http://%s:8080\n' % ip
                eprint.text(homepage)

        eprint.text('\n')
        eprint.cut()

    def print_receipt_body(self, eprint, receipt):

        def check(string):
            return string != True and bool(string) and string.strip()

        def price(amount):
            return ("{0:." + str(receipt['precision']['price']) + "f}").format(amount)

        def money(amount):
            return ("{0:." + str(receipt['precision']['money']) + "f}").format(amount)

        def quantity(amount):
            if math.floor(amount) != amount:
                return ("{0:." + str(receipt['precision']['quantity']) + "f}").format(amount)
            else:
                return str(amount)

        def printline(left, right='', width=40, ratio=0.5, indent=0):
            lwidth = int(width * ratio)
            rwidth = width - lwidth
            lwidth = lwidth - indent

            left = left[:lwidth]
            if len(left) != lwidth:
                left = left + ' ' * (lwidth - len(left))

            right = right[-rwidth:]
            if len(right) != rwidth:
                right = ' ' * (rwidth - len(right)) + right

            return ' ' * indent + left + right + '\n'

        def print_taxes():
            taxes = receipt['tax_details']
            for tax in taxes:
                eprint.text(printline(tax['tax']['name'], price(tax['amount']), width=40, ratio=0.6))

        # Receipt Header
        if receipt['company']['logo']:
            eprint.set(align='center')
            eprint.print_base64_image(receipt['company']['logo'])
            eprint.text('\n')
        else:
            eprint.set(align='center', text_type='b', height=2, width=2)
            eprint.text(receipt['company']['name'] + '\n')

        eprint.set(align='center', text_type='b')
        if check(receipt['company']['contact_address']):
            eprint.text(receipt['company']['contact_address'] + '\n')
        if check(receipt['company']['phone']):
            eprint.text('Tel:' + receipt['company']['phone'] + '\n')
        if check(receipt['company']['vat']):
            eprint.text('VAT:' + receipt['company']['vat'] + '\n')
        if check(receipt['company']['email']):
            eprint.text(receipt['company']['email'] + '\n')
        if check(receipt['company']['website']):
            eprint.text(receipt['company']['website'] + '\n')
        if check(receipt['header']):
            eprint.text(receipt['header'] + '\n')
        if check(receipt['cashier']):
            eprint.text('-' * 32 + '\n')
            eprint.text('Served by ' + receipt['cashier'] + '\n')

        # Orderlines
        eprint.text('\n\n')
        eprint.set(align='center')
        for line in receipt['orderlines']:
            pricestr = price(line['price_display'])
            if line['discount'] == 0 and line['unit_name'] == 'Unit(s)' and line['quantity'] == 1:
                eprint.text(printline(line['product_name'], pricestr, ratio=0.6))
            else:
                eprint.text(printline(line['product_name'], ratio=0.6))
                if line['discount'] != 0:
                    eprint.text(printline('Discount: ' + str(line['discount']) + '%', ratio=0.6, indent=2))
                if line['unit_name'] == 'Unit(s)':
                    eprint.text(
                        printline(quantity(line['quantity']) + ' x ' + price(line['price']), pricestr, ratio=0.6,
                                  indent=2))
                else:
                    eprint.text(printline(quantity(line['quantity']) + line['unit_name'] + ' x ' + price(line['price']),
                                          pricestr, ratio=0.6, indent=2))

        # Subtotal if the taxes are not included
        taxincluded = True
        if money(receipt['subtotal']) != money(receipt['total_with_tax']):
            eprint.text(printline('', '-------'));
            eprint.text(printline(_('Subtotal'), money(receipt['subtotal']), width=40, ratio=0.6))
            print_taxes()
            # eprint.text(printline(_('Taxes'),money(receipt['total_tax']),width=40, ratio=0.6))
            taxincluded = False

        # Total
        eprint.text(printline('', '-------'));
        eprint.set(align='center', height=2)
        eprint.text(printline(_('         TOTAL'), money(receipt['total_with_tax']), width=40, ratio=0.6))
        eprint.text('\n\n');

        # Paymentlines
        eprint.set(align='center')
        for line in receipt['paymentlines']:
            eprint.text(printline(line['journal'], money(line['amount']), ratio=0.6))

        eprint.text('\n');
        eprint.set(align='center', height=2)
        eprint.text(printline(_('        CHANGE'), money(receipt['change']), width=40, ratio=0.6))
        eprint.set(align='center')
        eprint.text('\n');

        # Extra Payment info
        if receipt['total_discount'] != 0:
            eprint.text(printline(_('Discounts'), money(receipt['total_discount']), width=40, ratio=0.6))
        if taxincluded:
            print_taxes()
            # eprint.text(printline(_('Taxes'),money(receipt['total_tax']),width=40, ratio=0.6))

        # Footer
        if check(receipt['footer']):
            eprint.text('\n' + receipt['footer'] + '\n\n')
        eprint.text(receipt['name'] + '\n')
        eprint.text(str(receipt['date']['date']).zfill(2)
                    + '/' + str(receipt['date']['month'] + 1).zfill(2)
                    + '/' + str(receipt['date']['year']).zfill(4)
                    + ' ' + str(receipt['date']['hour']).zfill(2)
                    + ':' + str(receipt['date']['minute']).zfill(2))


driver = EscposDriver()
driver.push_task('status')
hw_proxy.drivers['escpos'] = driver


class EscposProxy(hw_proxy.Proxy):

    @http.route('/hw_proxy/open_cashbox', type='json', auth='none', cors='*')
    def open_cashbox(self):
        _logger.info('ESC/POS: OPEN CASHBOX')
        driver.push_task('cashbox')

    @http.route('/hw_proxy/print_receipt', type='json', auth='none', cors='*')
    def print_receipt(self, receipt):
        _logger.info('ESC/POS: PRINT RECEIPT')
        driver.push_task('receipt', receipt)

    @http.route('/hw_proxy/print_xml_receipt', type='json', auth='none', cors='*')
    def print_xml_receipt(self, receipt):
        _logger.info('ESC/POS: PRINT XML RECEIPT')
        driver.push_task('xml_receipt', receipt)
