import os
import time
import logging
import usb.core
import usb.util

from devices.printer.exceptions import (NoDeviceError, NoStatusError,
                                        TicketNotPrinted, HandleDeviceError)

_logger = logging.getLogger(__name__)


class Printer(object):
    STATUS_DISCONNECTED = 0
    STATUS_CONNECTED = 1

    def __init__(self, product_id, vendor_id, description):
        self.product_id = product_id
        self.vendor_id = vendor_id
        self.description = description
        self.status = Printer.STATUS_DISCONNECTED
        self.print_test_request = False

    def get_status_display(self):
        if self.status == Printer.STATUS_DISCONNECTED:
            return 'Disconnected'
        if self.status == Printer.STATUS_CONNECTED:
            return 'Connected'

    @property
    def id(self):
        return '%d@%d' % (self.product_id, self.vendor_id)

    def __repr__(self):
        return self.description

    def __str__(self):
        return self.description

    def __eq__(self, other):
        return (
                self.__class__ == other.__class__ and
                self.id == other.id
        )

    def __hash__(self):
        return hash(self.id)


class FindPrinters(object):
    ''' Printer Iterator class '''

    def _get_connected_usb_printers(self):
        # printers can either define bDeviceClass=7, or they can define one of
        # their interfaces with bInterfaceClass=7. This class checks for both.
        class FindUsbClass(object):
            def __init__(self, usb_class=7):
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

        usb_devices = usb.core.find(find_all=True, custom_match=FindUsbClass())

        # if no printers are found after this step we will take the
        # first epson or star device we can find.
        # epson
        usb_devices += usb.core.find(find_all=True, idVendor=0x04b8)
        # star
        usb_devices += usb.core.find(find_all=True, idVendor=0x0519)

        printers = []
        for device in usb_devices:
            try:
                manufacture = usb.util.get_string(device, 256, device.iManufacturer)
                product = usb.util.get_string(device, 256, device.iProduct)
                description = '%s %s' % (manufacture, product)
            except Exception as e:
                _logger.error("Can not get printer description: %s" % (e.message or repr(e)))
                description = 'Unknown printer'

            # create printer instance
            printer = Printer(device.idProduct, device.idVendor, description)
            printers.append(printer)

        # finally we return all connected printers
        return printers

    # default constructors
    def __init__(self):
        self._current = 0
        self._printers = [Printer(0, 0, '')]
        self._printers += self._get_connected_usb_printers()
        self._length = len(self._printers)

    def __iter__(self):
        return self

    # To move to next element. In Python 3,
    # we should replace next with __next__
    def next(self):
        if self._current < self._length:
            printer = self._printers[self._current]
            self._current += 1
            return printer
        raise StopIteration


class Usb(object):
    """ Define USB printer """

    def __init__(self, idVendor, idProduct, interface=0, in_ep=None, out_ep=None):
        """
        @param idVendor  : Vendor ID
        @param idProduct : Product ID
        @param interface : USB device interface
        @param in_ep     : Input end point
        @param out_ep    : Output end point
        """

        self.idVendor = idVendor
        self.idProduct = idProduct
        self.interface = interface
        self.in_ep = in_ep
        self.out_ep = out_ep
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
            intf = cfg[(0, 0)]  # first interface
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

            time.sleep(0.1)

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
