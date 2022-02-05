import cv2,time,statistics,math,base64
from exif import Image as exifImage
import numpy as np
import pandas as pd

def initBlobDetector():
        '''Create the blob detector using the default parameter, see below code.'''
        params = cv2.SimpleBlobDetector_Params()
        
        params.minThreshold = 10
        params.maxThreshold = 1000
        # Color: 0 for dark, 225 light
        params.filterByColor = False
        params.blobColor = 200
        params.filterByArea = True
        params.minArea = 150
        params.maxArea = 1500
        params.filterByCircularity = False
        params.minCircularity = 0.1
        params.filterByConvexity = False
        params.minConvexity = 0.87
        params.filterByInertia = False
        params.minInertiaRatio = 0.01
        
        detector = cv2.SimpleBlobDetector_create(params)
        
        return detector

def setPara(parameters):
        '''Convert the input parameters to the one used to create blob detector'''
        params = cv2.SimpleBlobDetector_Params()
        params.minThreshold = parameters.minThreshold
        params.maxThreshold = parameters.maxThreshold
        # Color: 0 for dark, 225 light
        params.filterByColor = parameters.filterByColor
        params.blobColor = parameters.blobColor
        params.filterByArea = parameters.filterByArea
        params.minArea = parameters.minArea
        params.maxArea = parameters.maxArea
        params.filterByCircularity = parameters.filterByCircularity
        params.minCircularity = parameters.minCircularity
        params.filterByConvexity = parameters.filterByConvexity
        params.minConvexity = parameters.minConvexity
        params.filterByInertia = parameters.filterByInertia
        params.minInertiaRatio = parameters.minInertiaRatio
        return params

def createBlobDetector(blob_params,setPara,initBlobDetector):
        '''Create a blob detector according to the input blob parameters.'''
        if blob_params!=None:
            detector = cv2.SimpleBlobDetector_create(setPara(blob_params))
        else:
            detector = initBlobDetector()
        return detector

def euclidDist(p1, p2):
        return math.sqrt((int(p2[0])-int(p1[0]))**2 + (int(p2[1])-int(p1[1]))**2)

def getParticleLocations(image, detector):
        """Get the keypoints and the coordinates of the keypoints of the input image using the input detector."""
        keypoints = detector.detect(image)
        # Create array of coordinates of detected particles from keypoints
        dims=image.shape
        coordinates = []
        distances =[]
        for keypoint in keypoints:
            coords = (keypoint.pt[0], keypoint.pt[1])
            distances.append(euclidDist(coords, (0.5*dims[1],0.5*dims[1])))
            coordinates.append(coords)
        
        ind=distances.index(min(distances))
        keypoints.pop(ind)
        coordinates.pop(ind)
        cv2.waitKey(1)
        # coordinates = []
        # for keypoint in keypoints:
        #     coords = (keypoint.pt[0], keypoint.pt[1])
        #     coordinates.append(coords)
        # cv2.waitKey(1) 
        return keypoints, coordinates

def imageLoop(image):
        cv2.namedWindow("frame", cv2.WINDOW_NORMAL)
        while True:
            cv2.imshow("frame", image)
            query = cv2.waitKey(1)
            if query == ord('q'):
                break
        cv2.destroyAllWindows()

def saveImageWithMetaData(filename, image, comment):   
        """Saves an image and adds comment as metadata"""
        # write image under filename
        cv2.imwrite(filename, image)
        # wait, to be sure image has been written
        time.sleep(0.01)

        # open image file that was just written
        with open(filename, 'rb') as image_file:
            # open image with exif 
            my_image = exifImage(image_file)
            # Add comment containing experiment info to metadata
            my_image.image_description = comment
            
        # Write image with metadata over previous write
        with open(filename, 'wb') as new_image_file:
            new_image_file.write(my_image.get_file())
        return 1

def chooseNextAmp(prevMovements, prevAmps, desired_stepSize, default_amp, max_increase, min_amp, max_amp):
        '''Function for choosing new amplitude.'''
        # median of element-wise divison
        k = statistics.median(prevAmps / prevMovements)        
        # tune k by given step
        ret = k * desired_stepSize                
        # choose largest amp that yields movement smaller than step
        try:
            last_good_amp = max(prevAmps[(prevMovements < desired_stepSize)])
        except ValueError: 
            # resort to default if empty 
            last_good_amp = default_amp    
            
        # choose between ret or an increased amp from the best tried amp
        newAmp = min(ret, last_good_amp * max_increase)
        
        # check newAmp is within boundaries for amp and return
        return max(min(newAmp, max_amp),min_amp)

