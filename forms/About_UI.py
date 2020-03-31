# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'forms/About_UI.ui'
#
# Created: Sun Nov 20 09:49:31 2016
#      by: PyQt4 UI code generator 4.11.3
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

class Ui_CP_About_form(object):
    def setupUi(self, CP_About_form):
        CP_About_form.setObjectName(_fromUtf8("CP_About_form"))
        CP_About_form.setWindowModality(QtCore.Qt.ApplicationModal)
        CP_About_form.setEnabled(True)
        CP_About_form.resize(422, 426)
        CP_About_form.setMouseTracking(False)
        self.buttonBox = QtGui.QDialogButtonBox(CP_About_form)
        self.buttonBox.setGeometry(QtCore.QRect(10, 390, 160, 26))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.label = QtGui.QLabel(CP_About_form)
        self.label.setGeometry(QtCore.QRect(30, 10, 111, 51))
        font = QtGui.QFont()
        font.setPointSize(25)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.line = QtGui.QFrame(CP_About_form)
        self.line.setGeometry(QtCore.QRect(10, 60, 381, 16))
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.textBrowser = QtGui.QTextBrowser(CP_About_form)
        self.textBrowser.setGeometry(QtCore.QRect(10, 90, 391, 261))
        self.textBrowser.setObjectName(_fromUtf8("textBrowser"))

        self.retranslateUi(CP_About_form)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), CP_About_form.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), CP_About_form.reject)
        QtCore.QMetaObject.connectSlotsByName(CP_About_form)

    def retranslateUi(self, CP_About_form):
        CP_About_form.setWindowTitle(_translate("CP_About_form", "About BA-tools", None))
        self.label.setText(_translate("CP_About_form", "About", None))
        self.textBrowser.setHtml(_translate("CP_About_form", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Business Analyst Tools</span> is a set of Python plugins for manipulating vectordata in QGIS, specifically designed to solve problems related to geomarketing. </p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Some functions were availible in other Qgis-Plugins before so we took the liberty to include some tools (with minor changes) from the talented developers  Michael Minn(mmqgis), Carson Farmer(ftools) and  Alessandro Pasotti(GeoCoding).</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">The plugin allows you to: </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">geocode single addresses and geocoding from CSV,</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">buffering, </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">creating grid lines,</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">clustering data, </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">calculating customer density, </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">distance from specific centers and their catchment areas.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">This plugin was created during the project phase of a Gis-Analyst course in Berlin (Geo-sys).</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">author:Juliane B., Johannes J., Bennet J., Sebastian O</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">email:Juliane.Bonness@web.de ,<span style=\" font-size:8pt;\">jjenkner@web.de,</span> bjuhls@hotmail.com, <span style=\" font-size:8pt;\">abloofen@web.de</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))

