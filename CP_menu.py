# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CP_menu
				 A QGIS plugin
 ClusterPoints plugin version for QGIS
			      -------------------
	begin		     : 2015-12-01
	copyright	     : (C) 2016 by Johannes Jenkner
	email		     : jjenkner@web.de
 ***************************************************************************/

/***************************************************************************
 *									   *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or	   *
 *   (at your option) any later version.				   *
 *									   *
 ***************************************************************************/
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import os.path
import sys
import webbrowser

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/libs")
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")

import doCluster
import doCenter

class cp_menu:
    CLP_MENU = u"&Cluster Points"

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

    def initGui(self):
        cluster_icon = QIcon(os.path.dirname(__file__)+"/icons/cluster.png")
        center_icon = QIcon(os.path.dirname(__file__)+"/icons/center_gravity.png")
        about_icon = QIcon(os.path.dirname(__file__)+"/icons/about.png")
	help_icon = QIcon(os.path.dirname(__file__)+"/icons/help.png")

        self.clusteraction = QAction(cluster_icon, u"Clustering",self.iface.mainWindow())
        self.clusteraction.triggered.connect(self.doCluster)

        self.centeraction = QAction(center_icon, u"Cluster Centers",self.iface.mainWindow())
        self.centeraction.triggered.connect(self.doCenter)

        self.aboutaction = QAction(about_icon, u"About",self.iface.mainWindow())
        self.aboutaction.triggered.connect(self.doAbout)

	self.helpaction = QAction(help_icon, u"Help",self.iface.mainWindow())
	self.helpaction.triggered.connect(self.doHelp)

        self.iface.addPluginToMenu(self.CLP_MENU, self.clusteraction)
        self.iface.addPluginToMenu(self.CLP_MENU, self.centeraction)
        self.iface.addPluginToMenu(self.CLP_MENU, self.aboutaction)
	self.iface.addPluginToMenu(self.CLP_MENU, self.helpaction)

    def unload(self):
        self.iface.removePluginMenu(self.CLP_MENU, self.clusteraction)
        self.iface.removePluginMenu(self.CLP_MENU, self.centeraction)
        self.iface.removePluginMenu(self.CLP_MENU, self.aboutaction)
	self.iface.removePluginMenu(self.CLP_MENU, self.helpaction)

    def doCluster(self):
        dialog = doCluster.Dialog(self.iface)
        dialog.exec_()

    def doCenter(self):
        dialog = doCenter.Dialog(self.iface)
        dialog.exec_()
	
    def doAbout(self):
        dialog = CP_About_Dialog(self.iface)
        dialog.exec_()

    def doHelp(self):
        webbrowser.open("file://" + os.path.dirname(__file__) + "/README.html")


#----------------------- About------------------------------------------
from ui_frmAbout import *

class CP_About_Dialog(QDialog, Ui_CP_About_form):
    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)

