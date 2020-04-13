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
__date__ = '2020-04-03'
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
                                                QgsField,QgsPoint,
                                                QgsPointXY,QgsDistanceArea,
                                                QgsProcessingParameterVectorLayer,
                                                QgsProcessingParameterBoolean,
                                                QgsProcessingParameterEnum,
                                                QgsProcessingParameterNumber,
                                                QgsProcessingParameterField)

from math import fsum,sqrt
from sys import float_info
from bisect import bisect

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
    PercentAttrib = 'PercentAttrib'
    AttribValue = 'AttribValue'

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
            ['K-Means','Hierarchical'],defaultValue='K-Means'))
  
        self.addParameter(QgsProcessingParameterNumber(
            self.RandomSeed,
            self.tr('RandomSeed for initialization of the K-Means algorithm'),
            defaultValue=1,minValue=1,maxValue=999))

        self.addParameter(QgsProcessingParameterEnum(
            self.Linkage,
            self.tr("Link functions for Hierarchical algorithm"),
            ['Single','Complete','Average (only for small dataset)',
            'Ward\'s (only for small dataset)','Centroid (only for small dataset)'],
            optional=True))
        
        self.addParameter(QgsProcessingParameterEnum(
            self.Distance_Type,
            self.tr("Distance calculation type"),
            ['Euclidean','Manhattan'],defaultValue='Euclidean'))

        self.addParameter(QgsProcessingParameterNumber(
            self.NumberOfClusters,
            self.tr('User-defined number of clusters'),
            defaultValue=2,minValue=2,maxValue=999))

        self.addParameter(QgsProcessingParameterNumber(
            self.PercentAttrib,self.tr('Percentage contribution of attribute field'),
            defaultValue=0,minValue=0,maxValue=100))

        self.addParameter(QgsProcessingParameterField(
            self.AttribValue,self.tr('Attribute field'),'',
            self.Points,optional=True))

    def processAlgorithm(self, parameters, context, progress):

        vlayer = self.parameterAsVectorLayer(parameters, self.Points, context)
        SelectedFeaturesOnly = self.parameterAsBool(parameters, self.SelectedFeaturesOnly, context)
        Cluster_Type = self.parameterAsEnum(parameters, self.Cluster_Type, context)
        RandomSeed = self.parameterAsInt(parameters, self.RandomSeed, context)
        Linkage = self.parameterAsEnum(parameters, self.Linkage, context)
        Distance_Type = self.parameterAsEnum(parameters, self.Distance_Type, context)
        NumberOfClusters = self.parameterAsInt(parameters, self.NumberOfClusters, context)
        PercentAttrib = self.parameterAsInt(parameters, self.PercentAttrib, context)
        AttribValue = self.parameterAsFields(parameters, self.AttribValue, context)

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
        points = {infeat.id():QgsPoint(infeat.geometry().asPoint()) for \
                  infeat in fit}

        # retrieve optional z values to consider in clustering
        if PercentAttrib>0 and parameters['AttribValue'] is not None:
            id_attr = vlayer.dataProvider().fieldNameIndex(AttribValue[0])
            if id_attr<0:
                raise QgsProcessingException("Field {} not found in input layer".format(AttribValue[0]))
            if not vlayer.fields()[id_attr].typeName().startswith('Int') and \
                  not vlayer.fields()[id_attr].typeName().startswith('Real') and \
                  vlayer.fields()[id_attr].type()!=QVariant.Double:
        	    raise QgsProcessingException("Field {} must be numeric".format(AttribValue[0]))
            if SelectedFeaturesOnly:
                fit = vlayer.getSelectedFeatures()
            else:
                fit = vlayer.getFeatures()
            for infeat in fit:
                if infeat[id_attr] or infeat[id_attr]==0:
                    points[infeat.id()].addZValue(infeat[id_attr])
                else:
                    del points[infeat.id()]
        else:
            for key in points.keys():
                points[key].addZValue()

        if NumberOfClusters>len(points):
            raise QgsProcessingException("Too little valid points "+ \
                                    "available for {} clusters".format(NumberOfClusters))

        # standardize z values with standard deviation of horizontal distances
        if PercentAttrib>0 and parameters['AttribValue'] is not None:
            if len(set([p.z() for p in points.values()]))==1:
                raise QgsProcessingException("Field {} must not be constant".format(AttribValue[0])) 
            standard_factor = self.compute_sd_distance([p.x() for p in points.values()], \
                                                       [p.y() for p in points.values()], \
                                                       Distance_Type==1)/ \
                                                       self.__class__.compute_sd( \
                                                       [p.z() for p in points.values()])
            zcenter = fsum([p.z() for p in points.values()])/len(points)
            for key in points.keys():
                points[key].setZ((points[key].z()-zcenter)*standard_factor)

        # do the clustering
        if Cluster_Type==0:
            if parameters['Linkage'] is not None:
                progress.pushInfo(self.tr("Linkage not used for K-Means"))
            # K-means clustering
            clusters = self.kmeans(progress,points,PercentAttrib,NumberOfClusters,d, \
                                            10*float_info.epsilon,Distance_Type==1)
        else:
            # Hierarchical clustering
            if parameters['Linkage'] is None:
                raise QgsProcessingException("Linkage must be Single,"+ \
                                             " Complete, Average, Ward\'s"+ \
                                             " or Centroid")
            elif Linkage==0:
                clusters = self.hcluster_slink(progress,points,PercentAttrib, \
                                             NumberOfClusters,d,Distance_Type==1)
            elif Linkage==1:
                clusters = self.hcluster_clink(progress,points,PercentAttrib, \
                                             NumberOfClusters,d,Distance_Type==1)
            elif Linkage==2:
                clusters = self.hcluster(progress,"average",points,PercentAttrib, \
                                             NumberOfClusters,d,Distance_Type==1)
            elif Linkage==3:
                clusters = self.hcluster(progress,"wards",points,PercentAttrib, \
                                             NumberOfClusters,d,Distance_Type==1)
                                             
            elif Linkage==4:
                clusters = self.hcluster(progress,"centroid",points,PercentAttrib, \
                                             NumberOfClusters,d,Distance_Type==1)

        del points
            
        # assign cluster IDs
        cluster_id = {}
        for idx,cluster in enumerate(clusters):
            for key in cluster:
                cluster_id[key] = idx

        progress.pushInfo(self.tr("Writing output field Cluster_ID"))
        
        # prepare output field in input layer
        fieldList = vlayer.dataProvider().fields()
        vlayer.startEditing()
        if "Cluster_ID" in [field.name() for field in fieldList]:
            icl = fieldList.indexFromName("Cluster_ID")
            vlayer.dataProvider().deleteAttributes([icl])
        provider.addAttributes([QgsField("Cluster_ID",QVariant.Int)])
        vlayer.updateFields()
        vlayer.commitChanges()
        
        # write output field in input layer
        fieldList = vlayer.dataProvider().fields()
        icl = fieldList.indexFromName("Cluster_ID")
        vlayer.startEditing()
        for key in cluster_id.keys():
            vlayer.dataProvider().changeAttributeValues({key:{icl:cluster_id[key]}})
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

    # Define auxiliary functions
    
    @staticmethod
    def compute_sd(x):
        """
        Computes (unbiased) standard deviation of x
        """
        xmean = fsum(x)/len(x)
        sd = 0
        for i in range(len(x)):
            sd += (x[i]-xmean)*(x[i]-xmean)
        sd = sqrt(sd/(len(x)-1))
        return sd
    
    def compute_sd_distance(self, x, y, manhattan=False):
        """
        Computes standard deviation of distances
        for points describes by x and y 
        (either Euclidean or Manhattan)
        """
        xmean = fsum(x)/len(x)
        ymean = fsum(y)/len(y)
        sd = []
        if manhattan:
            for i in range(len(x)):
                sd.append(x[i]+y[i]-xmean-ymean)
        else:
            for i in range(len(x)):
                sd.append(sqrt((x[i]-xmean)*(x[i]-xmean)+(y[i]-ymean)*(y[i]-ymean)))
        return self.__class__.compute_sd(sd)

    # Define required functions for each clustering algorithm

    def init_kmeans_plusplus(self, points, pz, k, d, manhattan=False):
        """
        Initializes the K-means algorithm according to
        Arthur, D. and Vassilvitskii, S. (2007)
        Referred to as K-means++
        """
        
        keys = list(points.keys())
        
        # draw first point randomly from dataset with uniform weights
        p = random.choice(keys)
        inits = [KMCluster(set([p]),points[p],d, pz)]
        
        # loop until k points were found
        while len(inits)<k:
            # define new probability weights for sampling
            weights = [min([inits[i].distance2center(points[p], \
                       manhattan) for i in range(len(inits))]) for p in keys]
            # draw new point randomly with probability weights
            p = random.uniform(0,sum(weights)-float_info.epsilon)
            p = bisect([sum(weights[:i+1]) for i in range(len(weights))],p)
            p = keys[p]
            inits.append(KMCluster(set([p]),points[p],d, pz))
            
        return inits

    def kmeans(self, progress, points, pz, k, d, cutoff=10*float_info.epsilon, manhattan=False):

        # Create k clusters using the K-means++ initialization method
        progress.pushInfo(self.tr("Initializing clusters with K-means++"))
        clusters = self.init_kmeans_plusplus(points, pz, k, d, manhattan)
        progress.pushInfo(self.tr("{} clusters successfully initialized".format(k)))
    
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
                    distance = clusters[i].distance2center(points[p],manhattan)
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
                                                 "{} iterations: Choose a ".format(loopCounter)+ \
                                                 "different random seed or "+ \
                                                 "a smaller number of clusters")
                xcenter = fsum([points[p].x() for p in setList[i]])/numPoints
                ycenter = fsum([points[p].y() for p in setList[i]])/numPoints
                zcenter = fsum([points[p].z() for p in setList[i]])/numPoints
                # Calculate how far the centroid moved in this iteration
                shift = clusters[i].update(setList[i], QgsPoint(xcenter,ycenter,zcenter), manhattan)
                # Keep track of the largest move from all cluster centroid updates
                biggest_shift = max(biggest_shift, shift)

            # If the centroids have stopped moving much, say we're done!
            if biggest_shift < cutoff:
                progress.setProgress(90)
                progress.pushInfo(self.tr("Converged after {} iterations").format(loopCounter))
                break
    
        return [c.ids for c in clusters]

    def hcluster(self, progress, link, points, pz, k, d, manhattan=False):

        clust={}
        distances={}
        currentclustid=-1
        numPoints=len(points)

        # clusters are initially singletons
        for ik,p in zip(range(numPoints-1, -1, -1), points.keys()):
            clust[ik] = Cluster_node(members=[p],d=d,pz=pz)
        
        # compute pairwise distances
        for ik in clust.keys():
            for jk in clust.keys():
                if jk<ik:
                    distances[(ik,jk)]=clust[ik].getDistance(points[clust[ik].members[0]], \
                                       points[clust[jk].members[0]],manhattan)

        while currentclustid>=k-numPoints:
            closest = float_info.max
    
            # loop through every pair looking for the smallest distance
            for ik in clust.keys():
                for jk in clust.keys():
                    if jk<ik:
                        dist=distances[(ik,jk)]
                        if dist<closest:
                            closest=dist
                            ik_lowest=ik
                            jk_lowest=jk
            
            # detect clusters to merge
            ik = ik_lowest
            jk = jk_lowest
            
            # create the new cluster
            clust[currentclustid]=Cluster_node(members=clust[ik].members+ \
                                  clust[jk].members,d=d,pz=pz)
                                  
            # compute updated distances according to the Lance-Williams algorithm
            
            if link == 'single':

                alpha_i = 0.5
                alpha_j = 0.5
                gamma = -0.5
                for lk in clust.keys():
                    if lk not in (ik,jk,currentclustid):
                        jl = (jk,lk) if jk>lk else (lk,jk)
                        il = (ik,lk) if ik>lk else (lk,ik)
                        distances[(lk,currentclustid)] = alpha_i*distances[il]+ \
                                  alpha_j*distances[jl]+gamma*abs(distances[il]-distances[jl])

            elif link == 'complete':
            
                alpha_i = 0.5
                alpha_j = 0.5
                gamma = 0.5
                for lk in clust.keys():
                    if lk not in (ik,jk,currentclustid):
                        jl = (jk,lk) if jk>lk else (lk,jk)
                        il = (ik,lk) if ik>lk else (lk,ik)
                        distances[(lk,currentclustid)] = alpha_i*distances[il]+ \
                                  alpha_j*distances[jl]+gamma*abs(distances[il]-distances[jl])
            
            elif link == 'average':
            
                alpha_i = float(clust[ik].size)/clust[currentclustid].size
                alpha_j = float(clust[jk].size)/clust[currentclustid].size
                for lk in clust.keys():
                    if lk not in (ik,jk,currentclustid):
                        jl = (jk,lk) if jk>lk else (lk,jk)
                        il = (ik,lk) if ik>lk else (lk,ik)
                        distances[(lk,currentclustid)] = \
                                  alpha_i*distances[il]+alpha_j*distances[jl]

            elif link == 'wards':
            
                for lk in clust.keys():
                    if lk not in (ik,jk,currentclustid):
                        alpha_i = float(clust[ik].size+clust[lk].size)/ \
                                  (clust[ik].size+clust[jk].size+clust[lk].size)
                        alpha_j = float(clust[jk].size+clust[lk].size)/ \
                                  (clust[ik].size+clust[jk].size+clust[lk].size)
                        beta = -float(clust[lk].size)/(clust[ik].size+clust[jk].size+clust[lk].size)
                        jl = (jk,lk) if jk>lk else (lk,jk)
                        il = (ik,lk) if ik>lk else (lk,ik)
                        distances[(lk,currentclustid)] = alpha_i*distances[il]+ \
                                  alpha_j*distances[jl]+beta*distances[(ik,jk)]

            elif link == 'centroid':
            
                for lk in clust.keys():
                    if lk not in (ik,jk,currentclustid):
                        alpha_i = float(clust[ik].size)/ \
                                  (clust[ik].size+clust[jk].size)
                        alpha_j = float(clust[jk].size)/ \
                                  (clust[ik].size+clust[jk].size)
                        beta = -float(clust[ik].size*clust[jk].size)/ \
                                ((clust[ik].size+clust[jk].size)**2)
                        jl = (jk,lk) if jk>lk else (lk,jk)
                        il = (ik,lk) if ik>lk else (lk,ik)
                        distances[(lk,currentclustid)] = alpha_i*distances[il]+ \
                                  alpha_j*distances[jl]+beta*distances[(ik,jk)]

            else:

                 progress.pushInfo(self.tr("Link function invalid/not found"))
                              
            # delete deprecated clusters
            del clust[ik]
            del clust[jk]
            
            # cluster ids that weren't in the original set are negative
            progress.setProgress(int(90*currentclustid/(k-numPoints)))
            currentclustid-=1

        progress.pushInfo(self.tr("Cluster tree computed"))

        return [c.members for c in list(clust.values())]

    def hcluster_slink(self, progress, points, pz, k, d, manhattan=False):

        def findClusterMembers(Pi,keys,ik,clusters):
            members = []
            for i in (i for i,jk in enumerate(Pi) if jk==ik):
                if keys[i] not in [x for y in clusters for x in y]:
                    members.append(keys[i])
                members += findClusterMembers(Pi,keys,i,clusters)
            return members

        numPoints = len(points)
        keys = list(points.keys())
        Pi = [None]*numPoints
        Lambda = [None]*numPoints
        M = [None]*numPoints
        iks = []
        clusters = []
        
        # Initialize SLINK algorithm
        Pi[0] = 0
        Lambda[0] = float_info.max
        cluster_sample=Cluster_node(d=d,pz=pz)
        
        # Iterate over vertices (called OTUs)
        for i in range(1,numPoints):
            Pi[i] = i
            Lambda[i] = float_info.max
            M[:i] = [cluster_sample.getDistance(points[keys[p]],points[keys[i]], \
                     manhattan) for p in range(i)]
            for p in range(i):
                if Lambda[p]>=M[p]:
                    M[Pi[p]] = min(M[Pi[p]],Lambda[p])
                    Lambda[p] = M[p]
                    Pi[p] = i
                else:
                    M[Pi[p]] = min(M[Pi[p]],M[p])
            for p in range(i):
                if Lambda[p]>=Lambda[Pi[p]]:
                    Pi[p] = i
            progress.setProgress(int(90*i/numPoints))

        progress.pushInfo("Pi: "+str(Pi))
        progress.pushInfo("Lambda: "+str(Lambda))

        # Identify clusters in pointer representation
        for clusterIndex in range(1,k):
            closest = float_info.min
            
            for p in range(numPoints-1):
                if Lambda[p]>closest:
                    ik = p
                    closest = Lambda[p]
            Lambda[ik] = float_info.min
            iks.append(ik)

        iks.reverse()
        
        for ik in iks:
            clusters.append([keys[ik]]+findClusterMembers(Pi,keys,ik,clusters))
            
        # assign remaining points to the last cluster
        clusters.append([p for p in keys if p not in [x for y in clusters for x in y]])

        progress.setProgress(90)
        progress.pushInfo("Clusters: "+str(clusters))

        progress.pushInfo(self.tr("Cluster tree computed"))

        return clusters

    def hcluster_clink(self, progress, points, pz, k, d, manhattan=False):

        def findClusterMembers(Pi,keys,ik,clusters):
            members = []
            for i in (i for i,jk in enumerate(Pi) if jk==ik):
                if keys[i] not in [x for y in clusters for x in y]:
                    members.append(keys[i])
                members += findClusterMembers(Pi,keys,i,clusters)
            return members

        numPoints = len(points)
        keys = list(points.keys())
        Pi = [None]*numPoints
        Lambda = [None]*numPoints
        M = [None]*numPoints
        iks = []
        clusters = []
        
        # Initialize CLINK algorithm
        Pi[0] = 0
        Lambda[0] = float_info.max
        cluster_sample=Cluster_node(d=d,pz=pz)
        
        # Iterate over vertices (called OTUs)
        for i in range(1,numPoints):
            Pi[i] = i
            Lambda[i] = float_info.max
            M[:i] = [cluster_sample.getDistance(points[keys[p]],points[keys[i]], \
                     manhattan) for p in range(i)]
            for p in range(i):
                if Lambda[p]<M[p]:
                    M[Pi[p]] = max(M[Pi[p]],M[p])
                    M[p] = float_info.max
            a = i-1
            for p in range(i):
                if Lambda[i-p-1]>=M[Pi[i-p-1]]:
                    if M[i-p-1]<M[a]: a = i-p-1
                else:
                    M[i-p-1] = float_info.max
            b = Pi[a]
            c = Lambda[a]
            Pi[a] = i
            Lambda[a] = M[a]
            if a<i-1:
                while b<i-1:
                    d = Pi[b]
                    e = Lambda[b]
                    Pi[b] = i
                    Lambda[b] = c
                    b = d
                    c = e
                if b==i-1:
                    Pi[b] = i
                    Lambda[b] = c
            for p in range(i):
                if Pi[Pi[p]]==i:
                    if Lambda[p]>=Lambda[Pi[p]]: Pi[p] = i
            progress.setProgress(int(90*i/numPoints))

        progress.pushInfo("Pi: "+str(Pi))
        progress.pushInfo("Lambda: "+str(Lambda))

        # Identify clusters in pointer representation
        for clusterIndex in range(1,k):
            closest = float_info.min
            
            for p in range(numPoints-1):
                if Lambda[p]>closest:
                    ik = p
                    closest = Lambda[p]
            Lambda[ik] = float_info.min
            iks.append(ik)

        iks.reverse()
        
        for ik in iks:
            clusters.append([keys[ik]]+findClusterMembers(Pi,keys,ik,clusters))
            
        # assign remaining points to the last cluster
        clusters.append([p for p in keys if p not in [x for y in clusters for x in y]])

        progress.setProgress(90)
        progress.pushInfo("Clusters: "+str(clusters))

        progress.pushInfo(self.tr("Cluster tree computed"))

        return clusters



