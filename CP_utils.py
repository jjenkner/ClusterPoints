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
import subprocess

from processing.core.ProcessingLog import ProcessingLog
from processing.core.ProcessingConfig import ProcessingConfig


class CP_utils:

    CP_executable = 'CP_executable'

    @staticmethod
    def CP_path():
        filePath = ProcessingConfig.getSetting(CP_utils.CP_executable)
        return filePath if filePath is not None else ''

    @staticmethod
    def execute(command, progress):
        fused_command = ''.join(['"{}" '.format(c) for c in command])
        print fused_command

        loglines = []
        proc = subprocess.Popen(
            fused_command,
            shell=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            ).stdout
        for line in iter(proc.readline, ''):
            loglines.append(line)
            progress.setConsoleInfo(line)

        return loglines