def loadAmpExp(getParticleLocations,MunkresSolver,beforeFile, afterFile,detector):
        '''Loads before and after images, computes assignments, and calculates movement.'''
        # Create detector for particle detection
        # Get positions of particles before and after 
        _, p_before = getParticleLocations(cv2.imread(beforeFile), detector)
        _, p_after = getParticleLocations(cv2.imread(afterFile), detector)
        
        # Match particle positions before with positions after using munkres algorithm
        m = MunkresSolver()
        # assignments in form: list:((x1,y1), euclidianDist, (x2,y2))
        assignments = m.getAssignments(p_before, p_after)
        dif = [x[1] for x in assignments]
        
        # get movement from data
        absdif = math.sqrt(sum([x**2 for x in dif]))
        #movement = quantile(absdif,0.75)
        movement = m.quantile(absdif, 0.75)
        
        # Open before-image to fetch metadata on experiment
        with open(beforeFile, 'rb') as image_file:
            my_image = exifImage(image_file)   
            # eval string-comment to dictionary with metadata
            metadata = eval(my_image.image_description)
            
        # Fetch experiment parameters from metadata
        freq = metadata['Freq']
        amp = metadata['Amp']
        duration = metadata['Duration']
        
        #[movement, freq, amp, duration, p_before, p_after]
        return [movement, freq, amp, duration]


        
def doExperiment(detector,camera,sound,getParticleLocations,pauseEvent,socketInstance, saveImageWithMetaData,beforejpg,afterjpg,freq,amp,duration,desired_particles,namespace):
            """Runs experiment, which includes: 
                1. Taking picture of current state (and enforcing particle amount) 
                2. playing a frequency,
                3. taking picture new state
            """    
            parameters = str({'Freq': freq, 'Amp': amp, 'Duration': duration})
            img = camera.getImage()
            _, coords = getParticleLocations(img, detector)
            num_particles = len(coords)
            #pause experiment if the number of the objects is less than the desired number of the particles
            if (num_particles < desired_particles):
                tempImg = img.copy()
                
                for coord in coords:
                    tempImg = cv2.circle(img, (int(coord[0]), int(coord[1])), 5, (225,0,0), 5)
                _, jpeg = cv2.imencode('.jpg', tempImg)
                socketInstance.emit('info_image',base64.encodebytes(jpeg.tobytes()).decode("utf-8"),namespace=namespace)
                pauseEvent.startPause('startPause','Too few particles on the plate, please add more! Close info when ready. Is: {} Should be: {}\n'.format(num_particles,desired_particles),namespace)
            
            saveImageWithMetaData(beforejpg, img, parameters)
            #play the signal of the input parameters
            sound.playSignal(freq, amp, duration/1000)
            time.sleep(duration / 1000 + 0.5) #For under water + 3, For air + 0.5       
            
            img2 =camera.getImage()
            saveImageWithMetaData(afterjpg, img2, parameters)
            
            return num_particles


def readTuneAmplitudeData(fileName):
        data= pd.read_csv(fileName)
        frequencyList=np.array(data['frequencies'])
        AmplitudeList=np.array(data['Amplitudes'])
        return frequencyList,AmplitudeList

def loadImages(detector,getParticleLocations,MunkresSolver,beforeFile, afterFile):
        '''Loads before and after images, computes assignments, and calculates movement.'''
        # Get positions of particles before and after 
        _, p_before = getParticleLocations(cv2.imread(beforeFile), detector)
        _, p_after = getParticleLocations(cv2.imread(afterFile), detector)
        
        # Match particle positions before with positions after using munkres algorithm
        m = MunkresSolver()
        # assignments in form: list:((x1,y1), euclidianDist, (x2,y2))
        assignments = m.getAssignments(p_before, p_after)
        pBefore = np.array([x[0] for x in assignments])
        PAfter = np.array([x[2] for x in assignments])
        
        position=pBefore
        displacement=PAfter-pBefore
        
        # Open before-image to fetch metadata on experiment
        with open(beforeFile, 'rb') as image_file:
            my_image = exifImage(image_file)   
            metadata = eval(my_image.image_description)
            
        # Fetch experiment parameters from metadata
        freq = metadata['Freq']
        amp = metadata['Amp']
        duration = metadata['Duration']
        
        #[movement, freq, amp, duration, p_before, p_after]
        return [freq, amp, duration,position,displacement]