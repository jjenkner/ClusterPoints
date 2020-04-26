import numpy

from copy import copy
from enum import IntEnum
from sys import float_info

from qgis.core import QgsPointXY,QgsPoint,QgsDistanceArea



class cfnode_type(IntEnum):
    """!
    @brief Enumeration of CF-Node types that are used by CF-Tree.
    
    @see cfnode
    @see cftree
    
    """
    
    ## Undefined node.
    CFNODE_DUMMY = 0
    
    ## Leaf node hasn't got successors, only entries.
    CFNODE_LEAF = 1
    
    ## Non-leaf node has got successors and hasn't got entries.
    CFNODE_NONLEAF = 2


class cfentry:
    """!
    @brief Clustering feature representation.
    
    @see cfnode
    @see cftree
    
    """

    @property
    def number_points(self):
        """!
        @brief Returns number of points that are encoded.
        
        @return (uint) Number of encoded points.
        
        """
        return self.__number_points

    @property
    def linear_sum(self):
        """!
        @brief Returns linear sum.
        
        @return (list) Linear sum.
        
        """
        
        return self.__linear_sum

    @property
    def square_sum(self):
        """!
        @brief Returns square sum.
        
        @return (double) Square sum.
        
        """
        return self.__square_sum


    def __init__(self, number_points, linear_sum, square_sum, d = None, pz = 0, manhattan = False):
        """!
        @brief CF-entry constructor.
        
        @param[in] number_points (uint): Number of objects that is represented by the entry.
        @param[in] linear_sum (list): Linear sum of values that represent objects in each dimension.
        @param[in] square_sum (double): Square sum of values that represent objects.
        @param[in] d (QgsDistanceArea): Qgs Measurement object.
        @param[in] pz (uint): Percentage of z-coordinate.
        @param[in] manhattan (bool): Bool for use of Manhattan distance.
        
        """
        
        self.__number_points = number_points
        self.__linear_sum = numpy.array(linear_sum)
        self.__square_sum = square_sum
        
        self.__d = d
        self.__pz = min(100,max(0,pz))
        self.__manhattan = manhattan
        
        self.__centroid = None
        self.__radius = None
        self.__diameter = None


    def __copy__(self):
        """!
        @returns (cfentry) Makes copy of the CF-entry instance.
        
        """
        return cfentry(self.__number_points, self.__linear_sum, self.__square_sum, \
                       self.__d, self.__pz, self.__manhattan)


    def __repr__(self):
        """!
        @return (string) Returns CF-entry representation.
        
        """
        return "CF-Entry (N: '%s', LS: '%s', D: '%s')" % \
               (self.number_points, self.linear_sum, str(self.get_diameter()))


    def __str__(self):
        """!
        @brief Default cfentry string representation.
        
        """
        return self.__repr__()


    def __add__(self, entry):
        """!
        @brief Overloaded operator add. Performs addition of two clustering features.
        
        @param[in] entry (cfentry): Entry that is added to the current.
        
        @return (cfentry) Result of addition of two clustering features.
        
        """
        
        number_points = self.number_points + entry.number_points
        result_linear_sum = numpy.add(self.linear_sum, entry.linear_sum)
        result_square_sum = self.square_sum + entry.square_sum
        
        return cfentry(number_points, result_linear_sum, result_square_sum, \
                       self.__d, self.__pz, self.__manhattan)


    def __eq__(self, entry):
        """!
        @brief Overloaded operator eq. 
        @details Performs comparison of two clustering features.
        
        @param[in] entry (cfentry): Entry that is used for comparison with current.
        
        @return (bool) True is both clustering features are equals in line with tolerance, otherwise False.
        
        """
                
        tolerance = 0.00001
        
        result = (self.__number_points == entry.number_points)
        result &= ((self.square_sum + tolerance > entry.square_sum) and (self.square_sum - tolerance < entry.square_sum))
        
        for index_dimension in range(0, len(self.linear_sum)):
            result &= ((self.linear_sum[index_dimension] + tolerance > entry.linear_sum[index_dimension]) and (self.linear_sum[index_dimension] - tolerance < entry.linear_sum[index_dimension]))
        
        return result


    def get_distance(self, entry):
        """!
        @brief Calculates distance between two clusters in line with measurement type.
        
        @return (double) Distance between two clusters.
        
        """

        p = entry.get_centroid()
        q = self.get_centroid()
        
        if self.__manhattan:
            return (1-0.01*self.__pz)* \
                (self.__d.measureLine(QgsPointXY(p[0],p[1]), \
                QgsPointXY(p[0],q[1]))+ \
                self.__d.measureLine(QgsPointXY(p[0],p[1]), \
                QgsPointXY(q[0],p[1]))+ \
                self.__d.measureLine(QgsPointXY(q[0],q[1]), \
                QgsPointXY(p[0],q[1]))+ \
                self.__d.measureLine(QgsPointXY(q[0],q[1]), \
                QgsPointXY(q[0],p[1])))+ \
                2*0.01*self.__pz*abs(p[2]-q[2])
        else:
            return self.__d.measureLine(QgsPointXY(p[0],p[1]),QgsPointXY(q[0],q[1]))+ \
                0.01*self.__pz*abs(p[2]-q[2])


    def get_centroid(self):
        """!
        @brief Calculates centroid of cluster that is represented by the entry. 
        @details It's calculated once when it's requested after the last changes.
        
        @return (array_like) Centroid of cluster that is represented by the entry.
        
        """
        
        if self.__centroid is not None:
            return self.__centroid

        self.__centroid = numpy.divide(self.linear_sum, self.number_points)
        return self.__centroid
    
    
    def get_radius(self):
        """!
        @brief Calculates radius of cluster that is represented by the entry.
        @details It's calculated once when it's requested after the last changes.
        
        @return (double) Radius of cluster that is represented by the entry.
        
        """
        
        if self.__radius is not None:
            return self.__radius

        N = self.number_points
        centroid = self.get_centroid()
        
        radius_part_1 = self.square_sum
        radius_part_2 = 2.0 * numpy.dot(self.linear_sum, centroid)
        radius_part_3 = N * numpy.dot(centroid, centroid)
        
        self.__radius = ((1.0 / N) * (radius_part_1 - radius_part_2 + radius_part_3)) ** 0.5
        return self.__radius


    def get_diameter(self):
        """!
        @brief Calculates diameter of cluster that is represented by the entry.
        @details It's calculated once when it's requested after the last changes.
        
        @return (double) Diameter of cluster that is represented by the entry.
        
        """
        
        if self.__diameter is not None:
            return self.__diameter

        diameter_part = self.square_sum * self.number_points - 2.0 * numpy.dot(self.linear_sum, self.linear_sum) + self.square_sum * self.number_points

        if diameter_part < 0.000000001:
            self.__diameter = 0.0
        else:
            self.__diameter = (diameter_part / (self.number_points * (self.number_points - 1))) ** 0.5

        return self.__diameter


    def __get_average_inter_cluster_distance(self, entry):
        """!
        @brief Calculates average inter cluster distance between current and specified clusters.
        
        @param[in] entry (cfentry): Clustering feature to which distance should be obtained.
        
        @return (double) Average inter cluster distance.
        
        """
        
        linear_part_distance = numpy.dot(self.linear_sum, entry.linear_sum)

        return ((entry.number_points * self.square_sum - 2.0 * linear_part_distance + self.number_points * entry.square_sum) / (self.number_points * entry.number_points)) ** 0.5


    def __get_average_intra_cluster_distance(self, entry):
        """!
        @brief Calculates average intra cluster distance between current and specified clusters.
        
        @param[in] entry (cfentry): Clustering feature to which distance should be obtained.
        
        @return (double) Average intra cluster distance.
        
        """
        
        linear_part_first = numpy.add(self.linear_sum, entry.linear_sum)
        linear_part_second = linear_part_first
        
        linear_part_distance = numpy.dot(linear_part_first, linear_part_second)
        
        general_part_distance = 2.0 * (self.number_points + entry.number_points) * (self.square_sum + entry.square_sum) - 2.0 * linear_part_distance
        
        return (general_part_distance / ((self.number_points + entry.number_points) * (self.number_points + entry.number_points - 1.0))) ** 0.5
    
    
    def __get_variance_increase_distance(self, entry):
        """!
        @brief Calculates variance increase distance between current and specified clusters.
        
        @param[in] entry (cfentry): Clustering feature to which distance should be obtained.
        
        @return (double) Variance increase distance.
        
        """
                
        linear_part_12 = numpy.add(self.linear_sum, entry.linear_sum)
        variance_part_first = (self.square_sum + entry.square_sum) - \
            2.0 * numpy.dot(linear_part_12, linear_part_12) / (self.number_points + entry.number_points) + \
            (self.number_points + entry.number_points) * numpy.dot(linear_part_12, linear_part_12) / (self.number_points + entry.number_points)**2.0
        
        linear_part_11 = numpy.dot(self.linear_sum, self.linear_sum)
        variance_part_second = -(self.square_sum - (2.0 * linear_part_11 / self.number_points) + (linear_part_11 / self.number_points))
        
        linear_part_22 = numpy.dot(entry.linear_sum, entry.linear_sum)
        variance_part_third = -(entry.square_sum - (2.0 / entry.number_points) * linear_part_22 + entry.number_points * (1.0 / entry.number_points ** 2.0) * linear_part_22)

        return variance_part_first + variance_part_second + variance_part_third
        

