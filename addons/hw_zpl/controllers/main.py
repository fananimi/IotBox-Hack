# -*- coding: utf-8 -*-
import logging
import time
import traceback

try:
    from .. zpl import *
    from .. zpl.exceptions import *
    from .. zpl.printer import Usb
except ImportError:
    zpl = printer = None

from odoo.thread import Thread
from threading import Lock
from Queue import Queue

try:
    import usb.core
except ImportError:
    usb = None

from odoo import http
import addons.hw_proxy.controllers.main as hw_proxy

from state import StateManager
from devices import Printer

_logger = logging.getLogger(__name__)

# workaround https://bugs.launchpad.net/openobject-server/+bug/947231
# related to http://bugs.python.org/issue7980
from datetime import datetime
datetime.strptime('2012-01-01', '%Y-%m-%d')


class ZPLDriver(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.queue = Queue()
        self.lock  = Lock()
        self.status = {'status':'connecting', 'messages':[]}

    def lockedstart(self):
        with self.lock:
            if not self.isAlive():
                self.daemon = True
                self.start()

    def get_zpl_printer(self):
        printer = StateManager.getInstance().printer_zpl
        try:
            printer_device = Usb(printer.vendor_id, printer.product_id)
            self.set_status(
                'connected',
                "Connected to %s (in=0x%02x,out=0x%02x)" % (printer.description,
                                                            printer_device.in_ep,
                                                            printer_device.out_ep)
            )
            printer.status = Printer.STATUS_CONNECTED
            return printer_device
        except NoDeviceError:
            printer.status = Printer.STATUS_DISCONNECTED
            self.set_status('disconnected','Printer Not Found')

        return None

    def get_status(self):
        return self.status

    def set_status(self, status, message = None):
        _logger.info(status+' : '+ (message or 'no message'))
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
            _logger.error('ZPL Error: '+message)
        elif status == 'disconnected' and message:
            _logger.warning('ZPL Device Disconnected: '+message)

    def run(self):
        printer = None
        if not zpl:
            _logger.error('ZPL cannot initialize, please verify system dependencies.')
            return
        while True:
            error = True
            try:
                timestamp, task, data = self.queue.get(True)

                printer = None
                try:
                    printer = self.get_zpl_printer()
                except Exception as e:
                    _logger.error(e)

                if printer == None:
                    if task != 'status':
                        self.queue.put((timestamp,task,data))
                    error = False
                    time.sleep(1)
                    continue
                elif task == 'label':
                    if timestamp >= time.time() - 1 * 60 * 60:
                        pass
                elif task == 'xml_label':
                    if timestamp >= time.time() - 1 * 60 * 60:
                        pass
                elif task == 'printstatus':
                    pass
                elif task == 'status':
                    pass
                error = False

            except NoDeviceError as e:
                print "No device found %s" %str(e)
            except HandleDeviceError as e:
                print "Impossible to handle the device due to previous error %s" % str(e)
            except TicketNotPrinted as e:
                print "The ticket does not seems to have been fully printed %s" % str(e)
            except NoStatusError as e:
                print "Impossible to get the status of the printer %s" % str(e)
            except Exception as e:
                self.set_status('error', str(e))
                errmsg = str(e) + '\n' + '-'*60+'\n' + traceback.format_exc() + '-'*60 + '\n'
                _logger.error(errmsg);
            finally:
                if error:
                    self.queue.put((timestamp, task, data))
                if printer:
                    printer.close()
                self.push_task('status')

    def push_task(self,task, data = None):
        self.lockedstart()
        self.queue.put((time.time(),task,data))

    def print_status(self, printer):
        pass

    def print_label(self,eprint,receipt):
        pass

    def print_label_xml(self,eprint,receipt):
        pass


driver = ZPLDriver()
driver.push_task('status')
driver.push_task('printstatus')
hw_proxy.drivers['zpl'] = driver


class ZplProxy(hw_proxy.Proxy):

    @http.route('/hw_proxy/print_label', type='json', auth='none', cors='*')
    def print_receipt(self, receipt):
        _logger.info('ZPL: PRINT LABEL')
        driver.push_task('label',receipt)

    @http.route('/hw_proxy/print_xml_label', type='json', auth='none', cors='*')
    def print_xml_receipt(self, receipt):
        _logger.info('ZPL: PRINT XML LABEL')
        driver.push_task('xml_label',receipt)
