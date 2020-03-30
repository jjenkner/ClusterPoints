# -*- coding: utf-8 -*-
#-----------------------------------------------------------

from PyQt4.QtCore import QObject, SIGNAL, QVariant, QFile, QFileInfo
from PyQt4.QtGui import QDialog, QDialogButtonBox, QMessageBox
import ftools_utils
from qgis.core import QGis, QgsFeature, QgsVectorLayer, QgsVectorFileWriter, QgsFields, QgsField, QgsGeometry, QgsPoint
from qgis.core import QgsDistanceArea, QgsSimpleMarkerSymbolLayerV2, QgsMapLayerRegistry, QgsMessageLog 
from math import sqrt
from ui_frmCenter import Ui_Dialog
import os.path


class Dialog(QDialog, Ui_Dialog):

    def __init__(self, iface):
        QDialog.__init__(self, iface.mainWindow())
        self.iface = iface
        self.setupUi(self)
        self.updateUi()
        QObject.connect(self.toolOut, SIGNAL("clicked()"), self.outFile)
        QObject.connect(self.toolOut1, SIGNAL("clicked()"), self.outLineFile)
        QObject.connect(self.inShape, SIGNAL("currentIndexChanged(QString)"), self.update)
        self.buttonOk = self.buttonBox_2.button(QDialogButtonBox.Ok)
        self.progressBar.setValue(0)
        self.populateLayers()

    def populateLayers(self):
        layers = ftools_utils.getLayerNames([QGis.Point, QGis.Line, QGis.Polygon])
        self.inShape.blockSignals(True)
        self.inShape.clear()
        self.inShape.blockSignals(False)
        self.inShape.addItems(layers)

    def updateUi(self):
        self.setWindowTitle(self.tr("Cluster Centers"))
        self.sizeValue.setVisible(False)
        self.label_size.setVisible(False)
        self.resize(381, 100)

    def update(self, inputLayer):
        self.uniqueField.clear()
        self.changedLayer = ftools_utils.getVectorLayerByName(inputLayer)
        changedFieldName = [f.name() for f in ftools_utils.getFieldList(self.changedLayer)]
        if 'Cluster_ID' in changedFieldName:
            self.uniqueField.addItem(u'Cluster_ID')
        else:
            self.uniqueField.addItem(self.tr('Select Cluster ID Field'))
        for f in changedFieldName:
            if f <> 'Cluster_ID':
                self.uniqueField.addItem(unicode(f))

    def accept(self):
        self.buttonOk.setEnabled(False)
        if self.inShape.currentText() == "":
            QMessageBox.information(self, self.tr("Coordinate statistics"), self.tr("No input vector layer specified"))
        elif self.outShape.text() == "":
            QMessageBox.information(self, self.tr("Coordinate statistics"), self.tr("Please specify output shapefile"))
        else:
            inName = self.inShape.currentText()
            outPath = self.outShape.text()
            outPath1 = self.outLineShape.text()
            nCenter = self.compute(inName, self.sizeValue.value(), self.uniqueField.currentText())
            self.progressBar.setValue(50)
            if outPath1 <> "":
                message = self.centerlines(self.iface, unicode(outPath), unicode(self.uniqueField.currentText()),
					   unicode(inName),unicode(self.uniqueField.currentText()), unicode(outPath1),
					   self.addToCanvasCheck.isChecked())
                if message:
                    QMessageBox.information(self, self.tr("Coordinate statistics"), message)
            if self.addToCanvasCheck.isChecked():
                addCanvasCheck = self.addShapeToCanvasWithSingleSymbol(unicode(outPath))
                if not addCanvasCheck:
                    QMessageBox.warning(self, self.tr("Coordinate statistics"), self.tr("Error loading output shapefile:\n%s") % (unicode(outPath)))
                    self.populateLayers()
            else:
                QMessageBox.information(self, self.tr("Coordinate statistics"), self.tr("Created output shapefile:\n%s") % (unicode(outPath)))
            self.progressBar.setValue(100)
            QMessageBox.information(self, self.tr("Coordinate statistics"), self.tr("%s centers computed successfully") % str(nCenter))
            self.outShape.clear()
            self.outLineShape.clear()
            self.progressBar.setValue(0)
            self.buttonOk.setEnabled(True)

    def outFile(self):
        self.outShape.clear()
        (self.shapefileName, self.encoding) = ftools_utils.saveDialog(self)
        if self.shapefileName is None or self.encoding is None:
            return
        self.outShape.setText(self.shapefileName)

    def outLineFile(self):
        self.outLineShape.clear()
        (self.shapeLineFileName, self.encoding) = ftools_utils.saveDialog(self)
        if self.shapeLineFileName is None or self.encoding is None:
            return
        self.outLineShape.setText(self.shapeLineFileName)

    def compute(self, inName, times=1, uniqueField=""):
        vlayer = ftools_utils.getVectorLayerByName(inName)
        provider = vlayer.dataProvider()
        uniqueIndex = provider.fieldNameIndex(uniqueField)
        feat = QgsFeature()
        sRs = provider.crs()
        check = QFile(self.shapefileName)
        if check.exists():
            if not QgsVectorFileWriter.deleteShapeFile(self.shapefileName):
                return
        if uniqueIndex != -1:
            uniqueValues = ftools_utils.getUniqueValues(provider, int(uniqueIndex))
            single = False
        else:
            uniqueValues = [1]
            single = True
        fieldList = QgsFields()
        fieldList.append(QgsField("MEAN_X", QVariant.Double))
        fieldList.append(QgsField("MEAN_Y", QVariant.Double))
        fieldList.append(QgsField("Cluster_ID", QVariant.String))
        writer = QgsVectorFileWriter(self.shapefileName, self.encoding, fieldList, QGis.WKBPoint, sRs)
        outfeat = QgsFeature()
        outfeat.setFields(fieldList)
        points = []
        weights = []
        nFeat = provider.featureCount() * len(uniqueValues)
        nElement = 0
        self.progressBar.setValue(0)
        self.progressBar.setRange(0, nFeat)
        nCenter = 0
        for j in uniqueValues:
            cx = 0.00
            cy = 0.00
            points = []
            weights = []
            fit = provider.getFeatures()
            while fit.nextFeature(feat):
                nElement += 1
                self.progressBar.setValue(nElement)
                if single:
                    check = unicode(j).strip()
                else:
                    check = unicode(feat[uniqueIndex]).strip()
                if check == unicode(j).strip():
                    cx = 0.00
                    cy = 0.00
                    weight = 1.00
                    geom = QgsGeometry(feat.geometry())
                    geom = ftools_utils.extractPoints(geom)
                    for i in geom:
                        cx += i.x()
                        cy += i.y()
                        points.append(QgsPoint((cx / len(geom)), (cy / len(geom))))
                    weights.append(weight)
            sumWeight = sum(weights)
            cx = 0.00
            cy = 0.00
            item = 0
            for item, i in enumerate(points):
                cx += i.x() * weights[item]
                cy += i.y() * weights[item]
            cx = cx / sumWeight
            cy = cy / sumWeight
            meanPoint = QgsPoint(cx, cy)
            outfeat.setGeometry(QgsGeometry.fromPoint(meanPoint))
            outfeat.setAttribute(0, cx)
            outfeat.setAttribute(1, cy)
            outfeat.setAttribute(2, j)
            writer.addFeature(outfeat)
            nCenter += 1
        del writer
        return nCenter
            
    
    def addShapeToCanvasWithSingleSymbol(self,shapefile_path):
        file_info = QFileInfo(shapefile_path)
        if file_info.exists():
            layer_name = file_info.completeBaseName()
        else:
            return False
        vlayer_new = QgsVectorLayer(shapefile_path, layer_name, "ogr")
        if vlayer_new.isValid():
            properties = {'name': 'regular_star', 'size': '5.0', 'color': '0,255,0,255'}
            symbol_layer = QgsSimpleMarkerSymbolLayerV2.create(properties)
            vlayer_new.rendererV2().symbols()[0].changeSymbolLayer(0, symbol_layer)
            QgsMapLayerRegistry.instance().addMapLayers([vlayer_new])
            return True
        else:
            return False

    def find_layer(self,layer_name):
        # print "find_layer(" + str(layer_name) + ")"
        for name, search_layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
            # print unicode(search_layer.name()) + " ?= " + unicode(layer_name)
            if search_layer.name() == layer_name:
                return search_layer
        return None

    def centerlines(self, qgis, centername, centerattr, membername, memberattr, savename, addlayer):

        # Find layers
        if centername == membername:
            return "Same layer given for both centers and members"

        centerlayer = QgsVectorLayer(centername, centerattr, "ogr")
        centerfeatures = centerlayer.dataProvider().getFeatures()

        memberlayer = self.find_layer(membername)
        if memberlayer == None:
            return "Member Layer " + membername + " not found"

	    # Find Store ID attribute indices
        centerindex =  centerlayer.dataProvider().fieldNameIndex(centerattr)
        if centerindex < 0:
            return "Invalid name attribute: " + centerattr

        memberindex = memberlayer.dataProvider().fieldNameIndex(memberattr)
        if memberindex < 0:
            return "Invalid name attribute: " + memberattr

        # Create output file
        if len(savename) <= 0:
            return "No output filename given"

        if QFile(savename).exists():
            if not QgsVectorFileWriter.deleteShapeFile(savename):
                return "Failure deleting existing shapefile: " + savename

        outfields = memberlayer.dataProvider().fields()

        outfile1 = QgsVectorFileWriter(savename, "utf-8", outfields, QGis.WKBLineString, memberlayer.crs())

        if (outfile1.hasError() != QgsVectorFileWriter.NoError):
            return "Failure creating output shapefile: " + unicode(outfile1.errorMessage())

        # Scan member points
        linecount = 0
        for memberpoint in memberlayer.dataProvider().getFeatures():
            memberx = memberpoint.geometry().boundingBox().center().x()
            membery = memberpoint.geometry().boundingBox().center().y()
            memberid = unicode(memberpoint.attributes()[memberindex])
            centerfeatures.rewind()
            for centerpoint in centerfeatures:
                # centerid = unicode(centerpoint.attributes()[centerindex].toString())
                centerid = unicode(centerpoint.attributes()[centerindex])
                if centerid == memberid:
                    centerx = centerpoint.geometry().boundingBox().center().x()
                    centery = centerpoint.geometry().boundingBox().center().y()
                    #print "   Store " + str(centerx) + ", " + str(centery)

                    # Write line to the output file
                    outfeature = QgsFeature()
                    outfeature.setAttributes(memberpoint.attributes())

                    polyline = []
                    polyline.append(QgsPoint(memberx, membery))
                    polyline.append(QgsPoint(centerx, centery))
                    geometry = QgsGeometry()
                    outfeature.setGeometry(geometry.fromPolyline(polyline))
                    outfile1.addFeature(outfeature)
                    linecount = linecount + 1
                    break

        del memberlayer
        del centerlayer
        del outfile1

        if linecount <= 0:
            return "No member/center matches found to create lines"

        if addlayer:
            layer_name = os.path.basename(savename)
            layer_name = layer_name.split(".")
            layer_name = "".join(layer_name[0:-1])
            qgis.addVectorLayer(savename, layer_name, "ogr")

        return None
