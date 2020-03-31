# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ClusterPoints
                                 A QGIS plugin
 Cluster geographical points into a predefined number of groups.
                              -------------------
        begin                : 2015-12-01
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Johannes Jenkner
        email                : jjenkner@web.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Johannes Jenkner'
__date__ = '2017-09-01'
__copyright__ = '(C) 2017 by Johannes Jenkner'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.core.ProcessingConfig import Setting, ProcessingConfig

from .algorithms.doCluster import doCluster
from CP_utils import CP_utils

from PyQt4.QtGui import QIcon
from os import path

class CP_provider(AlgorithmProvider):

    my_cluster_setting = 'my_cluster_setting'

    def __init__(self):
        AlgorithmProvider.__init__(self)

        self.activate = True

        self.alglist = [doCluster()]
        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        AlgorithmProvider.initializeSettings(self)

        ProcessingConfig.addSetting(Setting(
            self.getDescription(),
            CP_utils.CP_executable,
            self.tr('CP executable'),
            CP_utils.CP_path(),
            valuetype=Setting.FILE))

    def unload(self):
        AlgorithmProvider.unload(self)

        ProcessingConfig.removeSetting(CP_utils.CP_executable)

    def getName(self):
        return 'ClusterPoints'

    def getDescription(self):
        return 'Cluster Geographical Point Layer'

    def getIcon(self):
        return QIcon(path.dirname(__file__) + '/icon.png')

    def _loadAlgorithms(self):
        self.algs = self.alglist
