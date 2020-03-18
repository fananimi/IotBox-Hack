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
        StateManager.getInstance().set_dialog(self)
        self.setupUi(self)
        self._register_thread()
        self._register_signal()

        # attribute registration
        self.printer_label_model = QtGui.QStandardItemModel()
        self.printer_thermal_model = QtGui.QStandardItemModel()

        # update status
        self._init_ui()

    # --------------------------------------------------------------------------------
    # ********************* All functions shown to user is here *********************|
    # --------------------------------------------------------------------------------
    def _init_ui(self):
        ws_port = StateManager.getInstance().web_service.port
        # set spinbox
        self.spnPort.setValue(ws_port)
        # set combobox
        self.cmbLabel.setModel(self.printer_label_model)
        self.cmbThermal.setModel(self.printer_thermal_model)
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
        self.cmbLabel.currentIndexChanged[int].connect(self.on_combobox_index_changed)
        self.cmbThermal.currentIndexChanged[int].connect(self.on_combobox_index_changed)

    # --------------------------------------------------------------------------------
    # ******************** Callback function for signals is here ********************|
    # --------------------------------------------------------------------------------
    @QtCore.pyqtSlot(int)
    def on_combobox_index_changed(self, row):
        cmbID = self.sender().objectName()
        if cmbID == 'cmbLabel':
            return
        if cmbID == 'cmbThermal':
            return

    def on_click_button(self):
        btnID = self.sender().objectName()
        if btnID == 'btnClose':
            self.hide()
            return
        if btnID == 'btnApply':
            cmbLabelIDx = self.cmbLabel.currentIndex()
            cmbThermalIDx = self.cmbThermal.currentIndex()
            selected_label_printer = self.printer_model.item(cmbLabelIDx).data().toPyObject()
            # selected_thermal_printer = self.printer_model.item(cmbThermalIDx).data().toPyObject()
            StateManager.getInstance().set_label_printer(selected_label_printer)
            return
        if btnID == 'btnReload':
            self._reload_printers()
            return

    # --------------------------------------------------------------------------------
    # *************************** Other function is here *************************** |
    # --------------------------------------------------------------------------------
    def _reload_printers(self):
        config = StateManager.getInstance()
        self.cmbLabel.clear()
        self.cmbThermal.clear()
        printers = [printer for printer in FindPrinters()]

        def add_to_model(type):
            _printers = printers
            _printers.append(config.get_printer(type))

            for printer in list(set(_printers)):
                _item = QtGui.QStandardItem(printer.description)
                _item.setData(printer)
                if type == StateManager.LABEL_PRINTER:
                    self.printer_label_model.appendRow(_item)
                if type == StateManager.THERMAL_PRINTER:
                    self.printer_thermal_model.appendRow(_item)

        add_to_model(StateManager.LABEL_PRINTER)
        add_to_model(StateManager.THERMAL_PRINTER)


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
