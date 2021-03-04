number_sample_points = 250

import random

from qgis.core import (QgsPoint,QgsPointXY,Qgis,QgsTask,QgsMessageLog)

from math import floor,ceil,sqrt
from sys import float_info

MESSAGE_CATEGORY = 'ClusterPoints: Preparation'


class CFTask(QgsTask):
    
    def __init__(self, description, data, agglomeration_percentile=0,
                 d = None, pa = 0, manhattan = False):
        super().__init__(description, QgsTask.CanCancel)
        self.__data = data
        self.__agglomeration_percentile = agglomeration_percentile
        
        self.d = d
        self.pa = pa
        self.manhattan = manhattan
        self.size = 0

    def cancel(self):
        QgsMessageLog.logMessage("Preparation task cancelled",
            MESSAGE_CATEGORY, Qgis.Critical)
        super().cancel()

    def run(self):
        """
        Execution of task
        """

        self.derive_cf_radius()
        return self.create_blobs()

    def finished(self,result):
        """
        Called upon finish of execution
        """
        
        if result:
             QgsMessageLog.logMessage(self.tr("Successful execution of preparation task"),
                       MESSAGE_CATEGORY, Qgis.Success)
        else:
             QgsMessageLog.logMessage(self.tr("Execution of preparation task failed"),
                       MESSAGE_CATEGORY, Qgis.Critical)

    def derive_cf_radius(self):
    
        # draw <number_sample_points> random points 
        # to estimate mean distance between individual points
        
        if len(self.__data)>number_sample_points:
            subset = random.sample(list(self.__data.keys()),number_sample_points)
        else:
            subset = list(self.__data.keys())
        
        # average pairwise distances
        
        sample_dist = [0]*int(0.5*(len(subset)*(len(subset)+1)))
        
        for i in range(len(subset)-1,0,-1):
            ik = len(subset)-i
            for j in range(i,len(subset)):
                sample_dist[int(0.5*ik*(ik+1))+j] = \
                       self.getDistance(self.__data[subset[i]],self.__data[subset[j]])

        # sort sample distances

        sample_dist.sort()
        
        # retrieve quantile values
        
        p = (len(subset)*(len(subset)+1))/200.0*self.__agglomeration_percentile
        if p.is_integer():
            self.radius = sample_dist[int(p)]
        else:
            self.radius = (1-p%1)*sample_dist[floor(p)]+(p%1)*sample_dist[ceil(p)]
        QgsMessageLog.logMessage(self.tr("Radius for cluster features: {:.5E}".format(
                                         self.radius)),MESSAGE_CATEGORY, Qgis.Info)
        
    def create_blobs(self):
    
        # assign cluster feature blobs with members and centroids
        
        self.derive_cf_radius
        
        self.blobs = []
        
        for key in self.__data.keys():
        
            if self.isCanceled():
                return False
            
            dist = float_info.max
            for j in range(len(self.blobs)):
                dist_j = self.blobs[j].distance2center(self.__data[key])
                if dist_j<dist:
                    add_j = j
                    dist = dist_j
            if dist<self.radius:
                self.blobs[add_j].add_point(key,self.__data[key])
            else:
                self.blobs.append(cf_blob(self.d,self.pa,self.manhattan,
                                 [key],self.__data[key]))
                self.size += 1
        
        return True

    def return_centroids(self):
    
        # return dictionary of cluster feature centroids
    
        return dict((i,self.blobs[i].centroid) for i in range(len(self.blobs)))
        
    def return_members(self,keys):
    
        # return cluster feature members for given list of keys
    
        return [p for b in [self.blobs[key].members for key in keys] for p in b]

    def getDistance(self, point1, point2):
        '''
        2-dimensional Euclidean distance or Manhattan distance between points 1 and 2
        plus percentage contribution (pa) of attribute values
        '''
        dist = 0
        if self.manhattan:
            if self.pa < 100:
                dist += (1-0.01*self.pa)* \
                    (self.d.measureLine(QgsPointXY(point1.x(),point1.y()), \
                    QgsPointXY(point2.x(),point1.y()))+ \
                    self.d.measureLine(QgsPointXY(point1.x(),point1.y()), \
                    QgsPointXY(point1.x(),point2.y()))+ \
                    self.d.measureLine(QgsPointXY(point2.x(),point2.y()), \
                    QgsPointXY(point2.x(),point1.y()))+ \
                    self.d.measureLine(QgsPointXY(point2.x(),point2.y()), \
                    QgsPointXY(point1.x(),point2.y())))
            if self.pa > 0:
                dist += 2*0.01*self.pa*self.getAttrDistance(point1,point2)
        else:
            if self.pa < 100:
                dist += (1-0.01*self.pa)* \
                self.d.measureLine(QgsPointXY(point1.x(),point1.y()), \
                QgsPointXY(point2.x(),point2.y()))
            if self.pa > 0:
                dist += 0.01*self.pa*self.getAttrDistance(point1,point2)
        return dist
                
    def getAttrDistance(self, point1, point2):
        '''
        2-dimensional Euclidean distance or Manhattan distance between attributes
        of points 1 and 2
        '''
        attr_size = min(point1.attr_size,point2.attr_size)
        if attr_size == 0:
            return 0
        dist = 0
        if self.manhattan:
            for i in range(attr_size):
                dist += abs(point1.attributes[i]-point2.attributes[i])
        else:
            for i in range(attr_size):
                dist += (point1.attributes[i]-point2.attributes[i])* \
                        (point1.attributes[i]-point2.attributes[i])
            dist = sqrt(dist)
        return dist