# Define required cluster classes

class KMCluster:
    '''
    Class for k-means clustering
    '''
    def __init__(self, ids, centerpoint, d, pz=0):
        '''
        ids - set of integer IDs of the cluster points
        centerpoint - point of centroid
        d - distance calculation reference
        pz - percentage contribution of the z coordinate
        '''
        
        if len(ids) == 0: raise Exception("Error: Empty cluster")
        
        # The point IDs that belong to this cluster
        self.ids = ids
        
        # The center that belongs to this cluster
        self.centerpoint = centerpoint

        # Initialize distance computing
        self.d = d
        
        # The percentage contribution of the z value
        self.pz = pz
    
    def update(self, ids, centerpoint, manhattan=False):
        '''
        Returns the distance between the previous centroid coordinates
        and the new centroid coordinates 
        and updates the point IDs and the centroid coordinates
        '''
        old_centerpoint = self.centerpoint
        self.ids = ids
        self.centerpoint = centerpoint
        return self.distance2center(old_centerpoint, manhattan)
    
    def distance2center(self, point, manhattan=False):
        '''
        "2-dimensional Euclidean distance or Manhattan distance to centerpoint
        plus percentage contribution (pz) of z value.
        '''
        if manhattan:
            return (1-0.01*self.pz)* \
                (self.d.measureLine(QgsPointXY(self.centerpoint), \
                QgsPointXY(point.x(),self.centerpoint.y()))+ \
                self.d.measureLine(QgsPointXY(self.centerpoint), \
                QgsPointXY(self.centerpoint.x(),point.y()))+ \
                self.d.measureLine(QgsPointXY(point), \
                QgsPointXY(point.x(),self.centerpoint.y()))+ \
                self.d.measureLine(QgsPointXY(point), \
                QgsPointXY(self.centerpoint.x(),point.y())))+ \
                2*0.01*self.pz*abs(point.z()-self.centerpoint.z())
        else:
            return (1-0.01*self.pz)* \
                self.d.measureLine(QgsPointXY(self.centerpoint),QgsPointXY(point))+ \
                0.01*self.pz*abs(point.z()-self.centerpoint.z())
                
class Cluster_node:
    '''
    Class for hierarchical clustering
    '''
    def __init__(self, members=[], d=None, pz=0):
        self.members = members
        self.size = len(members)
        self.d = d
        self.pz = pz

    def getDistance(self, point1, point2, manhattan=False):
        '''
        2-dimensional Euclidean distance or Manhattan distance between points 1 and 2
        plus percentage contribution (pz) of z value.
        '''
        if manhattan:
            return (1-0.01*self.pz)*(self.d.measureLine(QgsPointXY(point1), \
                QgsPointXY(point2.x(),point1.y()))+ \
                self.d.measureLine(QgsPointXY(point1), \
                QgsPointXY(point1.x(),point2.y()))+ \
                self.d.measureLine(QgsPointXY(point2), \
                QgsPointXY(point2.x(),point1.y()))+ \
                self.d.measureLine(QgsPointXY(point2), \
                QgsPointXY(point1.x(),point2.y())))+ \
                2*0.01*self.pz*abs(point1.z()-point2.z())
        else:
            return (1-0.01*self.pz)* \
                self.d.measureLine(QgsPointXY(point1),QgsPointXY(point2))+ \
                0.01*self.pz*abs(point1.z()-point2.z())