class cfnode:
    """!
    @brief Representation of node of CF-Tree.
    
    """
    
    def __init__(self, feature, parent):
        """!
        @brief Constructor of abstract CF node.
        
        @param[in] feature (cfentry): Clustering feature of the created node.
        @param[in] parent (cfnode): Parent of the created node.
        
        """
        
        ## Clustering feature of the node.
        self.feature = copy(feature)

        ## Pointer to the parent node (None for root).
        self.parent = parent
        
        ## Type node (leaf or non-leaf).
        self.type = cfnode_type.CFNODE_DUMMY
    
    
    def __repr__(self):
        """!
        @return (string) Default representation of CF node.
        
        """
        
        return 'CF node %s, parent %s, feature %s' % (hex(id(self)), self.parent, self.feature)


    def __str__(self):
        """!
        @return (string) String representation of CF node.
        
        """
        return self.__repr__()
    
    
    def get_distance(self, node):
        """!
        @brief Calculates distance between nodes in line with specified type measurement.
        
        @return (double) Distance between two nodes.
        
        """
        
        return self.feature.get_distance(node.feature)
    

class non_leaf_node(cfnode):
    """!
    @brief Representation of clustering feature non-leaf node.
    
    """ 
    
    @property
    def successors(self):
        """!
        @return (list) List of successors of the node.
        
        """
        return self.__successors
    
    
    def __init__(self, feature, parent, successors):
        """!
        @brief Create CF Non-leaf node.
        
        @param[in] feature (cfentry): Clustering feature of the created node.
        @param[in] parent (non_leaf_node): Parent of the created node.
        @param[in] successors (list): List of successors of the node.
        
        """
                
        super().__init__(feature, parent)
        
        ## Node type in CF tree that is CFNODE_NONLEAF for non leaf node.
        self.type = cfnode_type.CFNODE_NONLEAF
        
        self.__successors = successors
    
    
    def __repr__(self):
        """!
        @return (string) Representation of non-leaf node representation.
        
        """   
        return 'Non-leaf node %s, parent %s, feature %s, successors: %d' % (hex(id(self)), self.parent, self.feature, len(self.successors))
    
    
    def __str__(self):
        """!
        @return (string) String non-leaf representation.
        
        """
        return self.__repr__()
    
    
    def insert_successor(self, successor):
        """!
        @brief Insert successor to the node.
        
        @param[in] successor (cfnode): Successor for adding.
        
        """
        
        self.feature += successor.feature
        self.successors.append(successor)
        
        successor.parent = self


    def merge(self, node):
        """!
        @brief Merge non-leaf node to the current.
        
        @param[in] node (non_leaf_node): Non-leaf node that should be merged with current.
        
        """
                
        self.feature += node.feature
        
        for child in node.successors:
            child.parent = self
            self.successors.append(child)
    
    
    def get_farthest_successors(self):
        """!
        @brief Find pair of farthest successors of the node in line with measurement type.
        
        @return (list) Pair of farthest successors represented by list [cfnode1, cfnode2].
        
        """
        
        farthest_node1 = None
        farthest_node2 = None
        farthest_distance = 0.0
        
        for i in range(0, len(self.successors)):
            candidate1 = self.successors[i]
            
            for j in range(i + 1, len(self.successors)):
                candidate2 = self.successors[j]
                candidate_distance = candidate1.get_distance(candidate2)
                
                if candidate_distance > farthest_distance:
                    farthest_distance = candidate_distance
                    farthest_node1 = candidate1
                    farthest_node2 = candidate2
        
        return [farthest_node1, farthest_node2]
    
    
    def get_nearest_successors(self):
        """!
        @brief Find pair of nearest successors of the node in line with measurement type.
        
        @return (list) Pair of nearest successors represented by list.
        
        """
                
        nearest_node1 = None
        nearest_node2 = None
        nearest_distance = float("Inf")
        
        for i in range(0, len(self.successors)):
            candidate1 = self.successors[i]
            
            for j in range(i + 1, len(self.successors)):
                candidate2 = self.successors[j]
                candidate_distance = candidate1.get_distance(candidate2)
                
                if candidate_distance < nearest_distance:
                    nearest_distance = candidate_distance
                    nearest_node1 = candidate1
                    nearest_node2 = candidate2
        
                return [nearest_node1, nearest_node2]


