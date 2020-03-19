#!/usr/bin/python

import os
import usb.core
import usb.util

from zpl import *
from exceptions import *
from time import sleep


class Usb(Zpl):
    """ Define USB printer """

    def __init__(self, idVendor, idProduct, interface=0, in_ep=None, out_ep=None):
        """
        @param idVendor  : Vendor ID
        @param idProduct : Product ID
        @param interface : USB device interface
        @param in_ep     : Input end point
        @param out_ep    : Output end point
        """

        self.idVendor  = idVendor
        self.idProduct = idProduct
        self.interface = interface
        self.in_ep     = in_ep
        self.out_ep    = out_ep
        self.open()

    def open(self):
        """ Search device on USB tree and set is as escpos device """

        self.device = usb.core.find(idVendor=self.idVendor, idProduct=self.idProduct)
        if self.device is None:
            raise NoDeviceError()
        try:
            if os.name == 'posix' and self.device.is_kernel_driver_active(self.interface):
                self.device.detach_kernel_driver(self.interface)
            self.device.set_configuration()
            usb.util.claim_interface(self.device, self.interface)

            cfg = self.device.get_active_configuration()
            intf = cfg[(0,0)] # first interface
            if self.in_ep is None:
                # Attempt to detect IN/OUT endpoint addresses
                try:
                    is_IN = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
                    is_OUT = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
                    endpoint_in = usb.util.find_descriptor(intf, custom_match=is_IN)
                    endpoint_out = usb.util.find_descriptor(intf, custom_match=is_OUT)
                    self.in_ep = endpoint_in.bEndpointAddress
                    self.out_ep = endpoint_out.bEndpointAddress
                except usb.core.USBError:
                    # default values for officially supported printers
                    self.in_ep = 0x82
                    self.out_ep = 0x01

        except usb.core.USBError as e:
            raise HandleDeviceError(e)

    def close_on_posix(self):
        if not self.device.is_kernel_driver_active(self.interface):
            usb.util.release_interface(self.device, self.interface)
            self.device.attach_kernel_driver(self.interface)
            usb.util.dispose_resources(self.device)
        else:
            self.device = None

    def close_on_nt(self):
        if self.device:
            usb.util.release_interface(self.device, self.interface)
            usb.util.dispose_resources(self.device)
        self.device = None

    def close(self):
        i = 0
        while True:
            try:
                if not self.device:
                    return True

                if os.name == 'posix':
                    self.close_on_posix()
                if os.name == 'nt':
                    self.close_on_nt()
            except usb.core.USBError as e:
                i += 1
                if i > 10:
                    return False

            sleep(0.1)

    def _raw(self, msg):
        """ Print any command sent in raw format """
        if len(msg) != self.device.write(self.out_ep, msg, self.interface, timeout=5000):
            raise TicketNotPrinted()

    def __extract_status(self):
        maxiterate = 0
        rep = None
        while rep == None:
            maxiterate += 1
            if maxiterate > 10000:
                raise NoStatusError()
            r = self.device.read(self.in_ep, 20, self.interface).tolist()
            while len(r):
                rep = r.pop()
        return rep

    def get_printer_status(self):
        raise NotImplemented()

    def __del__(self):
        """ Release USB interface """
        if self.device:
            self.close()
        self.device = None
