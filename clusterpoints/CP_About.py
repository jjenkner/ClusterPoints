# --------------------------------------------------------
# Business Analyst
# email: bjuhls@hotmail.com;juliane.bonness@web.de; abloofen@web.de
# beta-version
# --------------------------------------------------------

import csv
import os.path
import operator

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

from MA_library import *
from urllib2 import URLError
import processing

import time
import math
import sys, os



from functools import reduce

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")	  # defining path for external forms
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/libs")	  # defining path for external forms
import ftools_utils

# --------------------------------------------------------
# MA_geocode_web_service - Geocode using Google Maps (Jule)
# --------------------------------------------------------
from Geocode_web_service_UI import *   #  import of external form

class MA_geocode_web_service_dialog(QDialog, Ui_MA_geocode_web_service_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse_infile, SIGNAL("clicked()"), self.browse_infile_dialog)
		QObject.connect(self.browse_shapefile, SIGNAL("clicked()"), self.browse_shapefile_dialog)
		QObject.connect(self.browse_notfound, SIGNAL("clicked()"), self.browse_notfound_dialog)
		QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)
		self.shapefilename.setText(MA_temp_file_name(".shp"))
		self.notfoundfilename.setText(os.getcwd() + "/notfound.csv")

		self.servicename.clear()
		self.servicename.addItems(["Google Maps", "OpenStreetMap / Nominatim"])
		self.servicename.setCurrentIndex(0)



        def browse_notfound_dialog(self):

    		newname = QFileDialog.getSaveFileName(None, "Not Found List Output File",
    		self.notfoundfilename.displayText(), "CSV File (*.csv *.txt)")
    		if newname != None:
    					self.notfoundfilename.setText(newname)

    	def browse_shapefile_dialog(self):
    		newname = QFileDialog.getSaveFileName(None, "Output Shapefile",
    		self.shapefilename.displayText(), "Shapefile (*.shp)")
    		if newname != None:
    			self.shapefilename.setText(newname)

	def run(self):
		csvname = unicode(self.infilename.displayText()).strip()
		shapefilename = unicode(self.shapefilename.displayText())
		notfoundfile = self.notfoundfilename.displayText()
		service = unicode(self.servicename.currentText()).strip()

		fields = [unicode(self.addressfield.currentText()).strip(),
			  unicode(self.cityfield.currentText()).strip(),
			  unicode(self.statefield.currentText()).strip(),
			  unicode(self.countryfield.currentText()).strip()]

		for x in range(0, len(fields)):
			if fields[x] == "(none)":
				fields[x] = ""

		# print csvname + "," + "," + shapefilename
		message = MA_geocode_web_service(self.iface, csvname,
			shapefilename, notfoundfile, fields, service, 1)

		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Geocode Goodle", message)

        def browse_infile_dialog(self):
		newname = QFileDialog.getOpenFileName(None, "Address CSV Input File",
			self.infilename.displayText(), "CSV File (*.csv *.txt)")

                if newname:

			if len(newname) > 4:
				prefix = newname[:len(newname) - 4]
				self.shapefilename.setText(prefix + ".shp")
			else:
				self.shapefilename.setText(MA_temp_file_name(".shp"))


			combolist = [self.addressfield, self.cityfield, self.statefield, self.countryfield]
			for box in combolist:
				box.clear()
				box.addItem("(none)")
				box.setCurrentIndex(0)

			header = MA_read_csv_header(self.iface, newname)
			if header == None:
				return

			for index in range(0, len(header)):
				field = header[index]
				for box in combolist:
					box.addItem(field)

				if field.lower().find("addr") >= 0:
					self.addressfield.setCurrentIndex(index + 1)
				if field.lower().find("street") >= 0:
					self.addressfield.setCurrentIndex(index + 1)
				if field.lower().find("city") >= 0:
					self.cityfield.setCurrentIndex(index + 1)
				if field.lower().find("state") >= 0:
					self.statefield.setCurrentIndex(index + 1)
				if field.lower() == "st":
					self.statefield.setCurrentIndex(index + 1)
				if field.lower().find("province") >= 0:
					self.statefield.setCurrentIndex(index + 1)
				if field.lower().find("country") >= 0:
					self.countryfield.setCurrentIndex(index + 1)

                	self.infilename.setText(newname)

        def browse_notfound_dialog(self):
		newname = QFileDialog.getSaveFileName(None, "Not Found List Output File",
			self.notfoundfilename.displayText(), "CSV File (*.csv *.txt)")
                if newname != None:
                	self.notfoundfilename.setText(newname)

        def browse_shapefile_dialog(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile",
			self.shapefilename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.shapefilename.setText(newname)

	def run(self):
		csvname = unicode(self.infilename.displayText()).strip()
		shapefilename = unicode(self.shapefilename.displayText())
		notfoundfile = self.notfoundfilename.displayText()
		service = unicode(self.servicename.currentText()).strip()

		fields = [unicode(self.addressfield.currentText()).strip(),
			  unicode(self.cityfield.currentText()).strip(),
			  unicode(self.statefield.currentText()).strip(),
			  unicode(self.countryfield.currentText()).strip()]

		for x in range(0, len(fields)):
			if fields[x] == "(none)":
				fields[x] = ""

		# print csvname + "," + "," + shapefilename
		message = MA_geocode_web_service(self.iface, csvname,
			shapefilename, notfoundfile, fields, service, 1)

		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Geocode Goodle", message)
# --------------------------------------------------------
#	Utility Functions
# --------------------------------------------------------

def MA_read_csv_header(qgis, filename):
	try:
		infile = open(filename, 'r')
	except Exception as e:
		QMessageBox.information(qgis.mainWindow(),
			"Input CSV File", "Failure opening " + filename + ": " + unicode(e))
		return None

	try:
		dialect = csv.Sniffer().sniff(infile.read(4096))
	except:
		QMessageBox.information(qgis.mainWindow(), "Input CSV File",
			"Bad CSV file - verify that your delimiters are consistent");
		return None

	infile.seek(0)
	reader = csv.reader(infile, dialect)

	# Decode from UTF-8 characters because csv.reader can only handle 8-bit characters
	header = reader.next()
	header = [unicode(field, "utf-8") for field in header]

	del reader
	del infile

	if len(header) <= 0:
		QMessageBox.information(qgis.mainWindow(), "Input CSV File",
			filename + " does not appear to be a CSV file")
		return None

	return header

def MA_load_combo_box_with_vector_layers(qgis, combo_box, set_selected):
	for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
		if layer.type() == QgsMapLayer.VectorLayer:
			combo_box.addItem(layer.name())

	# Parameter can be boolean "True" to use current selection in layer pane
	# or can be a str/unicode name

	if (type(set_selected) != bool):
		combo_index = combo_box.findText(set_selected)
		if combo_index >= 0:
			combo_box.setCurrentIndex(combo_index)
			return;

	for index, layer in enumerate(qgis.legendInterface().selectedLayers()):
		combo_index = combo_box.findText(layer.name())
		if combo_index >= 0:
			combo_box.setCurrentIndex(combo_index)
			break;



def MA_temp_file_name(suffix):
	preferred = os.getcwd() + "/temp" + suffix
	if not os.path.isfile(preferred):
		return preferred

	for x in range(2, 10):
		name = os.getcwd() + "/temp" + unicode(x) + suffix
		if not os.path.isfile(name):
			return name

	return preferred




#----------------------------------
# single address geocoder
#---------------------------------


from PlaceSelection_UI import *

class PlaceSelectionDialog(QtGui.QDialog, Ui_PlaceSelectionDialog):
	  def __init__(self):
		QtGui.QDialog.__init__(self)
		self.setupUi(self)

from GeoCoding_UI import *

class GeoCoding(QtGui.QDialog, Ui_GeoCoding):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.canvas = iface.mapCanvas()
		self.setupUi(self)
		QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)
		try:
			for layer in iface.mapCanvas().layers():
				if layer.dataProvider().geometryType() == QGis.WKBPoint or \
					layer.dataProvider().geometryType()  == QGis.WKBPoint25D or \
					layer.dataProvider().geometryType()  ==  QGis.WKBMultiPoint or \
					layer.dataProvider().geometryType()  == QGis.WKBMultiPoint25D:
						self.LayerComboBox.addItem(layer.name())
		except:
			pass


		self.layerid = ''
		libpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'libs')
		if not libpath in sys.path:
			# Makes sure geopy is imported from current path
			sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '/libs'))


	def run(self):
		chk = self.check_settings()
		if len(chk) :
			QMessageBox.information(self.iface.mainWindow(),QCoreApplication.translate('GeoCoding', "GeoCoding plugin error"), chk)
			return

		#Import geopy
		geocoder = self.get_geocoder_instance()
		result = geocoder.geocode(unicode(self.address.text()).encode('utf-8'), exactly_one=False)

		places = {}
		for place, point in result:
			places[place] = point


		if len(places) == 1:
			self.process_point(place, point)
		else:
			all_str = QCoreApplication.translate('GeoCoding', 'All')
			place_dlg = PlaceSelectionDialog()
			place_dlg.placesComboBox.addItem(all_str)
			place_dlg.placesComboBox.addItems(places.keys())
			place_dlg.show()
			result = place_dlg.exec_()
			if result == 1 :
				if place_dlg.placesComboBox.currentText() == all_str:
					for place in places:
						self.process_point(place, places[place])
				else:
					point = places[unicode(place_dlg.placesComboBox.currentText())]
					self.process_point(place_dlg.placesComboBox.currentText(), point)
		return


	def process_point(self, place, point):

		"""
		Transforms the point and save
		"""
		# lon lat and transform
		point = QgsPoint(point[1], point[0])
		point = pointFromWGS84(point, self.iface.mapCanvas().mapRenderer().destinationCrs())
		x = point[0]
		y = point[1]

		# Zoom Scale to set canvas extent
		scale = int(self.ZoomScale.text())
		if not scale:
			scale = float(self.canvas.scale())

		rect = QgsRectangle(  \
						x - scale \
						, y - scale \
						, x + scale \
						, y + scale)

		self.canvas.setExtent(rect)
		self.canvas.refresh()

		# save point
		self.save_point(point, unicode(place))



	def save_point(self, point, address):
		qDebug('Saving point ' + str(point[1])  + ' ' + str(point[0]))

		if self.LayerCheckBox.checkState() == QtCore.Qt.Unchecked:


			# create layer with same CRS as map canvas
			Layer_add = QgsVectorLayer("Point", "Geocode_address_result", "memory")
			QgsMapLayerRegistry.instance().addMapLayer(Layer_add)
			pr = Layer_add.dataProvider()
			fieldList = pr.fields()
			layerid = Layer_add.id()

			Layer_add.setCrs(self.canvas.mapRenderer().destinationCrs())
			Layer_add.startEditing()

				# activate if you want labels on