class leaf_node(cfnode):
    """!
    @brief Represents clustering feature leaf node.
    
    """
    
    @property
    def entries(self):
        """!
        @return (list) List of leaf nodes.
        
        """
        return self.__entries
    
    
    def __init__(self, feature, parent, entries):
        """!
        @brief Create CF Leaf node.
        
        @param[in] feature (cfentry): Clustering feature of the created node.
        @param[in] parent (non_leaf_node): Parent of the created node.
        @param[in] entries (list): List of entries of the node.
        
        """
        
        super().__init__(feature, parent)
        
        ## Node type in CF tree that is CFNODE_LEAF for leaf node.
        self.type = cfnode_type.CFNODE_LEAF
        
        self.__entries = entries   # list of clustering features
        
    
    def __repr__(self):
        """!
        @return (string) Default leaf node represenation.
        
        """
        text_entries = "\n"
        for entry in self.entries:
            text_entries += "\t" + str(entry) + "\n"
        
        return "Leaf-node: '%s', parent: '%s', feature: '%s', entries: '%d'" % \
               (str(hex(id(self))), self.parent, self.feature, len(self.entries))
    
    
    def __str__(self):
        """!
        @return (string) String leaf node representation.
        
        """
        return self.__repr__()
    
    
    def insert_entry(self, entry):
        """!
        @brief Insert new clustering feature to the leaf node.
        
        @param[in] entry (cfentry): Clustering feature.
        
        """

        self.feature += entry
        self.entries.append(entry)


    def merge(self, node):
        """!
        @brief Merge leaf node to the current.
        
        @param[in] node (leaf_node): Leaf node that should be merged with current.
        
        """
        
        self.feature += node.feature
        
        # Move entries from merged node
        for entry in node.entries:
            self.entries.append(entry)


    def get_farthest_entries(self):
        """!
        @brief Find pair of farthest entries of the node.
        
        @return (list) Pair of farthest entries of the node that are represented by list.
        
        """
        
        farthest_entity1 = None
        farthest_entity2 = None
        farthest_distance = 0
        
        for i in range(0, len(self.entries)):
            candidate1 = self.entries[i]
            
            for j in range(i + 1, len(self.entries)):
                candidate2 = self.entries[j]
                candidate_distance = candidate1.get_distance(candidate2)
                
                if candidate_distance > farthest_distance:
                    farthest_distance = candidate_distance
                    farthest_entity1 = candidate1
                    farthest_entity2 = candidate2
        
        return [farthest_entity1, farthest_entity2]


    def get_nearest_index_entry(self, entry):
        """!
        @brief Find nearest index of nearest entry of node for the specified entry.
        
        @return (uint) Index of nearest entry of node for the specified entry.
        
        """
        
        minimum_distance = float('Inf')
        nearest_index = -1
        
        for candidate_index in range(0, len(self.entries)):
            candidate_distance = self.entries[candidate_index].get_distance(entry)
            if candidate_distance < minimum_distance:
                minimum_distance = candidate_distance
                nearest_index = candidate_index
        
        return nearest_index


    def get_nearest_entry(self, entry):
        """!
        @brief Find nearest entry of node for the specified entry.
        
        @return (cfentry) Nearest entry of node for the specified entry.
        
        """
        
        min_key = lambda cur_entity: cur_entity.get_distance(entry)
        return min(self.entries, key=min_key)


