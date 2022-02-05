from munkres import Munkres
import math
import numpy as np
import bottleneck as bn

class MunkresSolver():
    def __init__(self):
        pass
    
    #helper
    def euclidianDistance(self, coordinate1, coordinate2):
        # Calculate and return euclidian distance between two points
        x1 = coordinate1[0]
        y1 = coordinate1[1]
        x2 = coordinate2[0]
        y2 = coordinate2[1]
        
        return math.sqrt((x2-x1)**2 + (y2-y1)**2)

    def sortCoords(self,Y, X):
        #sort X according to Y
        return [x for _, x in sorted(zip(Y, X), key=lambda pair: pair[0])]
        
    #helper
    def createAssignmentMatrix(self, coordinates1, coordinates2):
        """
        Returns matrix that tabulates pairwise euclidian distances betw/ coordinates 
        in coordinates1 and coordinates2, so that if:
       
        coordinates1 = {X,Y,Z} 
        coordinates2 = {A,B,C}
        
        Returned matrix:
            A   B   C
        X  dxa dxb dxc
        Y  dya dyb dyc
        Z  dza dzb dzc
        """
        matrix = []
        i = 0
        # Go over each pairwise assignment
        for coord1 in coordinates1:
            for coord2 in coordinates2:
                dist = self.euclidianDistance(coord1, coord2)
                # Append distance to array for corresponding coord1
                if len(matrix) == i+1:
                    matrix[i] = matrix[i] + [dist]
                # If array is empty (first case) append directly
                else:
                    matrix.append([dist])
                    
            i += 1
    
        return matrix
    
    #helper
    def assignmentSolution(self, matrix):
        """
        Returns assignments consisting of (row: coord1, column: coord2) tuples
        """
        try:
            assert(not len(matrix) == 0)
        except AssertionError:
            return []
        
        "https://www.hungarianalgorithm.com/index.php"
        m = Munkres()
        indexes = m.compute(matrix)
        
        # for row, column in indexes:
        #     value = matrix[row][column]
        #     total += value
        
        return indexes
    
    #helper
    def getAssignments(self, coordinates1, coordinates2):
        matrix = self.createAssignmentMatrix(coordinates1, coordinates2)
        indeces = self.assignmentSolution(matrix)
        
        # Create array with [coord1, dxy, coord2] for every particle
        assignments = []
        for row, column in indeces:
            pair = []
            # Previous coordinate
            pair.append(coordinates1[row])
            # Distace moved
            pair.append(matrix[row][column])
            # New coordinate
            pair.append(coordinates2[column])
            assignments.append(pair)
            
        return assignments
    
    def quantile(self, a, prob):
        """
        Taken from: https://stackoverflow.com/questions/13733034/equivalent-python-command-for-quantile-in-matlab
        Python translation of the algorithm used by MATLAB in-built function "quantile"
        
        Estimates the prob'th quantile of the values in a data array.
    
        Uses the algorithm of matlab's quantile(), namely:
            - Remove any nan values
            - Take the sorted data as the (.5/n), (1.5/n), ..., (1-.5/n) quantiles.
            - Use linear interpolation for values between (.5/n) and (1 - .5/n).
            - Use the minimum or maximum for quantiles outside that range.
    
        See also: scipy.stats.mstats.mquantiles
        """
        a = np.asanyarray(a)
        a = a[np.logical_not(np.isnan(a))].ravel()
        n = a.size
    
        if prob >= 1 - .5/n:
            return a.max()
        elif prob <= .5 / n:
            return a.min()
    
        # find the two bounds we're interpreting between:
        # that is, find i such that (i+.5) / n <= prob <= (i+1.5)/n
        t = n * prob - .5
        i = np.floor(t)
    
        # partial sort so that the ith element is at position i, with bigger ones
        # to the right and smaller to the left
        a = bn.partsort(a, i)
    
        if i == t: # did we luck out and get an integer index?
            return a[i]
        else:
            # we'll linearly interpolate between this and the next index
            smaller = a[i]
            larger = a[i+1:].min()
            if np.isinf(smaller):
                return smaller # avoid inf - inf
            return smaller + (larger - smaller) * (t - i)

    def reorderCoords(self,initCoords,coords):
        aMatrix = self.createAssignmentMatrix(initCoords,coords)
        assignment = self.assignmentSolution(aMatrix)
        Y=[assignment[i][1] for i in range(0,len(assignment))]
        reorderedCoords=self.sortCoords(Y,coords)
        return reorderedCoords