##				label = self.layer.label()
##				label.setLabelField(QgsLabel.Text, 0)
##				self.layer.enableLabels(True)

			#add feature and 'address' field
			fieldname = 'address'
			fieldList.append(QgsField(fieldname, QVariant.String))
			pr.addAttributes([QgsField(fieldname, QVariant.String)])
			fet = QgsFeature(fieldList)
			fet.setGeometry(QgsGeometry.fromPoint(point))
			#fet.setFields(fieldList, True)

			fet[fieldname]= address
			#pr.addFeatures([fet])
			Layer_add.commitChanges()

				# update layer's extent
			Layer_add.updateExtents()
			self.canvas.refresh()

		else:
			# find layer that is selected in LayerComboBox
			def find_layer(layer_name):
				for name, search_layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
					if search_layer.name() == layer_name:
						return search_layer

			Layer_add = find_layer(self.LayerComboBox.currentText())
			#layerid = Layer_add.id()

			if Layer_add == None:
				Layer_add = QgsVectorLayer("Point", "Geocode_address_result", "memory")
				QgsMapLayerRegistry.instance().addMapLayer(Layer_add)
				layerid = Layer_add.id()
				Layer_add.startEditing()

				pr = Layer_add.dataProvider()
				fieldList = pr.fields()
				fieldname = 'address'

				#add feature and 'address' field
				fieldList.append(QgsField(fieldname, QVariant.String))
				pr.addAttributes([QgsField(fieldname, QVariant.String)])
				fet = QgsFeature(fieldList)
				fet.setGeometry(QgsGeometry.fromPoint(point))
				fet.setFields(fieldList, True)


				fet[fieldname]= address
				#pr.addFeatures([fet])
				Layer_add.commitChanges()

				# update layer's extent
				Layer_add.updateExtents()
				self.canvas.refresh()

			else:
				Layer_add = find_layer(self.LayerComboBox.currentText())
				pr = Layer_add.dataProvider()
				fieldList = pr.fields()
				fieldname = 'address'
				fet = QgsFeature(fieldList)
				Layer_add.startEditing()

				# so that just one address field is inserted
				if fieldname not in [field.name() for field in fieldList]:
					fieldList.append(QgsField(fieldname, QVariant.String))
					pr.addAttributes([QgsField(fieldname, QVariant.String)])
				else:
					pass

				#add feature and 'address' field
                fet = QgsFeature(fieldList)
                fet.setGeometry(QgsGeometry.fromPoint(point))
                fet.setFields(fieldList, True)


                fet[fieldname]= address
                pr.addFeatures([fet])
                Layer_add.commitChanges()

				# update layer's extent
                Layer_add.updateExtents()
                self.canvas.refresh()




	def get_geocoder_instance(self):
		geocoder_class = unicode(self.geocoderComboBox.currentText())

		if geocoder_class == 'Google':
			geocoder_class = 'GoogleV3'
			try:
				self.geocoders
			except:
				from geopy import geocoders
				self.geocoders = geocoders
			geocoder = getattr(self.geocoders, geocoder_class)
			return geocoder()
		else:
			geocoder_class = 'Nominatim'
			try :
				self.geocoders
			except:
				from geopy import geocoders
				self.geocoders = geocoders
			geocoder = getattr(self.geocoders, geocoder_class)
			return geocoder()



	def check_settings (self):
		p = QgsProject.instance()
		error = ''

		if not self.iface.mapCanvas().hasCrsTransformEnabled() and self.iface.mapCanvas().mapRenderer().destinationCrs().authid() != 'EPSG:4326':
			error = QCoreApplication.translate('GeoCoding', "On-the-fly reprojection must be enabled if the destination CRS is not EPSG:4326. Please enable on-the-fly reprojection.")

		return error




