# -*- coding: utf-8 -*-
#-----------------------------------------------------------

from PyQt4.QtCore import QObject, SIGNAL, QVariant, QFile, QFileInfo
from PyQt4.QtGui import QDialog, QDialogButtonBox, QMessageBox, QColor
import ftools_utils
import matplotlib.cm
from qgis.core import QGis, QgsFeature, QgsVectorLayer, QgsVectorFileWriter, QgsFields, QgsField, QgsGeometry, QgsPoint, QgsCategorizedSymbolRendererV2, QgsSymbolV2, QgsRendererCategoryV2, QgsMapLayerRegistry, QgsDistanceArea 
from qgis.gui import QgsMapCanvas
from math import sqrt,fsum
from sys import float_info
from ui_frmCluster import Ui_Dialog
import random

class Dialog(QDialog, Ui_Dialog):

    def __init__(self, iface):
        QDialog.__init__(self, iface.mainWindow())
        self.iface = iface
        self.setupUi(self)
        self.updateUi()
        QObject.connect(self.toolOut, SIGNAL("clicked()"), self.outFile)
        QObject.connect(self.cmbClustertype, SIGNAL("currentIndexChanged(QString)"), self.update)
        self.buttonOk = self.buttonBox_2.button(QDialogButtonBox.Ok)
        self.progressBar.setValue(0)
        self.populateLayers()

    def populateLayers(self):
        layers = ftools_utils.getLayerNames([QGis.Point])
        self.inShape.blockSignals(True)
        self.inShape.clear()
        self.inShape.blockSignals(False)
        self.inShape.addItems(layers)

    def updateUi(self):
        self.setWindowTitle(self.tr("Customer clustering"))
        self.resize(381, 100)

    def update(self):
        self.cmbLinkage.blockSignals(True)
        self.cmbLinkage.clear()
        self.cmbLinkage.blockSignals(False)
        if self.cmbClustertype.currentIndex()<>0:
            self.spnSeed.setMaximum(0)
            self.spnSeed.clear()
            self.cmbLinkage.addItem(self.tr("Ward's"))
            self.cmbLinkage.addItem(self.tr("Single"))
            self.cmbLinkage.addItem(self.tr("Complete"))
            self.cmbLinkage.addItem(self.tr("Average"))
        else:
            self.spnSeed.setMinimum(1)
            self.spnSeed.setMaximum(999)
            self.spnSeed.setValue(1)

    def accept(self):
        self.buttonOk.setEnabled(False)
        if self.inShape.currentText() == "":
            QMessageBox.information(self, self.tr("Cluster statistics"), self.tr("No input vector layer specified"))
        elif self.outShape.text() == "":
            QMessageBox.information(self, self.tr("Cluster statistics"), self.tr("Please specify output shapefile"))
        else:
            inName = self.inShape.currentText()
            outPath = self.outShape.text()
            self.progressBar.setValue(0)
            success = self.compute(inName)
            self.outShape.clear()
            if not success:
                self.populateLayers()
            elif self.addToCanvasCheck.isChecked():
                addCanvasCheck = self.addShapeToCanvasWithColor(unicode(outPath),'Cluster_ID',0,self.spnNClust.value()-1)
                if not addCanvasCheck:
                    QMessageBox.warning(self, self.tr("Cluster statistics"), self.tr("Error loading output shapefile:\n%s") % (unicode(outPath)))
                self.populateLayers()
            else:
                QMessageBox.information(self, self.tr("Cluster statistics"), self.tr("Created output shapefile:\n%s") % (unicode(outPath)))
        self.progressBar.setValue(0)
        self.buttonOk.setEnabled(True)

    def outFile(self):
        self.outShape.clear()
        (self.shapefileName, self.encoding) = ftools_utils.saveDialog(self)
        if self.shapefileName is None or self.encoding is None:
            return
        self.outShape.setText(self.shapefileName)

    def compute(self, inName):
        vlayer = ftools_utils.getVectorLayerByName(inName)
        if self.useSelectedA.isChecked() and vlayer.selectedFeatureCount()<self.spnNClust.value():
            QMessageBox.critical(self, self.tr("Cluster statistics"), self.tr("Error initializing cluster analysis:\nToo little features selected"))
            return False
        provider = vlayer.dataProvider()
        if provider.featureCount()<self.spnNClust.value():
            QMessageBox.critical(self, self.tr("Cluster statistics"), self.tr("Error initializing cluster analysis:\nToo little features available"))
            return False
        sRs = provider.crs()
        self.d = QgsDistanceArea()
        self.d.setSourceCrs(sRs)
        self.d.setEllipsoid(sRs.ellipsoidAcronym())
        self.d.setEllipsoidalMode(sRs.geographicFlag())
        check = QFile(self.shapefileName)
        if check.exists():
            if not QgsVectorFileWriter.deleteShapeFile(self.shapefileName):
                return False
        fieldList = provider.fields()
        addID = fieldList.append(QgsField('Cluster_ID',QVariant.Int))
        if not addID:
            if 'Cluster_ID' in [field.name() for field in fieldList]:
                icl = fieldList.indexFromName('Cluster_ID')
                if fieldList[icl].type() <> QVariant.Int:
                    QMessageBox.warning(self, self.tr("Cluster statistics"), self.tr("Error setting output field Cluster_ID:\nField exists and has wrong type"))
                    return False
            else:
                QMessageBox.warning(self, self.tr("Cluster statistics"), self.tr("Error setting output field Cluster_ID"))
                return False
        writer = QgsVectorFileWriter(self.shapefileName, self.encoding, fieldList, QGis.WKBPoint, sRs)
        infeat = QgsFeature()
        outfeat = QgsFeature()
        # retrieve input features
        if self.useSelectedA.isChecked():
            fit = vlayer.selectedFeaturesIterator()
        else:
            fit = provider.getFeatures()
        # initialize points for clustering
        points = {}
        key = 0
        while fit.nextFeature(infeat):
            points[key] = infeat.geometry().asPoint()
            key += 1
        if self.spnNClust.value()>key:
            QMessageBox.warning(self, self.tr("Cluster statistics"), self.tr("Too little points available for %i clusters") % self.spnNClust.value())
            return False
        # do the clustering
        if self.cmbClustertype.currentIndex()==0:
            # K-means clustering
            progressRange = 100
            self.progressBar.setRange(0, progressRange)
            clusters = self.kmeans(points, self.spnNClust.value(), self.d,
                               10*float_info.epsilon, self.cmbDistance.currentIndex()==1)
            del points
            cluster_id = {}
            for idx,cluster in enumerate(clusters):
                for key in cluster.ids:
                    cluster_id[key] = idx
        else:
            # Hierarchical clustering
            progressRange = key
            self.progressBar.setRange(0, progressRange)
            if self.cmbLinkage.currentIndex()==0:
                clusters = self.hcluster_wards(points, self.spnNClust.value(),
						  self.cmbDistance.currentIndex()==1)
            elif self.cmbLinkage.currentIndex()==1:
                clusters = self.hcluster_single(points, self.spnNClust.value(),
						  self.cmbDistance.currentIndex()==1)
            elif self.cmbLinkage.currentIndex()==2:
                clusters = self.hcluster_complete(points, self.spnNClust.value(),
						  self.cmbDistance.currentIndex()==1)
            elif self.cmbLinkage.currentIndex()==3:
                clusters = self.hcluster_average(points, self.spnNClust.value(),
						  self.cmbDistance.currentIndex()==1)						   
            del points
            cluster_id = {}
            random.shuffle(clusters) # mix for nicer color display
            for idx,cluster in enumerate(clusters):
                for key in cluster:
                    cluster_id[key] = idx
        # retrieve input features again
        if self.useSelectedA.isChecked():
            fit = vlayer.selectedFeaturesIterator()
        else:
            fit = provider.getFeatures()
        # write results to output layer
        key = 0
        while fit.nextFeature(infeat):
            outfeat.setGeometry(infeat.geometry())
            atMap = infeat.attributes()
            if addID:
                atMap.append(cluster_id[key])
            else:
                atMap[icl] = cluster_id[key]
            outfeat.setAttributes(atMap)
            writer.addFeature(outfeat)
            key += 1
        del writer
        self.progressBar.setValue(progressRange)
        return True
    
    def addShapeToCanvasWithColor(self,shapefile_path,field,minval,maxval):
        file_info = QFileInfo(shapefile_path)
        if file_info.exists():
            layer_name = file_info.completeBaseName()
        else:
            return False
        vlayer_new = QgsVectorLayer(shapefile_path, layer_name, "ogr")
        if vlayer_new.isValid():
            self.applySymbologyFixedDivisions(vlayer_new,field,minval,maxval)
            QgsMapLayerRegistry.instance().addMapLayers([vlayer_new])
            return True
        else:
            return False
	    
    def validatedDefaultSymbol(self,geometryType):
        symbol = QgsSymbolV2.defaultSymbol(geometryType)
        if symbol is None:
            if geometryType == QGis.Point:
                symbol = QgsMarkerSymbolV2()
            elif geometryType == QGis.Line:
                symbol =  QgsLineSymbolV2()
            elif geometryType == QGis.Polygon:
                symbol = QgsFillSymbolV2()
        return symbol

    def makeSymbologyForCategory(self,layer,value,title,color):
        symbol = self.validatedDefaultSymbol(layer.geometryType())
        symbol.setColor(color)
        return QgsRendererCategoryV2(value,symbol,title)

    def applySymbologyFixedDivisions(self,layer,field,minval,maxval):
        rangeList = []
        cMap = matplotlib.cm.get_cmap('nipy_spectral',maxval-minval+1)
        for idx, fv in enumerate(range(minval,maxval+1)):
            rgb = [int(x*255) for x in cMap(idx)]
            rangeList.append(self.makeSymbologyForCategory(layer,fv,str(fv),
							QColor(rgb[0],rgb[1],rgb[2],rgb[3])))
        renderer = QgsCategorizedSymbolRendererV2(field,rangeList)
        layer.setRendererV2(renderer)
	  
    def kmeans(self, points, k, d, cutoff=10*float_info.epsilon, manhattan=False):

        random.seed(self.spnSeed.value()) 

        # Pick out k random points to use as our initial centroids
        initial = random.sample(points.keys(), k)
    
        # Create k clusters using those centroids
        clusters = [KMCluster(set([p]),points[p],d) for p in initial]
    
        # Loop through the dataset until the clusters stabilize
        loopCounter = 0
        while True:
            # Create a list of lists to hold the points in each cluster
            setList = [set() for i in range(k)]
	
            # Start counting loops
            loopCounter += 1
            self.progressBar.setValue(min(loopCounter,98))
            # For every point in the dataset ...
            for p in points.keys():
                # Get the distance between that point and the all the cluster centroids
                smallest_distance = float_info.max
	
                for i in range(k):
                    distance = self.getDistance(points[p],clusters[i].centerpoint,manhattan)
                    if distance < smallest_distance:
                        smallest_distance = distance
                        clusterIndex = i
                setList[clusterIndex].add(p)
	
            # Set biggest_shift to zero for this iteration
            biggest_shift = 0.0
	
            for i in range(k):
                # Calculate new centroid coordinates
                numPoints = len(setList[i])
                xcenter = fsum([points[p].x() for p in setList[i]])/numPoints
                ycenter = fsum([points[p].y() for p in setList[i]])/numPoints
                # Calculate how far the centroid moved in this iteration
                shift = clusters[i].update(setList[i], QgsPoint(xcenter,ycenter), manhattan)
                # Keep track of the largest move from all cluster centroid updates
                biggest_shift = max(biggest_shift, shift)

            # If the centroids have stopped moving much, say we're done!
            if biggest_shift < cutoff:
                self.progressBar.setValue(99)
                QMessageBox.information(self, self.tr("K-Means Clustering"), self.tr("Converged after %i iterations") % (loopCounter))
                break
        return clusters

    def hcluster_average(self, points, k, manhattan=False):

        def get_cluster_elements(clust):
            # return ids for elements in a cluster sub-tree
            if clust.id>=0:
                # positive id means that this is a leaf
                return [clust.id]
            else:
                # check the right and left branches
                cl = []
                cr = []
                if clust.left!=None:
                    cl = get_cluster_elements(clust.left)
                if clust.right!=None:
                    cr = get_cluster_elements(clust.right)
                return cl+cr

        clust={}
        distances={}
        currentclustid=-1
        numPoints=len(points)

        # clusters are initially singletons
        for p in points.keys():
            clust[p] = Cluster_node(id=p)
	    
        keys = clust.keys()
        keys.sort(reverse=True)
	
        # compute pairwise distances
        for i in range(len(keys)):
            ik = keys[i]
            for j in range(i+1,len(keys)):
                jk = keys[j]
                distances[(ik,jk)]=self.getDistance(points[ik],points[jk],manhattan)

        while currentclustid>=-numPoints+k:
            closest = float_info.max
    
            # loop through every pair looking for the smallest distance
            for i in range(len(keys)):
                ik = keys[i]
                for j in range(i+1,len(keys)):
                    jk = keys[j]
                    d=distances[(ik,jk)]
                    if d<closest:
                        closest=d
                        ilowest=i
                        jlowest=j
	    
            # retrieve clusters to merge
            ik = keys[ilowest]
            jk = keys[jlowest]
            iclust = clust[ik]
            jclust = clust[jk]
            size = iclust.size+jclust.size
            del clust[ik]
            del clust[jk]
            keys.pop(jlowest)
            keys.pop(ilowest)
	    
            # create the new cluster
            clust[currentclustid]=Cluster_node(size,left=iclust,
					       right=jclust,id=currentclustid)
            # compute new distances according to the Lance-Williams algorithm
            for l in range(len(keys)):
                lk = keys[l]
                lclust = clust[lk]
                alpha_i = float(iclust.size)/size
                alpha_j = float(jclust.size)/size
                jl = tuple(sorted([jk,lk],reverse=True))
                il = tuple(sorted([ik,lk],reverse=True))
                distances[(lk,currentclustid)] = alpha_i*distances[il]+alpha_j*distances[jl]
		
            keys.append(currentclustid)
	    
            # cluster ids that weren't in the original set are negative
            self.progressBar.setValue(-currentclustid)
            currentclustid-=1

        QMessageBox.information(self, self.tr("Hierarchical Clustering"), self.tr("Cluster tree computed"))

        return [get_cluster_elements(c) for c in clust.values()]

    def hcluster_single(self, points, k, manhattan=False):

        clusters={}
        distances=[]
        keys = points.keys()
        numPoints = len(keys)
        currentclustid = -1

        # clusters are initially singletons
        for p in keys:
            clusters[p] = [p]
	
        # compute pairwise distances
        for i in range(len(keys)):
            ik = keys[i]
            for j in range(i+1,len(keys)):
                jk = keys[j]
                distances.append((ik,jk,self.getDistance(points[ik],points[jk],manhattan)))
        distances.sort(key=lambda x: x[2],reverse=True)
	
        while currentclustid>=-numPoints+k:
            toMerge = distances.pop()
            ik = toMerge[0]
            jk = toMerge[1]
            if clusters[ik]<>clusters[jk]:
                # retrieve indexes of cluster
                if clusters[ik]<0:
                    members = clusters[clusters[ik]]
                    del clusters[clusters[ik]]
                else:
                    members = [ik]
                if clusters[jk]<0:
                    members += clusters[clusters[jk]]
                    del clusters[clusters[jk]]
                else:
                    members += [jk]
                for member in members:
                    clusters[member] = currentclustid
                clusters[currentclustid] = members
                self.progressBar.setValue(-currentclustid)
                currentclustid -= 1
	
        while currentclustid<0:
            if currentclustid in clusters:
                for member in clusters[currentclustid]:
                    del clusters[member]
            currentclustid +=1
		
        QMessageBox.information(self, self.tr("Hierarchical Clustering"), self.tr("Cluster tree computed"))

        return clusters.values()

    def hcluster_wards(self, points, k, manhattan=False):

        def get_cluster_elements(clust):
            # return ids for elements in a cluster sub-tree
            if clust.id>=0:
                # positive id means that this is a leaf
                return [clust.id]
            else:
                # check the right and left branches
                cl = []
                cr = []
                if clust.left!=None:
                    cl = get_cluster_elements(clust.left)
                if clust.right!=None:
                    cr = get_cluster_elements(clust.right)
                return cl+cr

        clust={}
        distances={}
        currentclustid=-1
        numPoints=len(points)

        # clusters are initially singletons
        for p in points.keys():
            clust[p] = Cluster_node(id=p)
	    
        keys = clust.keys()
        keys.sort(reverse=True)
	
        # compute pairwise distances
        for i in range(len(keys)):
            ik = keys[i]
            for j in range(i+1,len(keys)):
                jk = keys[j]
                distances[(ik,jk)]=self.getDistance(points[ik],points[jk],manhattan)

        while currentclustid>=-numPoints+k:
            closest = float_info.max
    
            # loop through every pair looking for the smallest distance
            for i in range(len(keys)):
                ik = keys[i]
                for j in range(i+1,len(keys)):
                    jk = keys[j]
                    d=distances[(ik,jk)]
                    if d<closest:
                        closest=d
                        ilowest=i
                        jlowest=j
	    
            # retrieve clusters to merge
            ik = keys[ilowest]
            jk = keys[jlowest]
            iclust = clust[ik]
            jclust = clust[jk]
            size = iclust.size+jclust.size
            del clust[ik]
            del clust[jk]
            keys.pop(jlowest)
            keys.pop(ilowest)
	    
            # create the new cluster
            clust[currentclustid]=Cluster_node(size,left=iclust,
                                               right=jclust,id=currentclustid)
            # compute new distances according to the Lance-Williams algorithm
            for l in range(len(keys)):
                lk = keys[l]
                lclust = clust[lk]
                alpha_i = float(iclust.size+lclust.size)/(iclust.size+jclust.size+lclust.size)
                alpha_j = float(jclust.size+lclust.size)/(iclust.size+jclust.size+lclust.size)
                beta = -float(lclust.size)/(iclust.size+jclust.size+lclust.size)
                jl = tuple(sorted([jk,lk],reverse=True))
                il = tuple(sorted([ik,lk],reverse=True))
                distances[(lk,currentclustid)] = alpha_i*distances[il]+alpha_j*distances[jl]+beta*distances[(ik,jk)]
		
            keys.append(currentclustid)
	    
            # cluster ids that weren't in the original set are negative
            self.progressBar.setValue(-currentclustid)
            currentclustid-=1

        QMessageBox.information(self, self.tr("Hierarchical Clustering"), self.tr("Cluster tree computed"))

        return [get_cluster_elements(c) for c in clust.values()]

    def hcluster_complete(self, points, k, manhattan=False):

        def get_cluster_elements(clust):
            # return ids for elements in a cluster sub-tree
            if clust.id>=0:
                # positive id means that this is a leaf
                return [clust.id]
            else:
                # check the right and left branches
                cl = []
                cr = []
                if clust.left!=None:
                    cl = get_cluster_elements(clust.left)
                if clust.right!=None:
                    cr = get_cluster_elements(clust.right)
                return cl+cr

        clust={}
        distances={}
        currentclustid=-1
        numPoints=len(points)

        # clusters are initially singletons
        for p in points.keys():
            clust[p] = Cluster_node(id=p)
	    
        keys = clust.keys()
        keys.sort(reverse=True)
	
        # compute pairwise distances
        for i in range(len(keys)):
            ik = keys[i]
            for j in range(i+1,len(keys)):
                jk = keys[j]
                distances[(ik,jk)]=self.getDistance(points[ik],points[jk],manhattan)

        while currentclustid>=-numPoints+k:
            closest = float_info.max
    
            # loop through every pair looking for the smallest distance
            for i in range(len(keys)):
                ik = keys[i]
                for j in range(i+1,len(keys)):
                    jk = keys[j]
                    d=distances[(ik,jk)]
                    if d<closest:
                        closest=d
                        ilowest=i
                        jlowest=j
	    
            # retrieve clusters to merge
            ik = keys[ilowest]
            jk = keys[jlowest]
            iclust = clust[ik]
            jclust = clust[jk]
            size = iclust.size+jclust.size
            del clust[ik]
            del clust[jk]
            keys.pop(jlowest)
            keys.pop(ilowest)
	    
            # create the new cluster
            clust[currentclustid]=Cluster_node(size,left=iclust,
					       right=jclust,id=currentclustid)
            # compute new distances according to the Lance-Williams algorithm
            for l in range(len(keys)):
                lk = keys[l]
                lclust = clust[lk]
                alpha_i = 0.5
                alpha_j = 0.5
                gamma = 0.5
                jl = tuple(sorted([jk,lk],reverse=True))
                il = tuple(sorted([ik,lk],reverse=True))
                distances[(lk,currentclustid)] = alpha_i*distances[il]+alpha_j*distances[jl]+gamma*abs(distances[il]-distances[jl])
		
            keys.append(currentclustid)
	    
            # cluster ids that weren't in the original set are negative
            self.progressBar.setValue(-currentclustid)
            currentclustid-=1

        QMessageBox.information(self, self.tr("Hierarchical Clustering"), self.tr("Cluster tree computed"))

        return [get_cluster_elements(c) for c in clust.values()]

    def getDistance(self, point1, point2, manhattan=False):
        '''
        Euclidean distance or Manhattan distance between points 1 and 2.
        '''
        if manhattan:
            return self.d.measureLine(point1,QgsPoint(point2.x(),point1.y()))+ \
                self.d.measureLine(QgsPoint(point2.x(),point1.y()),point2)+ \
                self.d.measureLine(point1,QgsPoint(point1.x(),point2.y()))+ \
                self.d.measureLine(QgsPoint(point1.x(),point2.y()),point2)
        else:
            return self.d.measureLine(point1,point2)

