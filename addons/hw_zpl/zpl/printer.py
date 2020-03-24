#!/usr/bin/python
from zpl.printer import Printer as ZPLUSB
from devices.printer import Usb as UsbPrinter

from .zpl import Zpl


class Usb(UsbPrinter, Zpl, ZPLUSB):
    """ Define USB printer """

    def __init__(self, idVendor, idProduct, timeout=0, in_ep=None, out_ep=None, *args, **kwargs):
        UsbPrinter.__init__(self, idVendor, idProduct, timeout, in_ep, out_ep)

    def send_job(self, zpl2):
        self._raw(zpl2)