# GRID____________________________________________(bennet)

# --------------------------------------------------------
#    MA_grid - Grid creation plugin
# --------------------------------------------------------

# Crid-shapefile Creation (Bennet)
#_______________________________________________


from Create_Grids_UI import *

class MA_grid_dialog(QDialog, Ui_MA_grid_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.hspacing, SIGNAL("textEdited(QString)"), self.hspacing_changed)
		QObject.connect(self.vspacing, SIGNAL("textEdited(QString)"), self.vspacing_changed)
		QObject.connect(self.gridtype, SIGNAL("currentIndexChanged(QString)"), self.gridtype_changed)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
		QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		QMessageBox.information(self, self.tr("Achtung"), self.tr("Der Layer Extent wird von dem aktiven ProjetkLayer genommen"))

		self.crs = QgsCoordinateReferenceSystem()
		self.crs.createFromProj4("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
		extent = QgsRectangle (-10.0, -10.0, 10.0, 20.0)

		# Done as exception handler to make backward compatible from "crs" functions new to qgis 1.7 and 2.0
		# if (self.iface.mapCanvas() != None) and (self.iface.mapCanvas().mapRenderer() != None):
		try:
			self.crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
			extent = self.iface.mapCanvas().mapRenderer().extent()

		#elif self.iface.activeLayer() != None:
		except:
			try:
				extent = self.iface.activeLayer().extent()
				self.crs = self.iface.activeLayer().crs()
			except:
				extent = extent

		centerx = MA_round((extent.xMinimum() + extent.xMaximum()) / 2, 4)
		centery = MA_round((extent.yMinimum() + extent.yMaximum()) / 2, 4)

		#self.xtype.setCurrentIndex(0);
		#self.ytype.setCurrentIndex(0);
		self.xMin.setText(unicode(centerx))
		self.yMin.setText(unicode(centery))

		if self.iface.activeLayer() == None:
			QMessageBox.information(self, self.tr("HALLOOO????"), self.tr("Erstmal n layer in dein projetk packen, sonst geht das nich!"))

		else:
			extent = self.iface.activeLayer().extent()


		#extent_new = self.inShape().extent()
		width = MA_round((extent.xMaximum() - extent.xMinimum()), 4)
		height = MA_round((extent.yMaximum() - extent.yMinimum()), 4)

		#width = MA_round(extent.width(), 4)
		#height = MA_round(extent.height(), 4)

		self.width.setText(unicode(width))
		self.height.setText(unicode(height))

		hspacing = 1
		if width > 0:
			hspacing = width / 10.0

		vspacing = 1
		if height > 0:
			vspacing = height / 10.0

		self.hspacing.setText(unicode(hspacing))
		self.vspacing.setText(unicode(vspacing))

		self.gridtype.addItem("Rectangle (line)")
		self.gridtype.addItem("Rectangle (polygon)")
		self.gridtype.addItem("Diamond (polygon)")
		self.gridtype.addItem("Hexagon (polygon)")
		self.gridtype.setCurrentIndex(0)

		self.filename.setText(os.getcwd() + "/grid.shp")
		self.populateLayers()
		QObject.connect(self.btnUpdate, SIGNAL("clicked()"), self.updateLayer)


	def populateLayers(self):
		self.inShape.clear()
		layermap = QgsMapLayerRegistry.instance().mapLayers()
		for name, layer in layermap.iteritems():
			self.inShape.addItem(unicode(layer.name()))
			if layer == self.iface.activeLayer():
				self.inShape.setCurrentIndex(self.inShape.count() - 1)

	def updateLayer(self):
		mLayerName = self.inShape.currentText()
		if not mLayerName == "":
			mLayer = ftools_utils.getMapLayerByName(unicode(mLayerName))
			# get layer extents
			boundBox = mLayer.extent()
			# if "align extents and resolution..." button is checked
			if self.chkAlign.isChecked():
				if not mLayer.type() == QgsMapLayer.RasterLayer:
					QMessageBox.information(self, self.tr("Vector grid"), self.tr("Please select a raster layer"))
				else:
					dx = math.fabs(boundBox.xMaximum() - boundBox.xMinimum()) / mLayer.width()
					dy = math.fabs(boundBox.yMaximum() - boundBox.yMinimum()) / mLayer.height()
					self.spnX.setValue(dx)
					self.spnY.setValue(dy)
			self.updateExtents(boundBox)

	def updateExtents(self, boundBox):
		self.xMin.setText(unicode(boundBox.xMinimum()))
		self.yMin.setText(unicode(boundBox.yMinimum()))
		self.xMax.setText(unicode(boundBox.xMaximum()))
		self.yMax.setText(unicode(boundBox.yMaximum()))


	def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", self.filename.displayText(), "Shapefile (*.shp)")
		if newname != None:
			self.filename.setText(newname)

	def vspacing_changed(self, text):
		# Hexagonal grid must maintain fixed aspect ratio to make sense
		if unicode(self.gridtype.currentText()) == "Hexagon (polygon)":
			spacing = float(text)
			self.hspacing.setText(unicode(spacing * 0.866025403784439))

	def hspacing_changed(self, text):
		if unicode(self.gridtype.currentText()) == "Hexagon (polygon)":
			spacing = float(text)
			self.vspacing.setText(unicode(spacing / 0.866025))

	def gridtype_changed(self, text):
		if text == "Hexagon (polygon)":
			spacing = float(self.vspacing.displayText())
			self.hspacing.setText(unicode(spacing * 0.866025))

	def run(self):
		savename = unicode(self.filename.displayText()).strip()
		try:
			hspacing = float(self.hspacing.displayText())
			vspacing = float(self.vspacing.displayText())
			#extent = self.inShape().extent()
			#width = MA_round((extent.xMaximum() - extent.xMinimum()), 4)
			#height = MA_round((extent.yMaximum() - extent.yMinimum()), 4)
			width = float(self.width.displayText())
			height = float(self.height.displayText())
		except:
			QMessageBox.critical(self.iface.mainWindow(), "Grid", "Invalid dimension parameter")
			return

		originx = float(self.xMin.displayText())- (width * 0.1)
		#if (str(self.xtype.currentText()) == "Center X") and (hspacing != 0):
			#originx = originx - (round(width / 2.0 / hspacing) * hspacing)
		#elif str(self.xtype.currentText()) == "Right X":
			#originx = originx - width

		originy = float(self.yMin.displayText()) - (height * 0.1)
		#if (str(self.ytype.currentText()) == "Middle Y") and (vspacing != 0):
			#originy = originy - (round(height / 2.0 / vspacing) * vspacing)
		#elif str(self.ytype.currentText()) == "Top Y":
			#originy = originy - height

		gridtype = unicode(self.gridtype.currentText())
		sourcename_grid = self.inShape.currentText()


		message = MA_grid(self.iface, sourcename_grid, savename, hspacing, vspacing, width, height, originx, originy, gridtype, 1)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Grid", message)

# --------------------------------------------------------
#	MA_store_distance - Create shapefile of distances
#			   from points to nearest store
# --------------------------------------------------------

from Store_distance_UI import *

class MA_store_distance_dialog(QDialog, Ui_MA_store_distance_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
		QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
			if layer.type() == QgsMapLayer.VectorLayer:
				self.sourcelayerbox.addItem(layer.name())
				self.storeslayerbox.addItem(layer.name())

		if self.storeslayerbox.count() > 1:
			self.storeslayerbox.setCurrentIndex(1)

		QObject.connect(self.storeslayerbox, SIGNAL("currentIndexChanged(QString)"), self.set_name_attributes)

		self.set_name_attributes()

		self.outputtype.addItems(["Line to Store", "Point"])

		self.measurement.addItems(["Layer Units", "Meters", "Feet", "Miles", "Kilometers"])
		# self.measurement.setEnabled(False)

		self.filename.setText(MA_temp_file_name(".shp"))

	def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile",
		self.filename.displayText(), "Shapefile (*.shp)")
		if newname != None:
			self.filename.setText(newname)

	def set_name_attributes(self):
		self.nameattributebox.clear()
		layer = MA_find_layer(self.storeslayerbox.currentText())
		if (layer == None):
			return
		for index, field in enumerate(layer.dataProvider().fields()):
			self.nameattributebox.addItem(field.name())

	def run(self):
		sourcename = unicode(self.sourcelayerbox.currentText())
		destname = unicode(self.storeslayerbox.currentText())
		nameattributename = unicode(self.nameattributebox.currentText())
		units = unicode(self.measurement.currentText())
		addlines = (self.outputtype.currentText() == "Line to Store")
		savename = unicode(self.filename.displayText()).strip()
		evenly_distributed = self.distribute.isChecked()

		message = MA_store_distance(self.iface, sourcename, destname, \
			nameattributename, units, addlines, savename, evenly_distributed, 1)

		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Store Distance", message)

# --------------------------------------------------------
#	MA_store_lines - Create shapefile of lines from
#			spoke points to matching stores
# --------------------------------------------------------

from MA_store_lines_form import *

class MA_store_lines_dialog(QDialog, Ui_MA_store_lines_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
		QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
			if layer.type() == QgsMapLayer.VectorLayer:
				self.storelayer.addItem(layer.name())
				self.spokelayer.addItem(layer.name())

		QObject.connect(self.storelayer, SIGNAL("currentIndexChanged(QString)"), self.set_store_attributes)
		QObject.connect(self.spokelayer, SIGNAL("currentIndexChanged(QString)"), self.set_spoke_attributes)

		self.set_store_attributes(self.storelayer.currentText())
		self.set_spoke_attributes(self.spokelayer.currentText())

		self.filename.setText(MA_temp_file_name(".shp"))

	def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile",
			self.filename.displayText(), "Shapefile (*.shp)")
		if newname != None:
			self.filename.setText(newname)

	def set_store_attributes(self, layername):
		self.storeid.clear()
		layer = MA_find_layer(layername)
		if (layer == None):
			return
		for index, field in enumerate(layer.dataProvider().fields()):
			self.storeid.addItem(field.name())

	def set_spoke_attributes(self, layername):
		self.spokestoreid.clear()
		layer = MA_find_layer(layername)
		if (layer == None):
			return
		for index, field in enumerate(layer.dataProvider().fields()):
			self.spokestoreid.addItem(field.name())

	def run(self):
		storename = unicode(self.storelayer.currentText())
		storeattr = unicode(self.storeid.currentText())
		spokename = unicode(self.spokelayer.currentText())
		spokeattr = unicode(self.spokestoreid.currentText())
		savename = unicode(self.filename.displayText()).strip()

		message = MA_store_lines(self.iface, storename, storeattr, spokename, spokeattr, savename, 1)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Store Lines", message)

#----------------------- About
from About_UI import *

class MA_About_Dialog(QDialog, Ui_MA_About_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)


