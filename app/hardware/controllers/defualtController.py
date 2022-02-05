from queue import PriorityQueue
import math
from random import randint
def floorToGridvalue(x,steps):
    return  int((math.floor(x*steps)/steps)*50)
def euclidDist(p1, p2):
    return math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
################################################################
## you can edit the contents of the controller() function     ##
## stay the function name and the arguments unchanged         ##
################################################################
def controller(targets,prepositions,model,freqNum,positionsArray):
            # priority queue to evaluate different frequency choices 
        q = PriorityQueue() 
        
        # fill prio queue
        for freqId in range(0, freqNum):
            # Add x and y displacement by given frequency predicted by model for new position
            dist=0
            newPosArray=[]
            for i in range(len(prepositions)):
                xGrid=floorToGridvalue(prepositions[i][0],50)
                yGrid=floorToGridvalue(prepositions[i][1],50)
                fu=model['u'][freqId].reshape(-1,50)[xGrid,yGrid]/850
                fv=model['v'][freqId].reshape(-1,50)[xGrid,yGrid]/850
                newPos = (prepositions[i][0] + fu,
                        prepositions[i][1] + fv)        
                dist += euclidDist(newPos, targets[i])
                newPosArray.append(newPos)
            q._put((dist, newPosArray,freqId))
            
        chosenFreqId = q._get()[2]

        return chosenFreqId