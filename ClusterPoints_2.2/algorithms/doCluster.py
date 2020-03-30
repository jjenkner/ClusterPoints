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

from os import path

from processing import getObject
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import (ParameterVector,
                                        ParameterBoolean,
                                        ParameterSelection,
                                        ParameterNumber)        

from PyQt4.QtCore import QVariant
from qgis.core import QGis, QgsFeature, QgsField, QgsPoint, QgsDistanceArea 
from math import fsum
from sys import float_info
from processing.core.GeoAlgorithmExecutionException import *

import random

class doCluster(GeoAlgorithm):

    Points = 'Points'
    SelectedFeaturesOnly = 'SelectedFeaturesOnly'
    Cluster_Type = 'Cluster_Type'
    RandomSeed = 'RandomSeed'
    Linkage = 'Linkage'
    Distance_Type = 'Distance_Type'
    NumberOfClusters = 'NumberOfClusters'

    def help(self):
        return False, 'README.html'
        
    def defineCharacteristics(self):

        # The name that the user will see in the toolbox
        self.name = 'doCluster'

        # The branch of the toolbox under which the algorithm will appear
        self.group = 'doCluster'

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument    

        self.addParameter(ParameterVector(
            self.Points,
            self.tr('Point layer')))

        self.addParameter(ParameterBoolean(
            self.SelectedFeaturesOnly,
            self.tr('Flag for the use of selected features/points only')))

        self.addParameter(ParameterSelection(
            self.Cluster_Type,
            self.tr("Cluster algorithm (K-Means or Hierarchical)"),
            ['K-Means','Hierarchical']))
  
        self.addParameter(ParameterNumber(
            self.RandomSeed,
            self.tr('RandomSeed for initialization of the K-Means algorithm'),
            1,9999,1))

        self.addParameter(ParameterSelection(
            self.Linkage,
            self.tr("Link functions for Hierarchical algorithm"),
            ['Ward\'s','Single','Complete','Average']))
        
        self.addParameter(ParameterSelection(
            self.Distance_Type,
            self.tr("Distance calculation type"),
            ['Euclidean','Manhattan']))

        self.addParameter(ParameterNumber(
            self.NumberOfClusters,
            self.tr('User-defined number of clusters'),
            2,9999,2))

    def processAlgorithm(self, progress):

        Points = self.getParameterValue(self.Points)
        SelectedFeaturesOnly = self.getParameterValue(self.SelectedFeaturesOnly)
        Cluster_Type = self.getParameterValue(self.Cluster_Type)
        RandomSeed = self.getParameterValue(self.RandomSeed)
        Linkage = self.getParameterValue(self.Linkage)
        Distance_Type = self.getParameterValue(self.Distance_Type)
        NumberOfClusters = self.getParameterValue(self.NumberOfClusters)

        random.seed(RandomSeed)

        vlayer = getObject(Points)
        provider = vlayer.dataProvider()
        if provider.featureCount()<NumberOfClusters:
            raise GeoAlgorithmExecutionException("Error initializing cluster analysis:\nToo little features available")
        sRs = provider.crs()

        d = QgsDistanceArea()
        d.setSourceCrs(sRs)
        d.setEllipsoid(sRs.ellipsoidAcronym())
        d.setEllipsoidalMode(sRs.geographicFlag())

        # retrieve input features
        infeat = QgsFeature()
        if SelectedFeaturesOnly:
            fit = vlayer.selectedFeaturesIterator()
        else:
            fit = provider.getFeatures()

        # initialize points for clustering
        points = {}
        key = 0
        while fit.nextFeature(infeat):
            points[key] = infeat.geometry().asPoint()
            key += 1
        if NumberOfClusters>key:
            raise GeoAlgorithmExecutionException("Too little points available for %i clusters") % (NumberOfClusters)

        # do the clustering
        if Cluster_Type==0:
            if Linkage<>0:
                progress.setInfo("Linkage not used for K-Means")
            # K-means clustering
            clusters = self.kmeans(progress,points,NumberOfClusters,d,10*float_info.epsilon,Distance_Type==1)
            del points
            cluster_id = {}
            for idx,cluster in enumerate(clusters):
                for key in cluster.ids:
                    cluster_id[key] = idx
        else:
            # Hierarchical clustering
            if Linkage==0:
                clusters = self.hcluster_wards(progress,points,NumberOfClusters,d,Distance_Type==1)
            elif Linkage==1:
                clusters = self.hcluster_single(progress,points,NumberOfClusters,d,Distance_Type==1)
            elif Linkage==2:
                clusters = self.hcluster_complete(progress,points,NumberOfClusters,d,Distance_Type==1)
            elif Linkage==3:
                clusters = self.hcluster_average(progress,points,NumberOfClusters,d,Distance_Type==1)
            else:
                raise GeoAlgorithmExecutionException("Linkage must be Ward's, Single, Complete or Average") 
            del points
            cluster_id = {}
            for idx,cluster in enumerate(clusters):
                for key in cluster:
                    cluster_id[key] = idx

        # write results to input file
        progress.setInfo("Writing output field Cluster_ID")
        if not vlayer.isEditable():
            vlayer.startEditing()
        fieldList = provider.fields()
        if 'Cluster_ID' in [field.name() for field in fieldList]:
            icl = fieldList.indexFromName('Cluster_ID')
            provider.deleteAttributes([icl])
        provider.addAttributes([QgsField('Cluster_ID',QVariant.Int)])
        vlayer.updateFields()

        # assign the output points to the clusters
        if SelectedFeaturesOnly:
            fit = vlayer.selectedFeaturesIterator()
        else:
            fit = provider.getFeatures()
        key = 0
        while fit.nextFeature(infeat):
            atMap = infeat.attributes()
            atMap[-1] = cluster_id[key]
            infeat.setAttributes(atMap)
            vlayer.updateFeature(infeat)    
            key += 1
        vlayer.commitChanges()
        progress.setPercentage(100)



    # Define required functions for each clustering algorithm
    
    def kmeans(self, progress, points, k, d, cutoff=10*float_info.epsilon, manhattan=False):

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
            progress.setPercentage(min(loopCounter,90))
            # For every point in the dataset ...
            for p in points.keys():
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
                xcenter = fsum([points[p].x() for p in setList[i]])/numPoints
                ycenter = fsum([points[p].y() for p in setList[i]])/numPoints
                # Calculate how far the centroid moved in this iteration
                shift = clusters[i].update(setList[i], QgsPoint(xcenter,ycenter), manhattan)
                # Keep track of the largest move from all cluster centroid updates
                biggest_shift = max(biggest_shift, shift)

            # If the centroids have stopped moving much, say we're done!
            if biggest_shift < cutoff:
                progress.setPercentage(90)
                progress.setInfo("Converged after "+str(loopCounter)+" iterations")
                break
        return clusters

    def hcluster_average(self, progress, points, k, d, manhattan=False):

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
            clust[p] = Cluster_node(id=p,d=d)
            
        keys = clust.keys()
        keys.sort(reverse=True)
        
        # compute pairwise distances
        for i in range(len(keys)):
            ik = keys[i]
            for j in range(i+1,len(keys)):
                jk = keys[j]
                distances[(ik,jk)]=clust[i].getDistance(points[ik],points[jk],manhattan)

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
                alpha_i = float(iclust.size)/size
                alpha_j = float(jclust.size)/size
                jl = tuple(sorted([jk,lk],reverse=True))
                il = tuple(sorted([ik,lk],reverse=True))
                distances[(lk,currentclustid)] = alpha_i*distances[il]+alpha_j*distances[jl]
                
            keys.append(currentclustid)
            
            # cluster ids that weren't in the original set are negative
            progress.setPercentage(int(90*currentclustid/(k-numPoints)))
            currentclustid-=1

        progress.setInfo("Cluster tree computed")

        return [get_cluster_elements(c) for c in clust.values()]

    def hcluster_single(self, progress, points, k, d, manhattan=False):

        clusters={}
        distances=[]
        keys = points.keys()
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
                progress.setPercentage(int(90*currentclustid/(k-numPoints)))
                currentclustid -= 1
        
        while currentclustid<0:
            if currentclustid in clusters:
                for member in clusters[currentclustid]:
                    del clusters[member]
            currentclustid +=1

        progress.setInfo("Cluster tree computed")

        return clusters.values()

    def hcluster_wards(self, progress, points, k, d, manhattan=False):

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
            clust[p] = Cluster_node(id=p,d=d)
            
        keys = clust.keys()
        keys.sort(reverse=True)
        
        # compute pairwise distances
        for i in range(len(keys)):
            ik = keys[i]
            for j in range(i+1,len(keys)):
                jk = keys[j]
                distances[(ik,jk)]=clust[i].getDistance(points[ik],points[jk],manhattan)

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
            progress.setPercentage(int(90*currentclustid/(k-numPoints)))
            currentclustid-=1

        progress.setInfo("Cluster tree computed")

        return [get_cluster_elements(c) for c in clust.values()]

    def hcluster_complete(self, progress, points, k, d, manhattan=False):

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
            clust[p] = Cluster_node(id=p,d=d)
            
        keys = clust.keys()
        keys.sort(reverse=True)
        
        # compute pairwise distances
        for i in range(len(keys)):
            ik = keys[i]
            for j in range(i+1,len(keys)):
                jk = keys[j]
                distances[(ik,jk)]=clust[i].getDistance(points[ik],points[jk],manhattan)

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
                alpha_i = 0.5
                alpha_j = 0.5
                gamma = 0.5
                jl = tuple(sorted([jk,lk],reverse=True))
                il = tuple(sorted([ik,lk],reverse=True))
                distances[(lk,currentclustid)] = alpha_i*distances[il]+alpha_j*distances[jl]+gamma*abs(distances[il]-distances[jl])
                
            keys.append(currentclustid)

            # cluster ids that weren't in the original set are negative
            progress.setPercentage(int(90*currentclustid/(k-numPoints)))
            currentclustid-=1

        progress.setInfo("Cluster tree computed")
 
        return [get_cluster_elements(c) for c in clust.values()]



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
            return self.d.measureLine(point1,QgsPoint(point2.x(),point1.y()))+ \
                self.d.measureLine(QgsPoint(point2.x(),point1.y()),point2)+ \
                self.d.measureLine(point1,QgsPoint(point1.x(),point2.y()))+ \
                self.d.measureLine(QgsPoint(point1.x(),point2.y()),point2)
        else:
            return self.d.measureLine(point1,point2)
