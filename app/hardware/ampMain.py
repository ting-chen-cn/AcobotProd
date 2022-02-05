
import cv2,os,random,base64
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from app.hardware.munkres_solver import MunkresSolver
from app import socketInstance
from app.hardware.funs import loadAmpExp,chooseNextAmp,doExperiment,getParticleLocations,saveImageWithMetaData,createBlobDetector,setPara,initBlobDetector

class AmpExperiment():
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
        socketInstance.emit('info','Starting amplitude experiment!',namespace='/amp')
        
        id = self.parameters['id']
        desired_particles = self.parameters['desired_particles']
        desired_stepSize = self.parameters['desired_stepSize']
        cycles = self.parameters['cycles']
        minfreq = self.parameters['minfreq']
        maxfreq = self.parameters['maxfreq']
        duration = self.parameters['duration']
        default_amp = self.parameters['default_amp']
        min_amp = self.parameters['min_amp']
        max_amp = self.parameters['max_amp']
        max_increase = self.parameters['max_increase']
        exps_before_reset = self.parameters['exps_before_reset']
        basescale = self.parameters['basescale']
        self.camera.enableCamera()
        self.camera.startCapture()

        # create prefix for all images saved from experiments
        prefiximg = self.workDir + '\\' +'ampExp'+'\\'+ id + '\\'

        if (os.path.isfile(prefiximg) ):
            socketInstance.emit('info','Cannot start the experiment because there is already folder named by the input id.', namespace='/amp')
            return
        # Create data directory for experiments
        os.makedirs(prefiximg)
        os.chdir(prefiximg) #change directory to prefiximg

        
        # create octaves below and above frequencies in scale and filter out frequencies above/below maxfreq/minfreq  
        tmpscale = [(x * 2**y) for y in range(-10, 11) for x in basescale]   
        expfreq = np.array([freq for freq in tmpscale if maxfreq > freq and freq > minfreq])
            
        # number of frequencies (52)
        M = len(expfreq)        
        # exps to play every frequency N (30) times [30*52]
        exps = []
        # loop over cycles and add permutation of freqs, results in M*cycles exps
        for i in range(cycles):
            # create permutations of frequency sequences
            exps = exps + random.sample(range(M), k=M)
        exps = np.array(exps).astype(int)
        
        # counter for keeping track of experiments completed
        exp_counter = 0
        # amount of experiments
        N = len(exps)
        # tolerance 
        tol = 1e-6
        
        # create empty arrays for experiments
        movements = np.full(N, np.nan)
        freqs = np.full(N, np.nan)
        amps = np.full(N, np.nan)
        durations = np.full(N, np.nan)
        detector=createBlobDetector(self.blob_params,setPara,initBlobDetector)    
        # loop over experiments (N = 30*52)
        for i in range(N):
            if self.isStopped:
                socketInstance.emit('info','Experiment is stopped by the client', namespace='/amp')
                return
            # if amps is not full 
            if np.isnan(amps[i]):
                # create image filenames for before and after
                beforefile = '{:s}{:s}_{:d}_{:.0f}_{:.0f}_in.jpg'.format(prefiximg,id,i+1,expfreq[exps[i]],duration)
                afterfile = '{:s}{:s}_{:d}_{:.0f}_{:.0f}_out.jpg'.format(prefiximg,id,i+1,expfreq[exps[i]],duration)
                # if the files don't already exist, create them by running exps
                if not (os.path.exists(beforefile) and os.path.exists(afterfile)):
                    # get wanted frequency for experiment
                    freq = expfreq[exps[i]]
                    # Boolean mask for succesful experiments (|?)
                    #选择频率为freq的实验
                    ind = ~np.isnan(amps) & (abs(freq - freqs) < tol) & (abs(durations - duration) < tol)
                    # get preiously used amplitudes for experiments
                    prevAmps = amps[ind]
                    # if none take default
                    if prevAmps.size == 0:
                        amp = default_amp
                    else:
                        # get movement from prev exp
                        prevMovements = movements[ind]
                        # scale amp depending on movement of prev exp
                        amp = chooseNextAmp(prevMovements, prevAmps, desired_stepSize, default_amp, max_increase, min_amp, max_amp)
                        
                    # give user possibility to reset particles
                    if (exp_counter >= exps_before_reset):
                        # prompt user to redistribute particles
                        self.pauseEvent.startPause('startPause','Redistribute the particles evenly on the plate and hit enter when ready\n','/amp')
                        exp_counter = 0
                        
                    # take picture for experiment + misc.
                    doExperiment( detector, self.camera, self.sound, getParticleLocations, self.pauseEvent, socketInstance, saveImageWithMetaData,beforefile,afterfile,freq,amp,duration,desired_particles,namespace='/amp')
                    exp_counter = exp_counter + 1

                frameIn=self.camera.getImage()
                jpeg=self.applyBlobDetector(frameIn,detector)
                frameOut = jpeg.tobytes()
                self.socketInstance.emit('info_image',base64.encodebytes(frameOut).decode("utf-8"),namespace='/amp')
                
                # get data from pictures for experiment
                [movements[i],freqs[i],amps[i],durations[i]] = loadAmpExp(getParticleLocations,MunkresSolver,beforefile,afterfile,detector)
                # print progress to client
                socketInstance.emit('info',"{:d} / {:d} ({:.0f}% done) {:1.1f} {:1.3f} {:1.4f}\n".format(i+1, N, (i+1)*100/N, freqs[i], amps[i], movements[i]),namespace='/amp')
        
        # Plot movement amplitude convergence over movement from experiments
        expsData = {'expNum': range(N),'Frequencies': freqs, 'Amplitudes': amps, 
                    'Movements': movements, 'Durations': durations}
        expsData = pd.DataFrame.from_dict(expsData)
        # plot with seaborn and use the hue parameter
        plt.figure(figsize=(10, 6))
        sns.lineplot(x='expNum', y='Amplitudes', data=expsData, hue='Frequencies', legend='full')
        plt.legend(bbox_to_anchor=(1, 1), loc='upper left')
        plt.xticks(rotation=90)
        plt.savefig('expsData_{}.png'.format(id))
        ampImg= cv2.imread('expsData_{}.png'.format(id))
        _, jpeg = cv2.imencode('.jpg', ampImg)
        socketInstance.emit('info_image',base64.encodebytes(jpeg.tobytes()).decode("utf-8"),namespace='/amp')
        
        
        expsData.to_csv('expsData_{}.csv'.format(id))
        os.chdir(self.workDir)
        # Save freq/amplitudes to mat-file
        finalAmps = [binnedAmps[-1] for binnedAmps in [amps[[i for i in range(len(amps)) if freqs[i] == x]] for x in expfreq]]
        freqAmpData = {'frequencies': expfreq, 'Amplitudes': finalAmps}
        freqAmpData = pd.DataFrame.from_dict(freqAmpData)
        freqAmpData.to_csv('./tunedAmp/freqAmpData_{}.csv'.format(id))
    def applyBlobDetector(self,frameIn,detector):
        _,keypoints = getParticleLocations(frameIn,detector)
        for coord in keypoints:
            circledImg = cv2.circle(frameIn, (int(float(coord[0])), int(float(coord[1]))),  5, (225,0,0), 5)
        
        _, jpeg = cv2.imencode('.jpg', circledImg)
        return jpeg

