"""
The route handler for camera function.

Parameters
----------
CAMERA_TYPE : String >> environment variable
    opencv : get access to web camera by using opencv driver.
    pycapture : get access to usb camera by using PyCapture2 driver.(which is the default value of the Lab PC)
global_.camera : object
    It is the specific camera instance.
global_.isCameraOpen: boolean 
    Indicating whether the camare is working or not. 

Returns
-------
signal : Numpy array
    Numpy float array characterising sine wave.

"""
from flask import request,Response,jsonify
from app import db,socketInstance
from app.models import Crop_coordinate, User
from app.api.camera import bp
from app.api.errors import bad_request
from app.hardware.camera_opencv import Camera as CameraOpenCV
from app.hardware.acoustic2Camera import acousticBot2CameraDevice as CameraPyCapture
from app.api import global_variables as global_
import os,base64,cv2,math,PyCapture2,time,logging


global workDir
workDir=os.getcwd()


@bp.route("/start_camera", methods=['GET', 'POST'])
def start_camera():
    """
    The /start_camera endpoint deal with the frontend start camera request.
    It will load the stored Cropping coords from the application database when create the camera instance.
    And different type of camera will use different driver:
        global_.CAMERA_TYPE == "opencv": opencv library has isOpened() method to check whether if the camera is open or not,
        global_.CAMERA_TYPE == "pycapture": while Pycapture 2 Library will call enableCamera() to start the camera, and if it return 0 then there is no camera opened.
    """
    payload=request.get_json() or {}
    user_id = payload['user_id']
    coords=Crop_coordinate.query.filter_by(user_id=user_id).first()
    # print(coords.to_dict())
    if coords is None:
        crop_coordinate_scaled={'left':0,'right':1,'top':0,'bottom':1}
    else:
        crop_coordinate_scaled={'left':coords.left,'right':coords.right,'top':coords.top,'bottom':coords.bottom} 
    print(crop_coordinate_scaled)
    if global_.CAMERA_TYPE == "opencv":
        global_.camera= CameraOpenCV(video_source=0,crop_coordinate_scaled=crop_coordinate_scaled)
        if not global_.camera.camera.isOpened():
            logging.info("Cannot open camera!")
            return bad_request('Cannot open camera!')

    if global_.CAMERA_TYPE == "pycapture":
        global_.camera= CameraPyCapture(crop_coordinate_scaled=crop_coordinate_scaled)
        res = global_.camera.enableCamera()
        global_.camera.startCapture()
        if res== 0:
            logging.info("Cannot open camera!")
            return bad_request('Cannot start camera!')
    global_.isCameraOpen=True
    logging.info('Camera started!')
    response = jsonify({'message':'Camera started!'})
    response.status_code = 200
    return response


def gen():
    '''
        Generate function to provide video streaming service
        this Gen() function will generate frame from the global_.camera class while the global_.isCameraOpen is true.
        And if the global_.recording and global_.videoWrite does exist, then it will also out out the frame to a avi file.
    '''
    while global_.isCameraOpen:
        try: 
            frameIn = global_.camera.getImage()
            if frameIn == []:
                break
            if global_.blob_detector:
                jpeg=applyBlobDetector(frameIn)
            else:
                _, jpeg = cv2.imencode('.jpg', frameIn) 
            if global_.isRecording:
                if global_.videoWriter:
                    print('recording')
                    global_.videoWriter.write(frameIn)
            frameOut = jpeg.tobytes()
            time.sleep(0)
            yield (b'--frame\r\n'
            b'Content-Type: image/png\r\n\r\n' + frameOut + b'\r\n')
        except :
            break

def euclidDist(p1, p2):
        return math.sqrt((int(p2[0])-int(p1[0]))**2 + (int(p2[1])-int(p1[1]))**2)

def applyBlobDetector(frameIn):
    keypoints =global_.blob_detector.detect(frameIn)
    dims=frameIn.shape
    coordinates = []
    distances =[]
    for keypoint in keypoints:
        coords = (keypoint.pt[0], keypoint.pt[1])
        distances.append(euclidDist(coords, (0.5*dims[1],0.5*dims[1])))
        coordinates.append(coords)
    
    ind=distances.index(min(distances))
    coordinates.pop(ind)
    cv2.waitKey(1)
    circledImg = frameIn.copy()
    for coord in coordinates:
        circledImg = cv2.circle(frameIn, (int(coord[0]), int(coord[1])), 10, (255,0,0), 2)
    _, jpeg = cv2.imencode('.jpg', circledImg)
    return jpeg

@bp.route("/video_feed")
def video_feed():
    '''
        This /video_feed endpoint is used for video streaming used in an img tag in the frontend.
    '''
    if global_.camera:
        if global_.CAMERA_TYPE == "pycapture":
            global_.camera.enableCamera()
            global_.camera.startCapture()
        return Response(gen(),
        mimetype="multipart/x-mixed-replace; boundary=frame")
    logging.info('No camera is opened!')
    return bad_request('No camera is opened!')

@bp.route("/stop_camera", methods=['GET', 'POST'])
def stop_camera():
    """
        The /stop_camera endpoint deal with the frontend stop camera request.
        And different type of camera will use different driver:
            global_.CAMERA_TYPE == "opencv": opencv library has release() method to release the camera,
            global_.CAMERA_TYPE == "pycapture": while Pycapture 2 Library will call stopCapture() to stop the camera.
        TODO:
        - not sure about the right way to stop the camera by using PyCapture2.
    """
    global_.isCameraOpen=False
    try:
        if global_.CAMERA_TYPE == "opencv":
            global_.camera.stop()
            global_.camera=None
        if global_.CAMERA_TYPE == "pycapture":
            global_.camera.stopCapture()
            global_.camera=None
        logging.info('Camera stopped!')
        response = jsonify({'message':'Camera stop!'})
        response.status_code = 200
        return response
    except AttributeError or  global_.camera is None:
        logging.info('No camera is started!')
        response = jsonify({'message':'No camera is started!'})
        response.status_code = 200
        return response

