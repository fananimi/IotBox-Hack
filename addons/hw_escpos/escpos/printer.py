#!/usr/bin/python

from .escpos import Escpos
from .constants import (PAPER_FULL_CUT, DLE_EOT_PRINTER,
                        DLE_EOT_OFFLINE, DLE_EOT_ERROR, DLE_EOT_PAPER)
from devices.printer import Usb as UsbPrinter
from devices.printer.exceptions import TicketNotPrinted


class Usb(UsbPrinter, Escpos):
    """ Define USB printer """

    def __init__(self, idVendor, idProduct, interface=0, in_ep=None, out_ep=None):
        UsbPrinter.__init__(self, idVendor, idProduct, interface, in_ep, out_ep)
        self.errorText = "ERROR PRINTER\n\n\n\n\n\n" + PAPER_FULL_CUT

    def _raw(self, msg):
        """ Print any command sent in raw format """
        if len(msg) != self.device.write(self.out_ep, msg, self.interface, timeout=5000):
            self.device.write(self.out_ep, self.errorText, self.interface)
            raise TicketNotPrinted()

    def get_printer_status(self):
        status = {
            'printer': {},
            'offline': {},
            'error': {},
            'paper': {},
        }

        self.device.write(self.out_ep, DLE_EOT_PRINTER, self.interface)
        printer = self.__extract_status()
        self.device.write(self.out_ep, DLE_EOT_OFFLINE, self.interface)
        offline = self.__extract_status()
        self.device.write(self.out_ep, DLE_EOT_ERROR, self.interface)
        error = self.__extract_status()
        self.device.write(self.out_ep, DLE_EOT_PAPER, self.interface)
        paper = self.__extract_status()

        status['printer']['status_code'] = printer
        status['printer']['status_error'] = not ((printer & 147) == 18)
        status['printer']['online'] = not bool(printer & 8)
        status['printer']['recovery'] = bool(printer & 32)
        status['printer']['paper_feed_on'] = bool(printer & 64)
        status['printer']['drawer_pin_high'] = bool(printer & 4)
        status['offline']['status_code'] = offline
        status['offline']['status_error'] = not ((offline & 147) == 18)
        status['offline']['cover_open'] = bool(offline & 4)
        status['offline']['paper_feed_on'] = bool(offline & 8)
        status['offline']['paper'] = not bool(offline & 32)
        status['offline']['error'] = bool(offline & 64)
        status['error']['status_code'] = error
        status['error']['status_error'] = not ((error & 147) == 18)
        status['error']['recoverable'] = bool(error & 4)
        status['error']['autocutter'] = bool(error & 8)
        status['error']['unrecoverable'] = bool(error & 32)
        status['error']['auto_recoverable'] = not bool(error & 64)
        status['paper']['status_code'] = paper
        status['paper']['status_error'] = not ((paper & 147) == 18)
        status['paper']['near_end'] = bool(paper & 12)
        status['paper']['present'] = not bool(paper & 96)

        return status

    def __del__(self):
        """ Release USB interface """
        if self.device:
            self.close()
        self.device = None
