import os,random,re,ast,re,base64,cv2
import numpy as np
import pandas as pd
from app import socketInstance
from app.hardware.munkres_solver import MunkresSolver
import pandas as pd
from app.hardware.funs import readTuneAmplitudeData,loadImages,doExperiment,getParticleLocations,saveImageWithMetaData,createBlobDetector,setPara,initBlobDetector


class DataCollection():
    def __init__(self,camera=None,sound=None,parameters=None,blob_params=None,workDir=os.getcwd(),pauseEvent=None,socketInstance=None):
        self.camera=camera 
        self.sound=sound 
        self.parameters=parameters 
        self.blob_params=blob_params
        self.workDir=workDir 
        self.isStopped=False
        self.pauseEvent=pauseEvent
        self.socketInstance=socketInstance
    
    def __del__(self):
        os.chdir(self.workDir)
    def stop(self):
        os.chdir(self.workDir)
        self.isStopped=True


    def run(self):
        socketInstance.emit('info','Starting data collection experiment!',namespace='/data')
        
        id = self.parameters['filename']
        desired_particles = self.parameters['desired_particles']
        cycles = self.parameters['cycles']
        duration = self.parameters['duration']
        exps_before_reset = self.parameters['exps_before_reset']
        filename =  os.path.join(self.workDir,'tunedAmp',self.parameters['filename'])
        self.camera.enableCamera()
        self.camera.startCapture()

        # create prefix for all images saved from experiments
        prefiximg = self.workDir + '\\' +'DataCollecting'+'\\'+ id.replace('.csv','') + '\\'

        if (os.path.isdir(prefiximg) ):
            os.chdir(prefiximg)
        else:
        # Create data directory for experiments
            try:
                os.makedirs(prefiximg)
            except :
                socketInstance.emit('info','Cannot start the experiment because there is already folder named by the input id.', namespace='/data')
                return
            os.chdir(prefiximg) #change directory to prefiximg

        if filename==None:
            socketInstance.emit('info','Cannot start the experiment because there is not available amplitude data file.', namespace='/data')
            return
        expfreq,AmplitudeList=readTuneAmplitudeData(filename)


        M = len(expfreq)        
        exps = []
        for i in range(cycles):
            exps = exps + random.sample(range(M), k=M)
        exps = np.array(exps).astype(int)
        
        # counter for keeping track of experiments completed
        exp_counter = 0
        N = len(exps)
        
        freqs = np.full(N, np.nan)
        amps = np.full(N, np.nan)
        durations = np.full(N, np.nan)
        positions=  np.empty(N, dtype=object)
        displacements=  np.empty(N, dtype=object)
        detector=createBlobDetector(self.blob_params,setPara,initBlobDetector)    
        for i in range(N):
            if self.isStopped:
                socketInstance.emit('info','Experiment is stopped by the client', namespace='/data')
                return
            if np.isnan(amps[i]):
                # create image filenames for before and after
                beforefile = '{:s}{:s}_{:d}_{:.0f}_{:.0f}_in.jpg'.format(prefiximg,id,i+1,expfreq[exps[i]],duration)
                afterfile = '{:s}{:s}_{:d}_{:.0f}_{:.0f}_out.jpg'.format(prefiximg,id,i+1,expfreq[exps[i]],duration)
                # if the files don't already exist, create them by running exps
                if not (os.path.exists(beforefile) and os.path.exists(afterfile)):
                    freq = expfreq[exps[i]]
                    amp = AmplitudeList[exps[i]]
                    #give user possibility to reset particles
                    if (exp_counter >= exps_before_reset):
                        # prompt user to redistribute particles
                        self.pauseEvent.startPause('startPause','Redistribute the particles evenly on the plate and hit enter when ready\n','/data')
                        # input('Redistribute the particles evenly on the plate and hit enter when ready\n')
                        exp_counter = 0
                        
                    # take picture for experiment + misc.
                    doExperiment( detector, self.camera, self.sound, getParticleLocations, self.pauseEvent, socketInstance, saveImageWithMetaData,beforefile,afterfile,freq,amp,duration,desired_particles,namespace='/data')
                    exp_counter = exp_counter + 1
                
                frameIn=self.camera.getImage()
                jpeg=self.applyBlobDetector(frameIn,detector)
                frameOut = jpeg.tobytes()
                self.socketInstance.emit('info_image',base64.encodebytes(frameOut).decode("utf-8"),namespace='/data')
                
                # get data from pictures for experiment
                [freqs[i],amps[i],durations[i], positions[i],displacements[i]] = loadImages(detector,getParticleLocations,MunkresSolver,beforefile,afterfile)
                socketInstance.emit('info',"{:d} / {:d} ({:.0f}% done) {:1.1f}  {:1.4f}\n".format(i+1, N, (i+1)*100/N, freqs[i], amps[i]),namespace='/data')
        
        # Plot movement amplitude convergence over movement from experiments
        expsData = {'expNum': range(N),'Frequencies': freqs, 'Amplitudes': amps, 
                    'Positions': positions, 'Displacements': displacements}
        expsData = pd.DataFrame.from_dict(expsData)
        
        os.chdir(self.workDir)
        expsData.to_csv('./DataCollecting/DataCollecting_{}.csv'.format(id))      

    def applyBlobDetector(self,frameIn,detector):
        _,keypoints = getParticleLocations(frameIn,detector)
        for coord in keypoints:
            circledImg = cv2.circle(frameIn, (int(float(coord[0])), int(float(coord[1]))),  5, (225,0,0), 5)
        
        _, jpeg = cv2.imencode('.jpg', circledImg)
        return jpeg

    def dataAnalysis(self,filename="./DataCollection/DataCollection_{}.csv".format(id)):
        data = pd.read_csv(filename)
        freSet=list(set(data['Frequencies']))
        X=[]
        Y=[]
        U=[]
        V=[]
        F=[]
        for j in range(len(freSet)):
            data1=data[data['Frequencies']==freSet[j]]
            # print(data1['Positions'])
            position=np.array([[0,0]])
            displacements=np.array([[0,0]])
            for index, row in data1.iterrows():
                a=re.sub(r"([^[\s])\s+([^]])", r"\1, \2", row['Positions'])
                position=np.vstack((position,np.array(ast.literal_eval(a))))
                b=re.sub(r"([^[\s])\s+([^]])", r"\1, \2", row['Velocities'])
                displacements=np.vstack((displacements, np.array(ast.literal_eval(b))))
        
                x, y = position.T
                u,v=displacements.T
                f= np.full(len(x), freSet[j])
                X=np.append(X,x)
                Y=np.append(Y,y)
                U=np.append(U,u)
                V=np.append(V,v)
                F=np.append(F,f)

        expsData = {'frequency':F,'x': X, 'y': Y, 'u': U, 'v': V}
        expsData = pd.DataFrame(expsData)
        expsData.to_csv('./DataCollecting/modelData1.csv')