class cftree:
    """!
    @brief CF-Tree representation.
    @details A CF-tree is a height-balanced tree with two parameters: branching factor and threshold.
    
    """

    @property
    def root(self):
        """!
        @return (cfnode) Root of the tree.
        
        """
        return self.__root


    @property
    def leafes(self):
        """!
        @return (list) List of all leaf nodes in the tree.
        
        """
        return self.__leafes


    @property
    def amount_nodes(self):
        """!
        @return (unit) Number of nodes (leaf and non-leaf) in the tree.
        
        """
        return self.__amount_nodes


    @property
    def amount_entries(self):
        """!
        @return (uint) Number of entries in the tree.
        
        """
        return self.__amount_entries


    @property
    def height(self):
        """!
        @return (uint) Height of the tree.
        
        """
        return self.__height


    @property
    def branch_factor(self):
        """!
        @return (uint) Branching factor of the tree.
        @details Branching factor defines maximum number of successors in each non-leaf node.
        
        """
        return self.__branch_factor


    @property
    def threshold(self):
        """!
        @return (double) Threshold of the tree that represents maximum diameter of sub-clusters that is formed by leaf node entries.
        
        """
        return self.__threshold


    @property
    def max_entries(self):
        """!
        @return (uint) Maximum number of entries in each leaf node.
        
        """
        return self.__max_entries


    @property
    def manhattan(self):
        """!
        @return (manhattan) Bool for use of Manhattan distance.
        
        """
        return self.__manhattan


    def __init__(self, branch_factor, max_entries, threshold, d = None, pz = 0, manhattan = False):
        """!
        @brief Create CF-tree.
        
        @param[in] branch_factor (uint): Maximum number of children for non-leaf nodes.
        @param[in] max_entries (uint): Maximum number of entries for leaf nodes.
        @param[in] threshold (double): Maximum diameter of feature clustering for each leaf node.
        @param[in] d (QgsDistanceArea): Qgs Measurement object.
        @param[in] pz (uint): Percentage of z-coordinate.
        @param[in] manhattan (bool): Bool for use of Manhattan distance.
        
        """

        self.__root = None

        self.__branch_factor = branch_factor  # maximum number of children
        if self.__branch_factor < 2:
            self.__branch_factor = 2
        
        self.__threshold = threshold  # maximum diameter of sub-clusters stored at the leaf nodes
        self.__max_entries = max_entries
        
        self.__leafes = []
        
        self.__d = d
        self.__pz = min(100,max(0,pz))
        self.__manhattan = manhattan
        
        # statistics
        self.__amount_nodes = 0    # root, despite it can be None.
        self.__amount_entries = 0
        self.__height = 0          # tree size with root.


    def compute_linear_sum(self, list_vector):

        dimension = 1
        linear_sum = 0.0
        point_representation = isinstance(list_vector[0],QgsPoint)
    
        if point_representation is True:
            linear_sum = [0] * 3
        
        for index_element in range(0, len(list_vector)):
            if (point_representation is True):
                linear_sum[0] += (1-0.01*self.__pz)*list_vector[index_element].x()
                linear_sum[1] += (1-0.01*self.__pz)*list_vector[index_element].y()
                linear_sum[2] = 0.01*self.__pz*list_vector[index_element].z()
            else:
                linear_sum += list_vector[index_element]

        return linear_sum
        
    
    def compute_square_sum(self, list_vector):

        square_sum = 0.0
        point_representation = isinstance(list_vector[0],QgsPoint)
        
        for index_element in range(0, len(list_vector)):
            if point_representation is True:
                square_sum += ((1-0.01*self.__pz)*list_vector[index_element].x())**2
                square_sum += ((1-0.01*self.__pz)*list_vector[index_element].y())**2
                square_sum += (0.01*self.__pz*list_vector[index_element].z())**2
            else:
                square_sum += (list_vector[index_element])**2
         
        return square_sum


    def get_level_nodes(self, level):
        """!
        @brief Traverses CF-tree to obtain nodes at the specified level.
        
        @param[in] level (uint): CF-tree level from that nodes should be returned.
        
        @return (list) List of CF-nodes that are located on the specified level of the CF-tree.
        
        """
        
        level_nodes = []
        if level < self.__height:
            level_nodes = self.__recursive_get_level_nodes(level, self.__root)
        
        return level_nodes


    def __recursive_get_level_nodes(self, level, node):
        """!
        @brief Traverses CF-tree to obtain nodes at the specified level recursively.
        
        @param[in] level (uint): Current CF-tree level.
        @param[in] node (cfnode): CF-node from that traversing is performed.
        
        @return (list) List of CF-nodes that are located on the specified level of the CF-tree.
        
        """
        
        level_nodes = []
        if level is 0:
            level_nodes.append(node)
        
        else:
            for sucessor in node.successors:
                level_nodes += self.__recursive_get_level_nodes(level - 1, sucessor)
        
        return level_nodes


    def insert_point(self, point):
        """!
        @brief Insert point that is represented by list of coordinates.
        @param[in] point (list): Point represented by list of coordinates that should be inserted to CF tree.
        """

        entry = cfentry(1, self.compute_linear_sum([point]), \
                        self.compute_square_sum([point]), self.__d, self.__pz, self.__manhattan)
        self.insert(entry)
    
    
    def insert(self, entry):
        """!
        @brief Insert clustering feature to the tree.
        
        @param[in] entry (cfentry): Clustering feature that should be inserted.
        
        """
                
        if self.__root is None:
            node = leaf_node(entry, None, [entry])
            
            self.__root = node
            self.__leafes.append(node)
            
            # Update statistics
            self.__amount_entries += 1
            self.__amount_nodes += 1
            self.__height += 1             # root has successor now
        else:
            child_node_updation = self.__recursive_insert(entry, self.__root)
            if child_node_updation is True:
                # Splitting has been finished, check for possibility to merge (at least we have already two children).
                if self.__merge_nearest_successors(self.__root) is True:
                    self.__amount_nodes -= 1


    def find_nearest_leaf(self, entry, search_node = None):
        """!
        @brief Search nearest leaf to the specified clustering feature.
        
        @param[in] entry (cfentry): Clustering feature.
        @param[in] search_node (cfnode): Node from that searching should be started, if None then search process will be started for the root.
        
        @return (leaf_node) Nearest node to the specified clustering feature.
        
        """
        
        if search_node is None:
            search_node = self.__root
        
        nearest_node = search_node
        
        if search_node.type == cfnode_type.CFNODE_NONLEAF:
            min_key = lambda child_node: child_node.feature.get_distance(entry)
            nearest_child_node = min(search_node.successors, key = min_key)
            
            nearest_node = self.find_nearest_leaf(entry, nearest_child_node)
        
        return nearest_node


    def __recursive_insert(self, entry, search_node):
        """!
        @brief Recursive insert of the entry to the tree.
        @details It performs all required procedures during insertion such as splitting, merging.
        
        @param[in] entry (cfentry): Clustering feature.
        @param[in] search_node (cfnode): Node from that insertion should be started.
        
        @return (bool) True if number of nodes at the below level is changed, otherwise False.
        
        """
        
        # None-leaf node
        if search_node.type == cfnode_type.CFNODE_NONLEAF:
            return self.__insert_for_noneleaf_node(entry, search_node)
        
        # Leaf is reached 
        else:
            return self.__insert_for_leaf_node(entry, search_node)


    def __insert_for_leaf_node(self, entry, search_node):
        """!
        @brief Recursive insert entry from leaf node to the tree.
        
        @param[in] entry (cfentry): Clustering feature.
        @param[in] search_node (cfnode): None-leaf node from that insertion should be started.
        
        @return (bool) True if number of nodes at the below level is changed, otherwise False.
        
        """
        
        node_amount_updation = False
        
        # Try to absorb by the entity
        index_nearest_entry = search_node.get_nearest_index_entry(entry)
        nearest_entry = search_node.entries[index_nearest_entry]    # get nearest entry
        merged_entry = nearest_entry + entry
        
        # Otherwise try to add new entry
        if merged_entry.get_diameter() > self.__threshold:
            # If it's not exceeded append entity and update feature of the leaf node.
            search_node.insert_entry(entry)
            
            # Otherwise current node should be splitted
            if len(search_node.entries) > self.__max_entries:
                self.__split_procedure(search_node)
                node_amount_updation = True
            
            # Update statistics
            self.__amount_entries += 1
            
        else:
            search_node.entries[index_nearest_entry] = merged_entry
            search_node.feature += entry
        
        return node_amount_updation


    def __insert_for_noneleaf_node(self, entry, search_node):
        """!
        @brief Recursive insert entry from none-leaf node to the tree.
        
        @param[in] entry (cfentry): Clustering feature.
        @param[in] search_node (cfnode): None-leaf node from that insertion should be started.
        
        @return (bool) True if number of nodes at the below level is changed, otherwise False.
        
        """
        
        node_amount_updation = False
        
        min_key = lambda child_node: child_node.get_distance(search_node)
        nearest_child_node = min(search_node.successors, key=min_key)
        
        child_node_updation = self.__recursive_insert(entry, nearest_child_node)
        
        # Update clustering feature of none-leaf node.
        search_node.feature += entry
            
        # Check branch factor, probably some leaf has been splitted and threshold has been exceeded.
        if (len(search_node.successors) > self.__branch_factor):
            
            # Check if it's aleady root then new root should be created (height is increased in this case).
            if search_node is self.__root:
                self.__root = non_leaf_node(search_node.feature, None, [search_node])
                search_node.parent = self.__root
                
                # Update statistics
                self.__amount_nodes += 1
                self.__height += 1
                
            [new_node1, new_node2] = self.__split_nonleaf_node(search_node)
            
            # Update parent list of successors
            parent = search_node.parent
            parent.successors.remove(search_node)
            parent.successors.append(new_node1)
            parent.successors.append(new_node2)
            
            # Update statistics
            self.__amount_nodes += 1
            node_amount_updation = True
            
        elif child_node_updation is True:
            # Splitting has been finished, check for possibility to merge (at least we have already two children).
            if self.__merge_nearest_successors(search_node) is True:
                self.__amount_nodes -= 1
        
        return node_amount_updation


    def __merge_nearest_successors(self, node):
        """!
        @brief Find nearest sucessors and merge them.
        
        @param[in] node (non_leaf_node): Node whose two nearest successors should be merged.
        
        @return (bool): True if merging has been successfully performed, otherwise False.
        
        """
        
        merging_result = False
        
        if node.successors[0].type == cfnode_type.CFNODE_NONLEAF:
            [nearest_child_node1, nearest_child_node2] = node.get_nearest_successors()
            
            if len(nearest_child_node1.successors) + len(nearest_child_node2.successors) <= self.__branch_factor:
                node.successors.remove(nearest_child_node2)
                if nearest_child_node2.type == cfnode_type.CFNODE_LEAF:
                    self.__leafes.remove(nearest_child_node2)
                
                nearest_child_node1.merge(nearest_child_node2)
                
                merging_result = True
        
        return merging_result


    def __split_procedure(self, split_node):
        """!
        @brief Starts node splitting procedure in the CF-tree from the specify node.
        
        @param[in] split_node (cfnode): CF-tree node that should be splitted.
        
        """
        if split_node is self.__root:
            self.__root = non_leaf_node(split_node.feature, None, [ split_node ])
            split_node.parent = self.__root
            
            # Update statistics
            self.__amount_nodes += 1
            self.__height += 1
        
        [new_node1, new_node2] = self.__split_leaf_node(split_node)
        
        self.__leafes.remove(split_node)
        self.__leafes.append(new_node1)
        self.__leafes.append(new_node2)
        
        # Update parent list of successors
        parent = split_node.parent
        parent.successors.remove(split_node)
        parent.successors.append(new_node1)
        parent.successors.append(new_node2)
        
        # Update statistics
        self.__amount_nodes += 1


    def __split_nonleaf_node(self, node):
        """!
        @brief Performs splitting of the specified non-leaf node.
        
        @param[in] node (non_leaf_node): Non-leaf node that should be splitted.
        
        @return (list) New pair of non-leaf nodes [non_leaf_node1, non_leaf_node2].
        
        """
        
        [farthest_node1, farthest_node2] = node.get_farthest_successors()
        
        # create new non-leaf nodes
        new_node1 = non_leaf_node(farthest_node1.feature, node.parent, [farthest_node1])
        new_node2 = non_leaf_node(farthest_node2.feature, node.parent, [farthest_node2])
        
        farthest_node1.parent = new_node1
        farthest_node2.parent = new_node2
        
        # re-insert other successors
        for successor in node.successors:
            if (successor is not farthest_node1) and (successor is not farthest_node2):
                distance1 = new_node1.get_distance(successor)
                distance2 = new_node2.get_distance(successor)
                
                if distance1 < distance2:
                    new_node1.insert_successor(successor)
                else:
                    new_node2.insert_successor(successor)
        
        return [new_node1, new_node2]


    def __split_leaf_node(self, node):
        """!
        @brief Performs splitting of the specified leaf node.
        
        @param[in] node (leaf_node): Leaf node that should be splitted.
        
        @return (list) New pair of leaf nodes [leaf_node1, leaf_node2].
        
        @warning Splitted node is transformed to non_leaf.
        
        """
        
        # search farthest pair of entries
        [farthest_entity1, farthest_entity2] = node.get_farthest_entries()
                    
        # create new nodes
        new_node1 = leaf_node(farthest_entity1, node.parent, [farthest_entity1])
        new_node2 = leaf_node(farthest_entity2, node.parent, [farthest_entity2])
        
        # re-insert other entries
        for entity in node.entries:
            if (entity is not farthest_entity1) and (entity is not farthest_entity2):
                distance1 = new_node1.feature.get_distance(entity)
                distance2 = new_node2.feature.get_distance(entity)
                
                if distance1 < distance2:
                    new_node1.insert_entry(entity)
                else:
                    new_node2.insert_entry(entity)
        
        return [new_node1, new_node2]