class KMCluster:
    '''
    Class for k-means clustering
    '''
    def __init__(self, ids, centerpoint,d):
	'''
	ids - set of integer IDs of the cluster points
	centerpoint - point of centroid
    d - distance calculation reference
	'''
	
        if len(ids) == 0: raise Exception("ILLEGAL: empty cluster")
	
        # The point IDs that belong to this cluster
        self.ids = ids
	
        # The center that belongs to this cluster
        self.centerpoint = centerpoint

        # Initialize distance computing
        self.d = d
    
    def update(self, ids, centerpoint, manhattan=False):
	'''
	Returns the distance between the previous centroid coordinates
	and the new centroid coordinates 
	and updates the point IDs and the centroid coordinates
	'''
        old_centerpoint = self.centerpoint
        self.ids = ids
        self.centerpoint = centerpoint
        return self.getDistance(old_centerpoint,
				 self.centerpoint, manhattan)
    
    def getDistance(self, point1, point2, manhattan=False):
	'''
	Euclidean distance or Manhattan distance between points 1 and 2.
	'''
        if manhattan:
            return self.d.measureLine(point1,QgsPoint(point2.x(),point1.y()))+ \
                self.d.measureLine(QgsPoint(point2.x(),point1.y()),point2)+ \
                self.d.measureLine(point1,QgsPoint(point1.x(),point2.y()))+ \
                self.d.measureLine(QgsPoint(point1.x(),point2.y()),point2)
        else:
            return self.d.measureLine(point1,point2)
	
	
class Cluster_node:
    '''
    Class for hierarchical clustering
    '''
    def __init__(self, size=1, left=None, right=None, id=None):

        self.size = size
        self.left = left
        self.right = right
        self.id = id