class cf_blob:

    def __init__(self, d, pa, manhattan, members, centroid):
        """!
        @brief Constructor of single cluster feature (blob).
        
        @param[in] d (QgsDistanceArea): Qgs Measurement object.
        @param[in] pa (uint): Percentage contribution of attribute values.
        @param[in] manhattan (bool): Bool for use of Manhattan distance.
        @param[in] members (list): List of member keys.
        @param[in] members (QgsPoint): Qgs Point with initial centroid
        """

        self.d = d
        self.pa = pa
        self.manhattan = manhattan
        self.members = members
        self.size = len(members)
        self.centroid = centroid
        
    def update_centroid(self,point):

        centroid = QgsPointXY(self.centroid.x()+(1.0/self.size)*(point.x()-self.centroid.x()), \
                              self.centroid.y()+(1.0/self.size)*(point.y()-self.centroid.y()))
        centroid = Cluster_point(centroid)
        centroid.replaceAttributes([self.centroid.attributes[j]+ \
                                    (1.0/self.size)*(point.attributes[j]- \
                                    self.centroid.attributes[j]) for j in \
                                    range(point.attr_size)])
        self.centroid = centroid
               
    def add_point(self,index,point):
    
        self.members.append(index)
        self.size+=1
        self.update_centroid(point)

    def distance2center(self, point):
        '''
        2-dimensional Euclidean distance or Manhattan distance to centerpoint
        plus percentage contribution (pa) of attribute values
        '''
        dist = 0
        if self.manhattan:
            if self.pa < 100:
                dist += (1-0.01*self.pa)* \
                    (self.d.measureLine(QgsPointXY(self.centroid.x(),self.centroid.y()), \
                    QgsPointXY(point.x(),self.centroid.y()))+ \
                    self.d.measureLine(QgsPointXY(self.centroid.x(),self.centroid.y()), \
                    QgsPointXY(self.centroid.x(),point.y()))+ \
                    self.d.measureLine(QgsPointXY(point.x(),point.y()), \
                    QgsPointXY(point.x(),self.centroid.y()))+ \
                    self.d.measureLine(QgsPointXY(point.x(),point.y()), \
                    QgsPointXY(self.centroid.x(),point.y())))
            if self.pa > 0:
                dist += 2*0.01*self.pa*self.attrDistance2center(point)
        else:
            if self.pa < 100:
                dist += (1-0.01*self.pa)* \
                    self.d.measureLine(QgsPointXY(self.centroid.x(),self.centroid.y()), \
                    QgsPointXY(point.x(),point.y()))
            if self.pa > 0:
                dist += 0.01*self.pa*self.attrDistance2center(point)
        return dist
                
    def attrDistance2center(self, point):
        '''
        2-dimensional Euclidean distance or Manhattan distance to centerpoint,
        only derived from attributes
        '''
        attr_size = min(point.attr_size,self.centroid.attr_size)
        if attr_size == 0:
            return 0
        dist = 0
        if self.manhattan:
            for i in range(attr_size):
                dist += abs(point.attributes[i]-self.centroid.attributes[i])
        else:
            for i in range(attr_size):
                dist += (point.attributes[i]-self.centroid.attributes[i])* \
                        (point.attributes[i]-self.centroid.attributes[i])
            dist = sqrt(dist)
        return dist


class Cluster_point(QgsPoint):
    '''
    Class extends QgsPoint with attribute values
    '''
    def __init__(self,point):
        super(Cluster_point, self).__init__(point)
        self.attr_size = 0
        self.attributes = []
    
    def addAttribute(self,v):
        self.attr_size += 1
        self.attributes.append(v)
        
    def replaceAttributes(self,v):
        self.attr_size = len(v)
        self.attributes = v
