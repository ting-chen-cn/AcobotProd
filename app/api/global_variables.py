'''Global variables for camare route module
    isCameraOpen: a boolean indicating whether the camare is working or not.
    isRecording: a boolean indicating whether to record the camare or not.
    isFromFile: a boolean indicating whether the video stream is from a file or not.
    camera: an instance of the camare class.
    videoWriter: an opencv videoWriter class instance
    CAMERA_TYPE : String >> environment variable
    opencv : get access to web camera by using opencv driver.
    pycapture : get access to usb camera by using PyCapture2 driver.(which is the default value of the Lab PC)
'''

CAMERA_TYPE = 'pycapture'
isCameraOpen = False
isRecording = False
isFromFile = False
camera = None
videoWriter = None
blob_detector = None