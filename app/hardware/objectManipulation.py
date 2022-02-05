import time,traceback
import numpy as np
import pandas as pd 
import pickle5 as pickle
import matplotlib.pyplot as plt
import os,re,ast,math
from app.hardware.munkres_solver import MunkresSolver
from app.hardware.funs import loadAmpExp,chooseNextAmp,doExperiment,getParticleLocations,saveImageWithMetaData,createBlobDetector,setPara,initBlobDetector
import cv2,random,base64
import pandas as pd
from time import sleep

class ObjectManipulation():
    def __init__(self,parameters,blob_params,camera=None,sound=None,workDir=os.getcwd(),pauseEvent=None,socketInstance=None):
        self.camera=camera 
        self.sound=sound
        self.workDir=workDir 
        self.filename=parameters['modelName']
        self.parameters=parameters 
        self.blob_params=blob_params
        self.munkresSolver=MunkresSolver()
        self.pauseEvent=pauseEvent
        self.socketInstance=socketInstance
        try:
            Target=ast.literal_eval(parameters['targets'])
        except SyntaxError:
            socketInstance.emit('error',traceback.format_exc(),namespace='/manipulation')
            
        self.targets= Target
        self.image=None
        self.currentPosition=None
        self.video=True
        self.background=None
        self.isRecording=False
        self.videoWriter=None
        pass

    def euclidDist(self,p1, p2):
        return math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)

    def getModel(self,filename):
        fullname=os.path.join(self.workDir,'ModelFitting',filename)
        infile = open(fullname,'rb')
        model = pickle.load(infile)
        infile.close()
        return model

    def getParticleLocations(self,image, detector):
        keypoints = detector.detect(image)
        # Create array of coordinates of detected particles from keypoints
        dims=image.shape
        coordinates = [] 
        distances =[]
        for keypoint in keypoints:
            coords = (keypoint.pt[0]/dims[1], keypoint.pt[1]/dims[0])
            distances.append(self.euclidDist(coords, (0.5,0.5)))
            coordinates.append(coords)
        cv2.waitKey(1) 
        ind=distances.index(min(distances))
        coordinates.pop(ind)
        return coordinates

    def getCurrentPosition(self,detector):
        img = self.camera.getImage()
        coord = self.getParticleLocations(img, detector)
        
        return img,coord

    def getSize(self):
    # use acoBot to find currentposition of particle
        return [1,1]

    def playFreq(self,data,freq):
        amp=data['Amplitudes'][data['frequencies']==freq].values[0]
        self.sound.playSignal(freq, amp, 2)


    def assignTarget(self,positions,targets,):
        if len(positions)!=len(targets):
            self.video=False
            raise SystemExit("The numbers of objects and targets are not match.")
        else:
            #reorder the positions array according to the targets array
            initPositions=self.munkresSolver.reorderCoords(targets,positions)
            return initPositions

    def prepare(self,detector,numberOfObj,targets):
        if self.camera==None:
                self.video=False
                raise SystemExit("The camera is not opened.")
        if str(numberOfObj)!=str(len(targets)):
            self.socketInstance.emit('error','The number of particle is not equal to the targets.\n',namespace='/manipulation')
            self.video=False
            raise SystemExit("The numbers of objects and targets are not match.")
        x=[int(targets[i][0]) for i in range(len(targets))]
        y=[int(targets[i][1])for i in range(len(targets))]
        if min(x)<0 or min(y)<0 or max(x)>1 or max(y)>1:
            self.socketInstance.emit('error','The targets are out of range.\n',namespace='/manipulation')
            self.video=False
            raise SystemExit("The targets are out of range.")
        self.camera.enableCamera()
        self.camera.startCapture()
        model = self.getModel(self.filename)
        frequencyList=model['frequency']
        freqNum = len(frequencyList)
        self.image,positions= self.getCurrentPosition(detector)
        if numberOfObj!=len(positions):
                self.socketInstance.emit('error','The number of particle is not equal to the targets.\n',namespace='/manipulation')
                raise SystemExit("The numbers of objects and targets are not match.")
        if numberOfObj==1:
            initPositions=positions
        else:
            initPositions=self.assignTarget(positions,targets)
        return model,frequencyList,freqNum,initPositions
    
    def costFun(self,positions,targets):
        #distance sum
        cost=[self.munkresSolver.euclidianDistance(targets[i],positions[i]) for i in range(len(positions))]
        return sum(cost)

    def terminate(self,positions,targets,tol):
        cost=self.costFun(positions,targets)
        return cost < tol

    def runObjectManipulation(self):
        
        # filename=os.path.join(self.workDir,'./app/hardware/controllers',self.parameters['controllerName'])
        controllerName= self.parameters['controllerName'].replace('.py','')
        module = __import__('app.hardware.controllers.'+controllerName, fromlist=('app.hardware.controllers'))
        controller = module.controller
        ##############
        # filename1=os.path.join(self.workDir,'tunedAmp',self.parameters['tunedAmpName'])
        tunedAmp= pd.read_csv('./tunedAmp/{}'.format(self.parameters['tunedAmpName']))
        tol=int(self.parameters['tol'])
        maxSteps=int(self.parameters['maxSteps'])
        numberOfObj=int(self.parameters['numberOfObj'])
        detector=createBlobDetector(self.blob_params,setPara,initBlobDetector) 
        model,frequencyList,freqNum,initPositions=self.prepare(detector,numberOfObj,self.targets)
        positionsArray=[initPositions]
        chosenFreqArray=[]
        targets=self.targets
        targetsArray=[targets]
        prepositions= initPositions
        self.currentPosition=initPositions
        self.socketInstance.emit('info','Starting the experiment!',namespace='/manipulation')
        dims=self.image.shape
        name = './ObjectManipulation/manipulationVideo_{}.avi'.format(time.strftime("%d%b%Y-%H%M%S", time.gmtime()))
        width = dims[1]
        height = dims[0]
        fourcc = cv2.VideoWriter_fourcc(*'DIVX')
        self.videoWriter = cv2.VideoWriter(name,fourcc, 20.0, (int(width),int(height)))
        self.isRecording=True
        i=0
        while i< maxSteps:
            prepositions=positionsArray[-1]
            chosenFreqId=controller(targets,prepositions,model,freqNum,positionsArray)
            self.playFreq(tunedAmp,frequencyList[chosenFreqId])
            time.sleep(2)
            self.image,positions=self.getCurrentPosition(detector)
            positions=self.munkresSolver.reorderCoords(prepositions,positions)
            self.currentPosition=positions
            self.socketInstance.emit('info',positions,namespace='/manipulation')
            
            if numberOfObj!=len(positions):
                self.socketInstance.emit('error','The number of particle is not equal to the targets.\n',namespace='/manipulation')
                self.video=False
                self.isRecording=False
                self.videoWriter.release()
                self.videoWriter=None
                raise SystemExit("The numbers of objects and targets are not match.")
            positionsArray.append(positions)
            targetsArray.append(targets)
            chosenFreqArray.append(frequencyList[chosenFreqId])
            if self.costFun(prepositions,positions)<0.01:
                j=random.randint(0,freqNum)
                self.playFreq(tunedAmp,frequencyList[j])
                time.sleep(2)
                self.image,positions=self.getCurrentPosition(detector)
                positions=self.munkresSolver.reorderCoords(prepositions,positions)
                self.currentPosition=positions
                self.socketInstance.emit('info',positions,namespace='/manipulation')
                
                if numberOfObj!=len(positions):
                    self.socketInstance.emit('error','The number of particle is not equal to the targets.\n',namespace='/manipulation')
                    self.video=False
                    self.isRecording=False
                    self.videoWriter.release()
                    self.videoWriter=None
                    raise SystemExit("The numbers of objects and targets are not match.")
                positionsArray.append(positions)
                targetsArray.append(targets)
                chosenFreqArray.append(frequencyList[chosenFreqId])
            if self.terminate(initPositions,targets,tol):
                self.socketInstance.emit('info','Finished with step: {} chosenFre: {}  \n'.format(i+1, frequencyList[chosenFreqId]),namespace='/manipulation')
                self.video=False
                self.isRecording=False
                self.videoWriter.release()
                self.videoWriter=None
                break
            else:
                self.socketInstance.emit('info','step: {} chosenFre: {}  \n'.format(i+1, frequencyList[chosenFreqId]),namespace='/manipulation')
                frameIn=self.image
                jpeg=self.applyBlobDetector(frameIn)
                frameOut = jpeg.tobytes()
                self.socketInstance.emit('info_image',base64.encodebytes(frameOut).decode("utf-8"),namespace='/manipulation')
                i += 1
        positionsArray.pop(0)
        targetsArray.pop(0)
        with open('./ObjectManipulation/manipulationData_{}.txt'.format(time.strftime("%d%b%Y-%H%M%S", time.gmtime())), 'w') as f:
            f.write("step, frequence, positions, targers,\n" )
            for j in range(i-1):
                f.write("{}, {}, {},{} \n".format(j+1, chosenFreqArray[j],positionsArray[j],self.targets))
        f.close()
        self.socketInstance.emit('info','Finished with step: {} chosenFre: {}  \n'.format(i+1, frequencyList[chosenFreqId]),namespace='/manipulation')

    # def gen(self):
    #         while self.video:
    #                 if self.image is  None:
    #                     sleep(2)
    #                 frameIn=self.image
    #                 jpeg=self.applyBlobDetector(frameIn)
    #                 frameOut = jpeg.tobytes()
    #                 yield (b'--frame\r\n'
    #                 b'Content-Type: image/png\r\n\r\n' + frameOut + b'\r\n')

    def applyBlobDetector(self,frameIn):
        if self.currentPosition is  None:
            _, jpeg = cv2.imencode('.jpg', frameIn)
            return jpeg
        else:
            dims = frameIn.shape
            circledImg=frameIn.copy()
            i=1
            for coord in self.currentPosition:
                circledImg = cv2.circle(frameIn, (int(float(coord[0])*dims[1]), int(float(coord[1])*dims[0])), 1, (255,0,0), 2)
                font = cv2.FONT_HERSHEY_SIMPLEX
                circledImg =cv2.putText(frameIn, 'Obj'+str(i), (int(float(coord[0])*dims[1]), int(float(coord[1])*dims[0])), font, 0.8, (10, 255, 225), 2, cv2.LINE_AA)
                i=i+1
            i=1
            for t in self.targets:
                circledImg = cv2.circle(frameIn, (int(float(t[0])*dims[1]), int(float(t[1])*dims[0])), 1, (255,225,0), 2)
                font = cv2.FONT_HERSHEY_SIMPLEX
                circledImg =cv2.putText(frameIn, 'target'+str(i), (int(float(t[0])*dims[1]), int(float(t[1])*dims[0])), font, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
                i=i+1
            if self.background is not None:
                outImg = cv2.addWeighted(circledImg,0.8,cv2.resize(self.background,(dims[1],dims[0])),0.5,0)
            else:
                outImg=circledImg
            if self.isRecording:
                    if self.videoWriter:
                        self.videoWriter.write(outImg)
            _, jpeg = cv2.imencode('.jpg', outImg)
            return jpeg
