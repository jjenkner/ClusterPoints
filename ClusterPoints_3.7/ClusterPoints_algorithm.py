# -*- coding: utf-8 -*-

"""
/***************************************************************************
 ClusterPoints
                                 A QGIS plugin
 Cluster Points conducts spatial clustering of points based on their mutual distance to each other. The user can select between the K-Means algorithm and (agglomerative) hierarchical clustering with several different link functions.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-03-30
        copyright            : (C) 2020 by Johannes Jenkner
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
__date__ = '2020-03-30'
__copyright__ = '(C) 2020 by Johannes Jenkner'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'



import os
import sys
import inspect

from qgis.core import QgsProcessingAlgorithm, QgsApplication
from qgis.core import QgsProcessingProvider

from PyQt5.QtCore import QCoreApplication,QVariant
from qgis.core import (QgsProcessing,QgsProcessingException,QgsProcessingAlgorithm,
                                                QgsFeature,QgsField,QgsPointXY,QgsDistanceArea,
                                                QgsProcessingParameterVectorLayer,
                                                QgsProcessingParameterBoolean,
                                                QgsProcessingParameterEnum,
                                                QgsProcessingParameterNumber)

from math import fsum
from sys import float_info

import random



class ClusterPointsAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    Points = 'Points'
    SelectedFeaturesOnly = 'SelectedFeaturesOnly'
    Cluster_Type = 'Cluster_Type'
    RandomSeed = 'RandomSeed'
    Linkage = 'Linkage'
    Distance_Type = 'Distance_Type'
    NumberOfClusters = 'NumberOfClusters'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(QgsProcessingParameterVectorLayer(
            self.Points,
            self.tr('Point layer')))

        self.addParameter(QgsProcessingParameterBoolean(
            self.SelectedFeaturesOnly,
            self.tr('Flag for the use of selected features/points only')))

        self.addParameter(QgsProcessingParameterEnum(
            self.Cluster_Type,
            self.tr("Cluster algorithm (K-Means or Hierarchical)"),
            ['K-Means','Hierarchical']))
  
        self.addParameter(QgsProcessingParameterNumber(
            self.RandomSeed,
            self.tr('RandomSeed for initialization of the K-Means algorithm'),
            defaultValue=1,minValue=1,maxValue=999))

        self.addParameter(QgsProcessingParameterEnum(
            self.Linkage,
            self.tr("Link functions for Hierarchical algorithm"),
            ['Ward\'s','Single','Complete','Average'],optional=True))
        
        self.addParameter(QgsProcessingParameterEnum(
            self.Distance_Type,
            self.tr("Distance calculation type"),
            ['Euclidean','Manhattan']))

        self.addParameter(QgsProcessingParameterNumber(
            self.NumberOfClusters,
            self.tr('User-defined number of clusters'),
            defaultValue=2,minValue=2,maxValue=999))

    def processAlgorithm(self, parameters, context, progress):

        vlayer = self.parameterAsVectorLayer(parameters, self.Points, context)
        SelectedFeaturesOnly = self.parameterAsBool(parameters, self.SelectedFeaturesOnly, context)
        Cluster_Type = self.parameterAsEnum(parameters, self.Cluster_Type, context)
        RandomSeed = self.parameterAsInt(parameters, self.RandomSeed, context)
        Linkage = self.parameterAsEnum(parameters, self.Linkage, context)
        Distance_Type = self.parameterAsEnum(parameters, self.Distance_Type, context)
        NumberOfClusters = self.parameterAsInt(parameters, self.NumberOfClusters, context)

        random.seed(RandomSeed)

        provider = vlayer.dataProvider()
        if provider.featureCount()<NumberOfClusters:
            raise QgsProcessingException("Error initializing cluster analysis:\nToo little features available")
        sRs = provider.crs()

        d = QgsDistanceArea()
        d.setSourceCrs(sRs, context.transformContext())
        d.setEllipsoid(context.project().ellipsoid())

        # retrieve input features
        if SelectedFeaturesOnly:
            fit = vlayer.getSelectedFeatures()
        else:
            fit = vlayer.getFeatures()

        # initialize points for clustering
        points = {}
        key = 0
        infeat = QgsFeature()
        while fit.nextFeature(infeat):
            points[key] = infeat.geometry().asPoint()
            key += 1
        if NumberOfClusters>key:
            raise QgsProcessingException("Too little points available for {} clusters".format(NumberOfClusters))

        # do the clustering
        if Cluster_Type==0:
            if parameters['Linkage'] is not None:
                progress.pushInfo(self.tr("Linkage not used for K-Means"))
            # K-means clustering
            clusters = self.kmeans(progress,points,NumberOfClusters,d,10*float_info.epsilon,Distance_Type==1)
        else:
            # Hierarchical clustering
            if parameters['Linkage'] is None:
                raise QgsProcessingException("Linkage must be Ward's, Single, Complete or Average")
            elif Linkage==0:
                clusters = self.hcluster_wards(progress,points,NumberOfClusters,d,Distance_Type==1)
            elif Linkage==1:
                clusters = self.hcluster_single(progress,points,NumberOfClusters,d,Distance_Type==1)
            elif Linkage==2:
                clusters = self.hcluster_complete(progress,points,NumberOfClusters,d,Distance_Type==1)
            elif Linkage==3:
                clusters = self.hcluster_average(progress,points,NumberOfClusters,d,Distance_Type==1)
        del points
            
        # assign cluster IDs
        cluster_id = {}
        for idx,cluster in enumerate(clusters):
            for key in cluster:
                cluster_id[key] = idx

        # prepare output field in input layer
        progress.pushInfo(self.tr("Writing output field Cluster_ID"))
        if not vlayer.isEditable():
            vlayer.startEditing()
        fieldList = provider.fields()
        if "Cluster_ID" in [field.name() for field in fieldList]:
            icl = fieldList.indexFromName("Cluster_ID")
            provider.deleteAttributes([icl])
        provider.addAttributes([QgsField("Cluster_ID",QVariant.Int)])
        vlayer.updateFields()

        # assign clusters to input layer
        if SelectedFeaturesOnly:
            fit = vlayer.getSelectedFeatures()
        else:
            fit = vlayer.getFeatures()
        key = 0
        id_clust = vlayer.dataProvider().fieldNameIndex("Cluster_ID")
        while fit.nextFeature(infeat):
            vlayer.changeAttributeValue(infeat.id(), id_clust, cluster_id[key])
            key += 1
        vlayer.commitChanges()
        progress.setProgress(100)
        
        return {self.Points:"Cluster_ID"}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'doCluster'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'clustering'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ClusterPointsAlgorithm()

    # Define required functions for each clustering algorithm
    
    def kmeans(self, progress, points, k, d, cutoff=10*float_info.epsilon, manhattan=False):

        # Pick out k random points to use as our initial centroids
        initial = random.sample(list(points.keys()), k)
    
        # Create k clusters using those centroids
        clusters = [KMCluster(set([p]),points[p],d) for p in initial]
    
        # Loop through the dataset until the clusters stabilize
        loopCounter = 0
        while True:
            # Create a list of lists to hold the points in each cluster
            setList = [set() for i in range(k)]
        
            # Start counting loops
            loopCounter += 1
            progress.setProgress(min(loopCounter,90))
            # For every point in the dataset ...
            for p in list(points.keys()):
                # Get the distance between that point and the all the cluster centroids
                smallest_distance = float_info.max
        
                for i in range(k):
                    distance = clusters[i].getDistance(points[p],clusters[i].centerpoint,manhattan)
                    if distance < smallest_distance:
                        smallest_distance = distance
                        clusterIndex = i
                setList[clusterIndex].add(p)
        
            # Set biggest_shift to zero for this iteration
            biggest_shift = 0.0
        
            for i in range(k):
                # Calculate new centroid coordinates
                numPoints = len(setList[i])
                if numPoints == 0:
                    raise QgsProcessingException("Algorithm failed after "+ \
                                                 "{} iterations: Choose a "+ \
                                                 "different random seed or "+ \
                                                 "a smaller number of clusters".format(loopCounter))
                xcenter = fsum([points[p].x() for p in setList[i]])/numPoints
                ycenter = fsum([points[p].y() for p in setList[i]])/numPoints
                # Calculate how far the centroid moved in this iteration
                shift = clusters[i].update(setList[i], QgsPointXY(xcenter,ycenter), manhattan)
                # Keep track of the largest move from all cluster centroid updates
                biggest_shift = max(biggest_shift, shift)

            # If the centroids have stopped moving much, say we're done!
            if biggest_shift < cutoff:
                progress.setProgress(90)
                progress.pushInfo(self.tr("Converged after {} iterations").format(loopCounter))
                break
    
        return [c.ids for c in clusters]

    def hcluster_average(self, progress, points, k, d, manhattan=False):

        clust={}
        distances={}
        currentclustid=-1
        numPoints=len(points)
        keys=[]

        # clusters are initially singletons
        for p in reversed(list(points.keys())):
            clust[p] = Cluster_node(id=p,d=d)
            keys.append(p)
        
        # compute pairwise distances
        for i in range(len(keys)):
            ik = keys[i]
            for j in range(i+1,len(keys)):
                jk = keys[j]
                distances[(ik,jk)]=clust[ik].getDistance(points[ik],points[jk],manhattan)

        while currentclustid>=k-numPoints:
            closest = float_info.max
    
            # loop through every pair looking for the smallest distance
            for i in range(len(keys)):
                ik = keys[i]
                for j in range(i+1,len(keys)):
                    jk = keys[j]
                    dist=distances[(ik,jk)]
                    if dist<closest:
                        closest=dist
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
                                               right=jclust,id=currentclustid,d=d)
            # compute new distances according to the Lance-Williams algorithm
            alpha_i = float(iclust.size)/size
            alpha_j = float(jclust.size)/size
            for l in range(len(keys)):
                lk = keys[l]
                jl = tuple(sorted([jk,lk],reverse=True))
                il = tuple(sorted([ik,lk],reverse=True))
                distances[(lk,currentclustid)] = alpha_i*distances[il]+alpha_j*distances[jl]
                
            keys.append(currentclustid)
            
            # cluster ids that weren't in the original set are negative
            progress.setProgress(int(90*currentclustid/(k-numPoints)))
            currentclustid-=1

        progress.pushInfo(self.tr("Cluster tree computed"))

        return [c.getElements(c) for c in list(clust.values())]

    def hcluster_single(self, progress, points, k, d, manhattan=False):

        clusters={}
        distances=[]
        keys = list(points.keys())
        numPoints = len(keys)
        currentclustid = -1

        # clusters are initially singletons
        cluster_sample=Cluster_node(d=d)
        for p in keys:
            clusters[p] = [p]
        
        # compute pairwise distances
        for i in range(len(keys)):
            ik = keys[i]
            for j in range(i+1,len(keys)):
                jk = keys[j]
                distances.append((ik,jk,cluster_sample.getDistance(points[ik],points[jk],manhattan)))
        distances.sort(key=lambda x: x[2],reverse=True)
        
        while currentclustid>=k-numPoints:
            toMerge = distances.pop()
            ik = toMerge[0]
            jk = toMerge[1]
            if clusters[ik]!=clusters[jk]:
                # retrieve indexes of cluster
                if isinstance(clusters[ik],int):
                    members = clusters[clusters[ik]]
                    del clusters[clusters[ik]]
                else:
                    members = [ik]
                if isinstance(clusters[jk],int):
                    members += clusters[clusters[jk]]
                    del clusters[clusters[jk]]
                else:
                    members += [jk]
                for member in members:
                    clusters[member] = currentclustid
                clusters[currentclustid] = members
                progress.setProgress(int(90*currentclustid/(k-numPoints)))
                currentclustid -= 1
        
        while currentclustid<0:
            if currentclustid in clusters:
                for member in clusters[currentclustid]:
                    del clusters[member]
            currentclustid +=1

        progress.pushInfo(self.tr("Cluster tree computed"))

        return list(clusters.values())

    def hcluster_wards(self, progress, points, k, d, manhattan=False):

        clust={}
        distances={}
        currentclustid=-1
        numPoints=len(points)
        keys=[]

        # clusters are initially singletons
        for p in reversed(list(points.keys())):
            clust[p] = Cluster_node(id=p,d=d)
            keys.append(p)
        
        # compute pairwise distances
        for i in range(len(keys)):
            ik = keys[i]
            for j in range(i+1,len(keys)):
                jk = keys[j]
                distances[(ik,jk)]=clust[ik].getDistance(points[ik],points[jk],manhattan)

        while currentclustid>=k-numPoints:
            closest = float_info.max
    
            # loop through every pair looking for the smallest distance
            for i in range(len(keys)):
                ik = keys[i]
                for j in range(i+1,len(keys)):
                    jk = keys[j]
                    dist=distances[(ik,jk)]
                    if dist<closest:
                        closest=dist
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
                                               right=jclust,id=currentclustid,d=d)
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
            progress.setProgress(int(90*currentclustid/(k-numPoints)))
            currentclustid-=1
        
        progress.pushInfo(self.tr("Cluster tree computed"))

        return [c.getElements(c) for c in list(clust.values())]

    def hcluster_complete(self, progress, points, k, d, manhattan=False):

        clust={}
        distances={}
        currentclustid=-1
        numPoints=len(points)
        keys=[]

        # clusters are initially singletons
        for p in reversed(list(points.keys())):
            clust[p] = Cluster_node(id=p,d=d)
            keys.append(p)
            
        keys = list(clust.keys())
        keys.sort(reverse=True)
        
        # compute pairwise distances
        for i in range(len(keys)):
            ik = keys[i]
            for j in range(i+1,len(keys)):
                jk = keys[j]
                distances[(ik,jk)]=clust[ik].getDistance(points[ik],points[jk],manhattan)

        while currentclustid>=k-numPoints:
            closest = float_info.max
    
            # loop through every pair looking for the smallest distance
            for i in range(len(keys)):
                ik = keys[i]
                for j in range(i+1,len(keys)):
                    jk = keys[j]
                    dist=distances[(ik,jk)]
                    if dist<closest:
                        closest=dist
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
                                               right=jclust,id=currentclustid,d=d)
            # compute new distances according to the Lance-Williams algorithm
            alpha_i = 0.5
            alpha_j = 0.5
            gamma = 0.5
            for l in range(len(keys)):
                lk = keys[l]
                jl = tuple(sorted([jk,lk],reverse=True))
                il = tuple(sorted([ik,lk],reverse=True))
                distances[(lk,currentclustid)] = alpha_i*distances[il]+alpha_j*distances[jl]+gamma*abs(distances[il]-distances[jl])
                
            keys.append(currentclustid)

            # cluster ids that weren't in the original set are negative
            progress.setProgress(int(90*currentclustid/(k-numPoints)))
            currentclustid-=1

        progress.pushInfo(self.tr("Cluster tree computed"))
 
        return [c.getElements(c) for c in list(clust.values())]



# Define required cluster classes

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
        
        if len(ids) == 0: raise Exception("Error: Empty cluster")
        
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
            return self.d.measureLine(point1,QgsPointXY(point2.x(),point1.y()))+ \
                self.d.measureLine(QgsPointXY(point2.x(),point1.y()),point2)+ \
                self.d.measureLine(point1,QgsPointXY(point1.x(),point2.y()))+ \
                self.d.measureLine(QgsPointXY(point1.x(),point2.y()),point2)
        else:
            return self.d.measureLine(point1,point2) 
                
class Cluster_node:
    '''
    Class for hierarchical clustering
    '''
    def __init__(self, size=1, left=None, right=None, id=None, d=None):
        self.size = size
        self.left = left
        self.right = right
        self.id = id
        self.d = d

    def getDistance(self, point1, point2, manhattan=False):
        '''
        Euclidean distance or Manhattan distance between points 1 and 2.
        '''
        if manhattan:
            return self.d.measureLine(point1,QgsPointXY(point2.x(),point1.y()))+ \
                self.d.measureLine(QgsPointXY(point2.x(),point1.y()),point2)+ \
                self.d.measureLine(point1,QgsPointXY(point1.x(),point2.y()))+ \
                self.d.measureLine(QgsPointXY(point1.x(),point2.y()),point2)
        else:
            return self.d.measureLine(point1,point2)

    def getElements(self,clust):
        '''
        Return all positive ids within the cluster
        '''
        if clust.id>=0:
            return [clust.id]
        else:
            return self.getElements(clust.left)+self.getElements(clust.right)

