import sys
import signal
import logging

from PyQt4 import QtCore, QtGui

from addons.hw_proxy.controllers.main import drivers
from odoo.thread import WebThread
from odoo.ui import SystemTrayIcon
from static.images import xpm
from ui.main import Ui_Dialog

from state import StateManager
from printer import FindPrinters


def setup_log():
    state = StateManager.getInstance()
    logformat = '%(asctime)s - %(funcName)s - %(levelname)s: %(message)s'

    if state.is_frozen is False:
        logging.basicConfig(
            format=logformat,
            level=state.log.level,
            handlers=[logging.StreamHandler()]
        )
    else:
        logging.basicConfig(
            format=logformat,
            level=state.log.level,
            filename=state.get_log().filename,
            filemode='a'
        )


class LinkBox(QtGui.QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        super(LinkBox, self).__init__(parent)
        self.state = StateManager.getInstance()
        self.state.set_dialog(self)
        self.setupUi(self)
        self._register_thread()
        self._register_signal()

        # attribute registration
        self.printer_zpl_model = QtGui.QStandardItemModel()
        self.printer_escpos_model = QtGui.QStandardItemModel()

        # update status
        self._init_ui()

    # --------------------------------------------------------------------------------
    # ********************* All functions shown to user is here *********************|
    # --------------------------------------------------------------------------------
    def _init_ui(self):
        ws_port = self.state.web_service.port
        # set spinbox
        self.spnPort.setValue(ws_port)
        # set combobox
        self.cmbZPL.setModel(self.printer_zpl_model)
        self.cmbESCPOS.setModel(self.printer_escpos_model)
        # set status
        self.txtPort.setText('%d' % ws_port)
        # trigger printers
        self._reload_printers()

    # --------------------------------------------------------------------------------
    # ****************** All threads must register on this section ******************|
    # --------------------------------------------------------------------------------
    def _register_thread(self):
        self.web_thread = WebThread()
        self.web_thread.start()
        # run all driver
        for key in drivers.keys():
            drivers[key].start()

    # --------------------------------------------------------------------------------
    # ****************** All signals must register on this section ******************|
    # --------------------------------------------------------------------------------
    def _register_signal(self):
        self.btnClose.clicked.connect(self.on_click_button)
        self.btnApply.clicked.connect(self.on_click_button)
        self.btnReload.clicked.connect(self.on_click_button)
        self.cmbZPL.currentIndexChanged[int].connect(self.on_combobox_index_changed)
        self.cmbESCPOS.currentIndexChanged[int].connect(self.on_combobox_index_changed)

    # --------------------------------------------------------------------------------
    # ******************** Callback function for signals is here ********************|
    # --------------------------------------------------------------------------------
    @QtCore.pyqtSlot(int)
    def on_combobox_index_changed(self, row):
        cmbID = self.sender().objectName()
        if cmbID == 'cmbESCPOS':
            pass
        if cmbID == 'cmbZPL':
            pass
        self.changed()

    def on_click_button(self):
        btnID = self.sender().objectName()
        if btnID == 'btnClose':
            self.hide()
            return
        if btnID == 'btnApply':
            self._apply_config()
            return
        if btnID == 'btnReload':
            self._reload_printers()
            return

    # --------------------------------------------------------------------------------
    # *************************** Other function is here *************************** |
    # --------------------------------------------------------------------------------
    def _apply_config(self):
        for printer_type in [StateManager.ZPL_PRINTER, StateManager.ESCPOS_PRINTER]:
            printer = None
            if printer_type == StateManager.ZPL_PRINTER:
                printer = self.get_combobox_object(self.cmbZPL, self.printer_zpl_model)
            if printer_type == StateManager.ESCPOS_PRINTER:
                printer = self.get_combobox_object(self.cmbESCPOS, self.printer_escpos_model)

            if printer_type in [StateManager.ZPL_PRINTER, StateManager.ESCPOS_PRINTER] and printer:
                self.state.set_printer(printer_type, printer)

        self.btnApply.setEnabled(False)
        self._reload_printers()

    def _reload_printers(self):
        self.cmbZPL.clear()
        self.cmbESCPOS.clear()
        printers = [printer for printer in FindPrinters()]
        for printer_type in [StateManager.ZPL_PRINTER, StateManager.ESCPOS_PRINTER]:
            _printers = [self.state.get_printer(printer_type)]
            for printer in printers:
                if printer not in _printers:
                    _printers.append(printer)

            for printer in _printers:
                _item = QtGui.QStandardItem(printer.description)
                _item.setData(printer)
                if printer_type == StateManager.ZPL_PRINTER:
                    self.printer_zpl_model.appendRow(_item)
                if printer_type == StateManager.ESCPOS_PRINTER:
                    self.printer_escpos_model.appendRow(_item)

    def get_combobox_object(self, combobox, model):
        index = combobox.currentIndex()
        if index >= 0:
            return model.item(index).data().toPyObject()

    def changed(self):
        change_statuses = []

        for printer_type in [StateManager.ZPL_PRINTER, StateManager.ESCPOS_PRINTER]:
            ui = None
            config = None
            if printer_type == StateManager.ZPL_PRINTER:
                ui = self.get_combobox_object(self.cmbZPL, self.printer_zpl_model)
                config = self.state.get_printer(StateManager.ZPL_PRINTER)
            if printer_type == StateManager.ESCPOS_PRINTER:
                ui = self.get_combobox_object(self.cmbESCPOS, self.printer_escpos_model)
                config = self.state.get_printer(StateManager.ESCPOS_PRINTER)

            if ui and config:
                change_statuses.append(ui == config)

        self.btnApply.setEnabled(False in change_statuses)


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtGui.QApplication(sys.argv)

    # show system try icon
    systemTryIcon = SystemTrayIcon(QtGui.QIcon(QtGui.QPixmap(xpm.icon_64)))
    systemTryIcon.show()
    # ui dialog
    dialog = LinkBox()
    dialog.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    setup_log()
    main()
