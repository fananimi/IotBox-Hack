#!/usr/bin/python

from .zpl import Zpl
from devices.printer import Usb as UsbPrinter


class Usb(UsbPrinter, Zpl):
    """ Define USB printer """

    def __init__(self, idVendor, idProduct, interface=0, in_ep=None, out_ep=None):
        UsbPrinter.__init__(self, idVendor, idProduct, interface, in_ep, out_ep)
