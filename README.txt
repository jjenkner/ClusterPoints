Cluster Points

Introduction

Cluster Points offers a set of cluster tools for an automatical grouping of a point layer in QGIS minimizing the intra-group distance and maximizing the between-group distance: There are two inherently different algorithms the user may choose from. First, there is K-means clustering which randomly initializes the cluster centers and reassigns cluster members until the centers stop moving. Second, there is agglomerative hierarchical clustering which starts with as many clusters as there are points and gradually merges individual clusters according to a certain link function. Cluster Points works with input shapefiles with a new field "Cluster_ID" appended to the attribute table as output.

Cluster Points is a free software and offered without guarantee or warranty. You 
can redistribute it and/or modify it under the terms of version 3 of the GNU 
General Public License. Bug reports or suggestions are welcome at the e-mail address "jjenkner@web.de".

Note that some code segments have been taken from the built-in ftools and the MMQGIS plugin. This plugin was started during the project phase of a GIS-Analyst training course in Berlin (GIS-Trainer). I acknowledge the assistance of the GIS-Trainer tutors and my classmates Juliane, Bennet and Sebastian.

User Manual

The Clustering Tool offers spatial clustering of a point layer based on the mutual distances between points.
Basically, the inter-class distances are maximized whereas the intra-class distances are minimized.
The user always needs to define the number of clusters which is sought (minimum is 2). Also, the user needs to decide between the Euclidean distance and the Manhattan distance within the cluster computation. Since the K-means algorithm is based on a random initialization, a random seed can be specified for this type of clustering to guarantee stable results. For hierachical clustering a linkage, i.e. link function, must be specified which determines where the distances are measured between individual clusters.

Two inherently different clustering types are available:

K-means Clustering

K-means is an iterative algorithm which is randomly initialized. Here, the standard algorithm version of Lloyd is implemented which consists of three steps. First, a user-defined number of clusters is initialized by randomly choosing points in the input layer as their centers. Then the iteration starts with alternating assignment and updating steps. During the assignment, the points are assigned to the closest
cluster centers. During the updating, the cluster centers are recalculated from the members which were assigned to a certain cluster. The algorithm stops, as soon the cluster centers do not move any more. Note that the K-means algorithm is comparatively fast, but it slightly depends on its random initialization and hence does not always produce the same results. To this end, a predefined random seed is used, to guarantee the results to be the same for the same seed.

Hierarchical Clustering

The clustering here is agglomerative, i.e. it starts with as many clusters as there are points and gradually merges the two closest clusters to a composite cluster. The user needs to choose a link function which describes the way how the two closest clusters are found. He may choose from Ward's Linkage as well as Single, Complete and Average Linkage. The definitions of the individual link functions can be found online. By gradually merging clusters, the so-called cluster tree is built which shows when individual clusters were merged exactly. Each time two clusters are merged, the distances of the new composite cluster to all the other clusters need to be updated. To do this as efficient as possible, the Lance-Williams method is used here which quickly updates the underlying distance matrix. Note that the Lance-Williams
method is unequivocal, but it is still computationally expensive, if the number of points is high. The output always is a new field/attribute labelled "Cluster ID" appended to the input shapefile to indicate cluster membership of individual points.














