# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:/src/qgis/python/plugins/fTools/tools/frmMeanCoords.ui'
#
# Created: Sat Oct 24 00:57:14 2015
#      by: PyQt4 UI code generator 4.10.2
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
	Dialog.setWindowModality(QtCore.Qt.NonModal)
	Dialog.resize(374, 390)
	Dialog.setSizeGripEnabled(True)
	self.gridLayout = QtGui.QGridLayout(Dialog)
	self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
	self.vboxlayout = QtGui.QVBoxLayout()
	self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
	self.label_3 = QtGui.QLabel(Dialog)
	self.label_3.setObjectName(_fromUtf8("label_3"))
	self.vboxlayout.addWidget(self.label_3)
	self.inShape = QtGui.QComboBox(Dialog)
	self.inShape.setObjectName(_fromUtf8("inShape"))
	self.vboxlayout.addWidget(self.inShape)
	self.gridLayout.addLayout(self.vboxlayout, 0, 0, 1, 1)
	self.vboxlayout1 = QtGui.QVBoxLayout()
	self.vboxlayout1.setObjectName(_fromUtf8("vboxlayout1"))
	self.label_unique = QtGui.QLabel(Dialog)
	self.label_unique.setObjectName(_fromUtf8("label_unique"))
	self.vboxlayout1.addWidget(self.label_unique)
	self.uniqueField = QtGui.QComboBox(Dialog)
	self.uniqueField.setObjectName(_fromUtf8("uniqueField"))
	self.vboxlayout1.addWidget(self.uniqueField)
	self.gridLayout.addLayout(self.vboxlayout1, 1, 0, 1, 1)
	self.hboxlayout = QtGui.QHBoxLayout()
	self.hboxlayout.setObjectName(_fromUtf8("hboxlayout"))
	self.label_size = QtGui.QLabel(Dialog)
	self.label_size.setObjectName(_fromUtf8("label_size"))
	self.hboxlayout.addWidget(self.label_size)
	self.sizeValue = QtGui.QSpinBox(Dialog)
	self.sizeValue.setMinimum(1)
	self.sizeValue.setMaximum(3)
	self.sizeValue.setObjectName(_fromUtf8("sizeValue"))
	self.hboxlayout.addWidget(self.sizeValue)
	self.gridLayout.addLayout(self.hboxlayout, 2, 0, 1, 1)
	spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
	self.gridLayout.addItem(spacerItem, 3, 0, 1, 1)
	self.vboxlayout2 = QtGui.QVBoxLayout()
	self.vboxlayout2.setObjectName(_fromUtf8("vboxlayout2"))
	self.label_2 = QtGui.QLabel(Dialog)
	self.label_2.setObjectName(_fromUtf8("label_2"))
	self.vboxlayout2.addWidget(self.label_2)
	self.hboxlayout1 = QtGui.QHBoxLayout()
	self.hboxlayout1.setObjectName(_fromUtf8("hboxlayout1"))
	self.outShape = QtGui.QLineEdit(Dialog)
	self.outShape.setReadOnly(True)
	self.outShape.setObjectName(_fromUtf8("outShape"))
	self.hboxlayout1.addWidget(self.outShape)
	self.toolOut = QtGui.QPushButton(Dialog)
	self.toolOut.setObjectName(_fromUtf8("toolOut"))
	self.hboxlayout1.addWidget(self.toolOut)
	self.vboxlayout2.addLayout(self.hboxlayout1)
	self.gridLayout.addLayout(self.vboxlayout2, 4, 0, 1, 1)
	self.vboxlayout3 = QtGui.QVBoxLayout()
	self.vboxlayout3.setObjectName(_fromUtf8("vboxlayout3"))
	self.label_1 = QtGui.QLabel(Dialog)
	self.label_1.setObjectName(_fromUtf8("label_1"))
	self.vboxlayout3.addWidget(self.label_1)
	self.hboxlayout2 = QtGui.QHBoxLayout()
	self.hboxlayout2.setObjectName(_fromUtf8("hboxlayout2"))
	self.outLineShape = QtGui.QLineEdit(Dialog)
	self.outLineShape.setReadOnly(True)
	self.outLineShape.setObjectName(_fromUtf8("outLineShape"))
	self.hboxlayout2.addWidget(self.outLineShape)
	self.toolOut1 = QtGui.QPushButton(Dialog)
	self.toolOut1.setObjectName(_fromUtf8("toolOut1"))
	self.hboxlayout2.addWidget(self.toolOut1)
	self.vboxlayout3.addLayout(self.hboxlayout2)
	self.gridLayout.addLayout(self.vboxlayout3, 5, 0, 1, 1)
	self.addToCanvasCheck = QtGui.QCheckBox(Dialog)
	self.addToCanvasCheck.setChecked(True)
	self.addToCanvasCheck.setObjectName(_fromUtf8("addToCanvasCheck"))
	self.gridLayout.addWidget(self.addToCanvasCheck, 6, 0, 1, 1)
	self.horizontalLayout = QtGui.QHBoxLayout()
	self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
	self.progressBar = QtGui.QProgressBar(Dialog)
	self.progressBar.setProperty("value", 0)
	self.progressBar.setAlignment(QtCore.Qt.AlignCenter)
	self.progressBar.setTextVisible(True)
	self.progressBar.setObjectName(_fromUtf8("progressBar"))
	self.horizontalLayout.addWidget(self.progressBar)
	self.buttonBox_2 = QtGui.QDialogButtonBox(Dialog)
	self.buttonBox_2.setOrientation(QtCore.Qt.Horizontal)
	self.buttonBox_2.setStandardButtons(QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Ok)
	self.buttonBox_2.setObjectName(_fromUtf8("buttonBox_2"))
	self.horizontalLayout.addWidget(self.buttonBox_2)
	self.gridLayout.addLayout(self.horizontalLayout, 7, 0, 1, 1)

	self.retranslateUi(Dialog)
	QtCore.QObject.connect(self.buttonBox_2, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
	QtCore.QObject.connect(self.buttonBox_2, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.close)
	QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
	Dialog.setWindowTitle(_translate("Dialog", "Generate Centroids", None))
	self.label_3.setText(_translate("Dialog", "Input vector layer", None))
	self.label_unique.setText(_translate("Dialog", "Cluster ID field", None))
	self.label_size.setText(_translate("Dialog", "Number of standard deviations", None))
	self.sizeValue.setSuffix(_translate("Dialog", "Std. Dev.", None))
	self.label_2.setText(_translate("Dialog", "Output shapefile", None))
	self.toolOut.setText(_translate("Dialog", "Browse", None))
	self.label_1.setText(_translate("Dialog", "Optional line shapefile", None))
	self.toolOut1.setText(_translate("Dialog", "Browse", None))
	self.addToCanvasCheck.setText(_translate("Dialog", "Add result to canvas", None))

