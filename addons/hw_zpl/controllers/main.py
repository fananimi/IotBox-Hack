# -*- coding: utf-8 -*-
import time
import logging
import traceback
from threading import Lock
from Queue import Queue
from PyQt4 import QtCore
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
        except NoDeviceError:
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
            self.emit(QtCore.SIGNAL("update_printer_status(QString, QString)"),
                      str(StateManager.ZPL_PRINTER),
                      str(printer.status))

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
            _logger.error('ZPL Error: ' + message)
        elif status == 'disconnected' and message:
            _logger.warning('ZPL Device Disconnected: ' + message)

    def run(self):
        while True:
            printer = None
            error = False
            try:
                timestamp, task, data = self.queue.get(True)

                try:
                    printer = self.get_zpl_printer()
                except Exception as e:
                    _logger.error(e)

                if printer:
                    if task == 'status':
                        # nothing todo
                        continue

                    # specific done bellow
                    if task == 'label':
                        if timestamp >= time.time() - 1 * 60 * 60:
                            pass
                    elif task == 'xml_label':
                        if timestamp >= time.time() - 1 * 60 * 60:
                            pass
                    elif task == 'printstatus':
                        self.print_status(printer)
                else:
                    if task != 'status':
                        # re-add job if exists
                        self.queue.put((timestamp, task, data))
            except NoDeviceError as e:
                error = True
                print "No device found %s" % str(e)
            except HandleDeviceError as e:
                error = True
                print "Impossible to handle the device due to previous error %s" % str(e)
            except TicketNotPrinted as e:
                error = True
                print "The ticket does not seems to have been fully printed %s" % str(e)
            except NoStatusError as e:
                error = True
                print "Impossible to get the status of the printer %s" % str(e)
            except Exception as e:
                error = True
                self.set_status('error', str(e))
                errmsg = str(e) + '\n' + '-' * 60 + '\n' + traceback.format_exc() + '-' * 60 + '\n'
                _logger.error(errmsg);
            finally:
                if error:
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

    @http.route('/hw_proxy/print_label', type='json', auth='none', cors='*')
    def print_label(self, label):
        _logger.info('ZPL: PRINT LABEL')
        driver.push_task('label', label)

    @http.route('/hw_proxy/print_xml_label', type='json', auth='none', cors='*')
    def print_xml_receipt(self, label):
        _logger.info('ZPL: PRINT XML LABEL')
        driver.push_task('xml_label', label)
