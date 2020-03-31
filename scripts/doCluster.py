##Points=vector
##SelectedFeaturesOnly=boolean False
##Cluster_Type=selection K-Means;Hierarchical
##RandomSeed=number 1
##Linkage=selection ;Ward's;Single;Complete;Average
##Distance_Type=selection Euclidean;Manhattan
##NumberOfClusters=number 2


# Import required libraries

from PyQt4.QtCore import QVariant
from qgis.core import QGis, QgsFeature, QgsField, QgsPoint, QgsDistanceArea 
from math import sqrt,fsum
from sys import float_info
from processing.core.GeoAlgorithmExecutionException import *
from processing.tools.vector import VectorWriter
import random


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


# Define required functions for each clustering algorithm
    
def kmeans(points, k, d, cutoff=10*float_info.epsilon, manhattan=False):

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

def hcluster_average(points, k, d, manhattan=False):

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

def hcluster_single(points, k, d, manhattan=False):

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

def hcluster_wards(points, k, d, manhattan=False):

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

def hcluster_complete(points, k, d, manhattan=False):

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


# Proceed with the script

if RandomSeed<1:
    raise GeoAlgorithmExecutionException("Error initializing cluster analysis:\nRandom seed must be positive number")
if NumberOfClusters<2:
    raise GeoAlgorithmExecutionException("Error initializing cluster analysis:\nNumber of Clusters must be at least 2")

random.seed(RandomSeed)

vlayer = processing.getObject(Points)
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
    clusters = kmeans(points,NumberOfClusters,d,10*float_info.epsilon,Distance_Type==1)
    del points
    cluster_id = {}
    for idx,cluster in enumerate(clusters):
        for key in cluster.ids:
            cluster_id[key] = idx
else:
    # Hierarchical clustering
    if Linkage==1:
        clusters = hcluster_wards(points,NumberOfClusters,d,Distance_Type==1)
    elif Linkage==2:
        clusters = hcluster_single(points,NumberOfClusters,d,Distance_Type==1)
    elif Linkage==3:
        clusters = hcluster_complete(points,NumberOfClusters,d,Distance_Type==1)
    elif Linkage==4:
        clusters = hcluster_average(points,NumberOfClusters,d,Distance_Type==1)
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
