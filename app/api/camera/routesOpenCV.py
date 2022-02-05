import time
from flask import request,Response,jsonify
from app import db
from app.models import Crop_coordinate
from app.api.camera import bp
from app.api.errors import bad_request
from app.hardware.camera_opencv import Camera
from app.api.camera import global_variables as global_
import os
import cv2
import time

@bp.route("/init")
def init():
    crop=Crop(name='acrobot',left=0,right=1,top=0,bottom=1)
    db.session.add(crop)
    db.session.commit()
    c=Crop.query.all()
    print(c)


@bp.route("/start_camera")
def start_video():
    global_.isCameraOpen=True
    coords=Crop_coordinate.query.filter_by(name='acrobot').first()
    crop_coordinate_scaled={'left':coords.left,'right':coords.right,'top':coords.top,'bottom':coords.bottom} 
    global_.camera= Camera(video_source=0,crop_coordinate_scaled=crop_coordinate_scaled)
    if not global_.camera.camera.isOpened():
        return bad_request('cannot open camera')
    response = jsonify({'message':'camera started!'})
    response.status_code = 200
    return response

'''Generate function to provide video streaming service
    this Gen() function will generate frame from the global_.camera class while the global_.isCameraOpen is true.
    And if the global_.recording and global_.videoWrite does exist, then it will also out out the frame to a avi file.
'''
def gen():
    while global_.isCameraOpen:
        frameIn = global_.camera.getImage()
        if not global_.camera.camera.isOpened():
            ret, jpeg = cv2.imencode('.jpg', last_img)
            last_frame = jpeg.tobytes()
            time.sleep(0)
            yield (b'--frame\r\n'
            b'Content-Type: image/png\r\n\r\n' + last_frame + b'\r\n')
            break
        else:
            last_img = frameIn
            ret, jpeg = cv2.imencode('.jpg', frameIn)
            if global_.isRecording:
                if global_.videoWriter:
                    print('recording')
                    global_.videoWriter.write(frameIn)
            frameOut = jpeg.tobytes()
            time.sleep(0)
            yield (b'--frame\r\n'
            b'Content-Type: image/png\r\n\r\n' + frameOut + b'\r\n')

@bp.route("/video_feed")
def video_feed():
    if global_.camera:
        return Response(gen(),
        mimetype="multipart/x-mixed-replace; boundary=frame")
    return bad_request('No camera is opened!')

@bp.route("/stop_camera")
def stop_camera():
    global_.isCameraOpen=False
    if global_.camera is not None:
        global_.camera.camera.release()
        response = jsonify({'message':'camera stop!'})
        response.status_code = 200
        return response
    else:
        response = jsonify({'message':'no camera is started!'})
        response.status_code = 200
        return response

@bp.route("/crop_camera", methods=['GET', 'POST'])
def crop_camera():
    data=request.get_json() or {}
    if  'top' not in data  or 'left' not in data or not 'right' in data or 'bottom' not in data:
        return bad_request('must give up, left,right, down related crop relative size')
    if global_.camera:
        coords=Crop_coordinate.query.filter_by(name='acrobot').first()
        coords.left=data['left']
        coords.right=data['right']
        coords.top=data['top']
        coords.bottom=data['bottom']
        crop_coordinate_scaled={'left':data['left'],'right':data['right'],'top':data['top'],'bottom':data['bottom']}
        global_.camera.crop_coordinate_scaled= crop_coordinate_scaled
        db.session.commit()
    response = jsonify({'message':'image cropped!'})
    response.status_code = 200
    return response

@bp.route("/video_fromFile", methods=['GET', 'POST'])
def video_fromFile():
    data=request.get_json() or {}
    print(data)
    global filename
    filename=os.path.join(os.getcwd(),'video',data['filename'])
    if os.path.exists(filename):
        global_.isFromFile=True
    response = jsonify({'message':'start streaming video from chosen file!'})
    response.status_code = 200
    return response
    
def gen1(filename):
    camera = cv2.VideoCapture(filename)
    while True:
        success,img = camera.read()
        if not success:
            camera.release()
            break
        ret, jpeg = cv2.imencode('.jpg', img)
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
            b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')

@bp.route("/video_feedFromFile")
def video_feedFromFile():
    if global_.isFromFile:
        return Response(gen1(filename),
        mimetype="multipart/x-mixed-replace; boundary=frame")
    return bad_request('No video file is opened!')

@bp.route("/get_files")
def get_fileName():
    files_path = [x for x in os.listdir(os.path.join(os.getcwd(),'video'))]
    response = jsonify({'data':files_path})
    response.status_code = 200
    return response

@bp.route('/start_record', methods=['POST'])
def start_record():
    if global_.camera is None:
        return Response(jsonify({'message':'camera not available!'}))
    name = os.path.join(os.getcwd(),'video',time.strftime("%d%b%Y-%H%M%S.avi", time.gmtime()))
    width,height = global_.camera.imageSize()
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    global_.videoWriter = cv2.VideoWriter(name,fourcc, 20.0, (int(width),int(height)))
    global_.isRecording=True
    print('start record')
    response = jsonify({'message':'record started!'})
    response.status_code = 200
    return response

@bp.route('/stop_record', methods=['POST'])
def stop_record():
    if global_.camera is None:
        return Response(jsonify({'message':'camera not available!'}))
    global_.isRecording=False
    global_.videoWriter.release()
    print('stop record')
    response = jsonify({'message':'record stopped!'})
    response.status_code = 200
    return response