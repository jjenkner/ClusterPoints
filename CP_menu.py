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

import os
import sys
import inspect

from processing.core.Processing import Processing
from CP_provider import CP_provider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class CP_menu:

    def __init__(self):
        self.provider = CP_provider()

    def initGui(self):
        Processing.addProvider(self.provider)

    def unload(self):
        Processing.removeProvider(self.provider)