class birch:
    
    def __init__(self, data, number_clusters, branching_factor=100, max_node_entries=500, diameter=0.5,
                 d = None, pz = 0, manhattan = False,
                 entry_size_limit=1000,
                 diameter_multiplier=1.5,
                 ccore=True):
        """!
        @brief Constructor of clustering algorithm BIRCH.
        
        @param[in] data (list): An input data represented as a list of points (objects) where each point is be represented by list of coordinates.
        @param[in] number_clusters (uint): Amount of clusters that should be allocated.
        @param[in] branching_factor (uint): Maximum number of successor that might be contained by each non-leaf node in CF-Tree.
        @param[in] max_node_entries (uint): Maximum number of entries that might be contained by each leaf node in CF-Tree.
        @param[in] diameter (double): CF-entry diameter that used for CF-Tree construction, it might be increase if 'entry_size_limit' is exceeded.
        @param[in] d (QgsDistanceArea): Qgs Measurement object.
        @param[in] pz (uint): Percentage of z-coordinate.
        @param[in] manhattan (bool): Bool for use of Manhattan distance.
        @param[in] entry_size_limit (uint): Maximum number of entries that can be stored in CF-Tree, if it is exceeded
                    during creation then the 'diameter' is increased and CF-Tree is rebuilt.
        @param[in] diameter_multiplier (double): Multiplier that is used for increasing diameter when 'entry_size_limit' is exceeded.
        @param[in] ccore (bool): If True than C++ part of the library is used for processing.
        """
        
        self.__pointer_data = data
        self.__number_clusters = number_clusters
        

        self.__d = d
        self.__pz = pz
        self.__manhattan = manhattan
        self.__entry_size_limit = entry_size_limit
        self.__diameter_multiplier = diameter_multiplier
        self.__ccore = ccore

        self.__verify_arguments()

        self.__features = None
        self.__tree = cftree(branching_factor, max_node_entries, diameter, d, pz, manhattan)
        
        self.__clusters = []
        self.__cf_clusters = []


    def pre_process(self):
        
        self.__insert_data()
        self.__extract_features()

        cf_data = [feature.get_centroid() for feature in self.__features]
        self.__cf_data = {i:QgsPoint(p[0],p[1],p[2]) for i,p in enumerate(cf_data)}

        return self.__cf_data


    def post_process(self, cf_clusters):
    
        self.__cf_clusters = cf_clusters

        cf_labels = {i:index_cluster for index_cluster,p in enumerate(self.__cf_clusters) \
                     for i in p}

        for key in self.__cf_data.keys():
             self.__cf_data[key] = ((1-0.01*self.__pz)*self.__cf_data[key].x(), \
                             (1-0.01*self.__pz)*self.__cf_data[key].y(), \
                             0.01*self.__pz*self.__cf_data[key].z())

        for key in self.__pointer_data.keys():
             self.__point_data[key] = ((1-0.01*self.__pz)*self.__point_data[key].x(), \
                             (1-0.01*self.__pz)*self.__point_data[key].y(), \
                              0.01*self.__pz*self.__point_data[key].z())

        self.__clusters = [[] for _ in range(len(self.__cf_clusters))]

        if self.__manhattan:
            for index_point in self.__pointer_data.keys():
                index_cf_entry = numpy.argmin(numpy.sum(numpy.absolute(
                    numpy.subtract(list(self.__cf_data.values()), \
                    self.__pointer_data[index_point])), axis=1))
                index_cf_entry = list(self.__cf_data.keys())[index_cf_entry]
                index_cluster = cf_labels[index_cf_entry]
                self.__clusters[index_cluster].append(index_point)
        else:
            for index_point in self.__pointer_data.keys():
                index_cf_entry = numpy.argmin(numpy.sum(numpy.square(
                    numpy.subtract(list(self.__cf_data.values()), \
                    self.__pointer_data[index_point])), axis=1))
                index_cf_entry = list(self.__cf_data.keys())[index_cf_entry]
                index_cluster = cf_labels[index_cf_entry]
                self.__clusters[index_cluster].append(index_point)

        return self.__clusters


    def __verify_arguments(self):
        """!
        @brief Verify input parameters for the algorithm and throw exception in case of incorrectness.
        """
        if len(self.__pointer_data) == 0:
            raise ValueError("Input data is empty (size: '%d')." % len(self.__pointer_data))

        if self.__number_clusters <= 0:
            raise ValueError("Amount of cluster (current value: '%d') for allocation should be greater than 0." %
                             self.__number_clusters)

        if self.__entry_size_limit <= 0:
            raise ValueError("Limit entry size (current value: '%d') should be greater than 0." %
                             self.__entry_size_limit)


    def __extract_features(self):
        """!
        @brief Extracts features from CF-tree cluster.
        
        """
        
        self.__features = []
        
        if len(self.__tree.leafes) == 1:
            # parameters are too general, copy all entries
            for entry in self.__tree.leafes[0].entries:
                self.__features.append(entry)

        else:
            # copy all leaf clustering features
            for leaf_node in self.__tree.leafes:
                self.__features += leaf_node.entries


    def __insert_data(self):
        """!
        @brief Inserts input data to the tree.
        
        @remark If number of maximum number of entries is exceeded than diameter is increased and tree is rebuilt.
        
        """
        
        for index_point in self.__pointer_data.keys():
            point = self.__pointer_data[index_point]
            self.__tree.insert_point(point)
            
            if self.__tree.amount_entries > self.__entry_size_limit:
                self.__tree = self.__rebuild_tree(index_point)
    
    
    def __rebuild_tree(self, index_point):
        """!
        @brief Rebuilt tree in case of maxumum number of entries is exceeded.
        
        @param[in] index_point (uint): Index of point that is used as end point of re-building.
        
        @return (cftree) Rebuilt tree with encoded points till specified point from input data space.
        
        """

        rebuild_result = False
        increased_diameter = self.__tree.threshold * self.__diameter_multiplier
        
        tree = None
        
        while rebuild_result is False:
            # increase diameter and rebuild tree
            if increased_diameter == 0.0:
                increased_diameter = 1.0
            
            # build tree with update parameters
            tree = cftree(self.__tree.branch_factor, self.__tree.max_entries, \
                           increased_diameter, self.__d, self.__pz, self.__manhattan)
            
            for index_point in range(0, index_point + 1):
                point = self.__pointer_data[index_point]
                tree.insert_point(point)

                if tree.amount_entries > self.__entry_size_limit:
                    increased_diameter *= self.__diameter_multiplier
                    continue
            
            # Re-build is successful.
            rebuild_result = True
        
        return tree
