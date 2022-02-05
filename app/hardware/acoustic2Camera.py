
# -*- coding: utf-8 -*- 
import cv2
import numpy as np
import os
import PyCapture2
import sounddevice as sd

class acousticBot2CameraDevice:
    """
    Hardware side of acoustic manipulation bot, acousticbot 2.
    
    Requires a connection to a vibration generator and camera.
    
    TODO:
        - Docstrings
        - Exception handling
        - filepaths for files
        - more comments
    """
    
    def __init__(self,crop_coordinate_scaled={'left':0,'right':1,'top':0,'bottom':1}):
        self.cam = None
        self.capture = False
        self.crop_coordinate_scaled = crop_coordinate_scaled
        self.crop_width=0
        self.crop_height=0
    
    def __str__(self):
        return("AcousticBot 2 camera device driver")

    def enableCamera(self):
        #Find camera
        bus = PyCapture2.BusManager()
        numOfCams = bus.getNumOfCameras()
        print('Number of cameras detected: ' + str(numOfCams))
        if not numOfCams:
            print('No cameras detected. Exiting.')
            return 0
        else:
            print('Selecting first camera.')
            
        # Select camera on 0th index
        cam = PyCapture2.Camera()
        uid = bus.getCameraFromIndex(0)
        cam.connect(uid)
    
        self.cam = cam

    def printCameraInfo(self):
        cam_info = self.cam.getCameraInfo()
        print('\n*** CAMERA INFORMATION ***\n')
        print('Serial number - {}'.format(cam_info.serialNumber))
        print('Camera model - {}'.format(cam_info.modelName))
        print('Camera vendor - {}'.format(cam_info.vendorName))
        print('Sensor - {}'.format(cam_info.sensorInfo))
        print('Resolution - {}'.format(cam_info.sensorResolution))
        print('Firmware version - {}'.format(cam_info.firmwareVersion))
        print('Firmware build time - {}'.format(cam_info.firmwareBuildTime))
        print()
        return
        
    def disconnectCamera(self):
        try:
            self.cam.disconnect()
            print("Camera disconnected.")
        except AttributeError: 
            print("No camera connected.")
        
    def startCapture(self):
        self.cam.startCapture()
        self.capture = True

    def stopCapture(self):
        self.cam.stopCapture()
        self.capture = False
        

    def getImage(self):
        try:
            image = self.cam.retrieveBuffer()
        except AttributeError or PyCapture2.Fc2error as fc2Err:
            print('Error retrieving buffer : %s' % fc2Err)
            return []
        # Convert PyCapture image to type used in opencv
        cvImage = np.array(image.getData(), dtype="uint8").reshape((image.getRows(), image.getCols()))
        cvImage = cv2.cvtColor(cvImage, cv2.COLOR_BAYER_BG2BGR)
        # Crop if desired
        ######
        height=image.getRows()
        width = image.getCols()
        L=int(self.crop_coordinate_scaled['left']*width)
        T=int(self.crop_coordinate_scaled['top']*height)
        R=int(self.crop_coordinate_scaled['right']*width)
        B=int(self.crop_coordinate_scaled['bottom']*height)
        self.crop_width=R-L
        self.crop_height=B-T
        cvImage = cvImage[T:B, L:R]
        return cvImage