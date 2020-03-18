import logging
import usb.util


_logger = logging.getLogger(__name__)


class Printer(object):

    def __init__(self, idProduct, idVendor, description):
        self.id = '%d@%d' % (idProduct, idVendor)
        self.idVendor = idVendor
        self.idProduct = idProduct
        self.description = description


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
        self._printers = [Printer(0, 0, "")]
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
