# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/Main.ui'
#
# Created by: PyQt4 UI code generator 4.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(790, 530)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.frame = QtGui.QFrame(Dialog)
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.formLayout = QtGui.QFormLayout(self.frame)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.groupBox = QtGui.QGroupBox(self.frame)
        self.groupBox.setMinimumSize(QtCore.QSize(0, 0))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.formLayout_3 = QtGui.QFormLayout(self.groupBox)
        self.formLayout_3.setObjectName(_fromUtf8("formLayout_3"))
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setMinimumSize(QtCore.QSize(50, 0))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout_3.setWidget(0, QtGui.QFormLayout.LabelRole, self.label_2)
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setMinimumSize(QtCore.QSize(50, 0))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout_3.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_3)
        self.comboBox_2 = QtGui.QComboBox(self.groupBox)
        self.comboBox_2.setMinimumSize(QtCore.QSize(250, 0))
        self.comboBox_2.setObjectName(_fromUtf8("comboBox_2"))
        self.formLayout_3.setWidget(1, QtGui.QFormLayout.FieldRole, self.comboBox_2)
        self.comboBox = QtGui.QComboBox(self.groupBox)
        self.comboBox.setMinimumSize(QtCore.QSize(250, 0))
        self.comboBox.setObjectName(_fromUtf8("comboBox"))
        self.formLayout_3.setWidget(0, QtGui.QFormLayout.FieldRole, self.comboBox)
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.groupBox)
        self.groupBox_2 = QtGui.QGroupBox(self.frame)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.formLayout_2 = QtGui.QFormLayout(self.groupBox_2)
        self.formLayout_2.setObjectName(_fromUtf8("formLayout_2"))
        self.label = QtGui.QLabel(self.groupBox_2)
        self.label.setMinimumSize(QtCore.QSize(50, 0))
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.lineEdit = QtGui.QLineEdit(self.groupBox_2)
        self.lineEdit.setMinimumSize(QtCore.QSize(200, 0))
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.FieldRole, self.lineEdit)
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.groupBox_2)
        self.verticalLayout.addWidget(self.frame)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.groupBox.setTitle(_translate("Dialog", "Printer", None))
        self.label_2.setText(_translate("Dialog", "Label", None))
        self.label_3.setText(_translate("Dialog", "POS", None))
        self.groupBox_2.setTitle(_translate("Dialog", "Sevices", None))
        self.label.setText(_translate("Dialog", "Port", None))