@bp.route("/crop_camera", methods=['GET', 'POST'])
def crop_camera():
    '''
        The /crop_camera endpoint is used to deal with the crop request sent from the frontend.
        The request body is the crop coordinates scaled to [0,1] and this function will extract the coordinates from the request,
        then update it in the application database.
    '''
    payload=request.get_json() or {}
    data = payload['coords']
    if  'top' not in data  or 'left' not in data or not 'right' in data or 'bottom' not in data:
        return bad_request('The crop coordinates formate is not correct.')
    if global_.camera:
        coords =Crop_coordinate.query.filter_by(user_id=payload['user_id']).first()
        if coords is None:
            coords =Crop_coordinate(top=data['top'], left=data['left'], bottom=data['bottom'],right=data['right'])
            coords.user_id = payload['user_id']
            db.session.add(coords)
            db.session.flush()
            db.session.commit()
        else:
            Crop_coordinate.query.filter_by(user_id=payload['user_id']).update(data)
            user = User.query.filter_by(id=payload['user_id']).first()
            db.session.flush()
            db.session.commit()
        global_.camera.crop_coordinate_scaled= data
        c=Crop_coordinate.query.filter_by(user_id=payload['user_id']).first()
    response = jsonify({'message':'image cropped!','data':c.to_dict()})
    response.status_code = 200
    return response

@bp.route("/get_crop_cords", methods=['GET', 'POST'])
def get_crop_cords():
    payload=request.get_json() or {}
    coords =Crop_coordinate.query.filter_by(user_id=payload['user_id']).first()
    if coords is None:
        coords={'left': 0,'top': 0,'right': 1,'bottom': 1}
        response = jsonify({'data':coords})
        response.status_code = 200
    else:
        response = jsonify({'data':coords.to_dict()})
        response.status_code = 200
    return response


@bp.route("/get_videoFileNames")
def get_fileName():
    '''
      This /get_fileName endpoint is used to get the video files' name from the './video' folder for users to choose to play.
    '''
    global workDir
    files_path = [x for x in os.listdir(os.path.join(workDir,'video'))]
    response = jsonify({'data':files_path})
    response.status_code = 200
    return response

@bp.route("/set_videoFile", methods=['GET', 'POST'])
def video_fromFile():
    '''
      This /set_videoFile endpoint is used to set the selected video file' name ready to display.
    '''
    data=request.get_json() or {}
    print(data)
    global filename, workDir
    filename=os.path.join(workDir,'video',data['filename'])
    if os.path.exists(filename):
        global_.isFromFile=True
    response = jsonify({'message':'start streaming video from chosen file!'})
    response.status_code = 200
    return response

def gen1(camera):
    '''
      Generate function when users choose to display stored video file.
    '''
    while camera.isOpened():
        success,img = camera.read()
        if not success:
            print('file is over')
            print(camera)
            if camera:
                camera.release()
            break
        ret, jpeg = cv2.imencode('.jpg', img)
        frame = jpeg.tobytes()
        
        yield (b'--frame\r\n'
            b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')

@bp.route("/video_feedFromFile")
def video_feedFromFile():
    '''
        This /video_feedFromFile endpoint is used for video streaming used in an img tag in the frontend when users had chosen a file to display.
    '''
    if global_.isFromFile:
        camera = cv2.VideoCapture(filename)
        return Response(gen1(camera),
        mimetype="multipart/x-mixed-replace; boundary=frame")
    return bad_request('No video file is opened!')

@bp.route('/start_record', methods=['POST'])
def start_record():
    if global_.camera is None:
        return Response(jsonify({'message':'camera not available!'}))
    global workDir
    name = os.path.join(workDir,'video',time.strftime("%d%b%Y-%H%M%S.avi", time.gmtime()))
    width = global_.camera.crop_width
    height = global_.camera.crop_height
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    global_.videoWriter = cv2.VideoWriter(name,fourcc, 20.0, (int(width),int(height)))
    global_.isRecording=True
    response = jsonify({'message':'record started!'})
    response.status_code = 200
    return response

@bp.route('/stop_record', methods=['POST'])
def stop_record():
    if global_.camera is None:
        return Response(jsonify({'message':'camera not available!'}))
    if global_.videoWriter:
        global_.isRecording=False
        global_.videoWriter.release()
        print('stop record')
        response = jsonify({'message':'record stopped!'})
        response.status_code = 200
        return response
    else:
        response = jsonify({'message':'no video recorder avaliable!'})
        response.status_code = 200
        return response

@bp.route("/delete_crop", methods=['GET', 'POST'])
def delete_crop():
    coords =Crop_coordinate.query.filter().all()
    for x in range(len(coords)):
        db.session.delete(coords[x])
    db.session.commit()
    response = jsonify({'message':'image cropped!'})
    response.status_code = 200
    return response

@socketInstance.on('videostream')
def videostream(data):
    print(data)
    if data['type'] =='live':
        for video_frame in gen():
            socketInstance.emit('image', base64.encodebytes(video_frame).decode("utf-8") , broadcast=True)
    else:
        if global_.isFromFile:
            camera = cv2.VideoCapture(filename)
        for video_frame in gen1(camera):
            socketInstance.emit('image', base64.encodebytes(video_frame).decode("utf-8") , broadcast=True)