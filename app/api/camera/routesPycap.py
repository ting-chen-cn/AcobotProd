
# from flask import request,Response,jsonify
# from app import db
# from app.models import Crop
# from app.api.camera import bp
# from app.api.errors import bad_request
# from app.hardware.acousticbot2 import acousticBot2
# import time
# import PyCapture2
# import cv2
# import os
# #create a new global instance of the acousticBot2 class for this application

# global acoBot 
# acoBot = acousticBot2()

# #endpoints for start cameras action of the acoBot
# @bp.route("/start_camera")
# def start_camera():
#     res = acoBot.enableCamera()
#     acoBot.startCapture()
#     if res== 0:
#         return bad_request('cannot start camera',404)
#     coords=Crop.query.filter_by(name='acrobot').first()
#     crop_coordinate_scaled={'left':coords.left,'right':coords.right,'top':coords.top,'bottom':coords.bottom}
#     acoBot.clickCoordinates= crop_coordinate_scaled
#     response = jsonify({'message':'camera started!'})
#     response.status_code = 200
#     return response

# @bp.route("/video_feed")
# def video_feed():
#     # def gen():
#     #         while True:
#     #             try:
#     #                 frame = acoBot.getBytesImage()
#     #                 yield (b'--frame\r\n'
#     #                 b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')
#     #             except AttributeError or PyCapture2.Fc2error as fc2Err:
#     #                 break
#     res = acoBot.enableCamera()
#     acoBot.startCapture()
#     if res== 0:
#         return bad_request('cannot start camera',404)
#     return Response(gen(),
#     mimetype="multipart/x-mixed-replace; boundary=frame")
    

# @bp.route("/stop_camera")
# def stop_camera():
#     # acoBot.stopCapture()
#     # response = jsonify({'message':'camera stop!'})
#     # response.status_code = 200
#     # return response
#     try:
#         acoBot.stopCapture()
#         response = jsonify({'message':'camera stop!'})
#         response.status_code = 200
#         return response
#     except NameError:
#         response = jsonify({'message':'no camera is started!'})
#         response.status_code = 200
#         return response

# ##TODO
# '''change crop coordinates according to the pycapture2'''
# @bp.route("/crop_camera", methods=['GET', 'POST'])
# def crop_camera():
#     data=request.get_json() or {}
#     if  'top' not in data  or 'left' not in data or not 'right' in data or 'bottom' not in data:
#         return bad_request('must give up, left,right, down related crop relative size')
    
#     coords=Crop.query.filter_by(name='acrobot').first()
#     coords.left=data['left']
#     coords.right=data['right']
#     coords.top=data['top']
#     coords.bottom=data['bottom']
#     crop_coordinate_scaled={'left':data['left'],'right':data['right'],'top':data['top'],'bottom':data['bottom']}
#     acoBot.clickCoordinates= crop_coordinate_scaled
#     db.session.commit()
#     response = jsonify({'message':'image cropped!'})
#     response.status_code = 200
#     return response
# #############################################

# def gen():
#     while True:
#         try:
#             frameIn = acoBot.getImage()
#             if frameIn!=0:
#                 global_img = frameIn
#                 ret, jpeg = cv2.imencode('.jpg', frameIn)
#                 if rec:
#                     print('recording')
#                     if videoWriter:
#                         videoWriter.append(frameIn)
#                 frameOut = jpeg.tobytes()
#                 time.sleep(0)
#                 yield (b'--frame\r\n'
#                 b'Content-Type: image/png\r\n\r\n' + frameOut + b'\r\n')
#             else:
#                 ret, jpeg = cv2.imencode('.jpg', global_img)
#                 global_frame = jpeg.tobytes()
#                 time.sleep(0)
#                 yield (b'--frame\r\n'
#                 b'Content-Type: image/png\r\n\r\n' + global_frame + b'\r\n')
#                 break
#         except AttributeError or PyCapture2.Fc2error as fc2Err:
#             break


# @bp.route("/video_fromFile", methods=['GET', 'POST'])
# def video_fromFile():
#     data=request.get_json() or {}
#     print(data)
#     global filename
#     filename=os.path.join('/Users/yangnan/work/new/backend/video',data['filename'])
#     if os.path.exists(filename):
#         global isFromFile
#         isFromFile=True
#     response = jsonify({'message':'start streaming video from chosen file!'})
#     response.status_code = 200
#     return response
    
# def gen1(filename):
#     camera = cv2.VideoCapture(filename)
#     while True:
#         res,img = camera.read()
#         if not res:
#             break
#         ret, jpeg = cv2.imencode('.jpg', img)
#         frame = jpeg.tobytes()
#         yield (b'--frame\r\n'
#             b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')

# @bp.route("/video_feedFromFile")
# def video_feedFromFile():
#     if isFromFile:
#         return Response(gen1(filename),
#         mimetype="multipart/x-mixed-replace; boundary=frame")
#     return bad_request('No video file is opened!')

# @bp.route("/get_files")
# def get_fileName():
#     files_path = [x for x in os.listdir('/Users/yangnan/work/new/backend/video')]
#     response = jsonify({'data':files_path})
#     response.status_code = 200
#     return response
# @bp.route('/start_record', methods=['POST'])
# def start_record():
#     if not acoBot:
#         return Response(jsonify({'message':'camera not available!'}))
#     # name = os.path.join('/Users/yangnan/work/new/backend/video',time.strftime("%d%b%Y-%H%M%S.avi", time.gmtime()))
#     global rec 
#     rec=True
#     print('start record')
#     #filename needs to be bytes for PyCapture2 function video.AVIOpen()
#     filename = str.encode(time.strftime("%d%b%Y-%H%M%S.avi", time.gmtime()))
#     fRateProp = acoBot.cam.getProperty(PyCapture2.PROPERTY_TYPE.FRAME_RATE)
#     framerate = fRateProp.absValue
#     print('Frame rate: {}'.format(framerate))
#     global videoWriter
#     videoWriter = PyCapture2.FlyCapture2Video()
#     videoWriter.AVIOpen(filename, framerate) 
#     response = jsonify({'message':'record started!'})
#     response.status_code = 200
#     return response

# @bp.route('/stop_record', methods=['POST'])
# def stop_record():
#     if not acoBot:
#         return Response(jsonify({'message':'camera not available!'}))
#     global rec 
#     rec=False
#     try:
#         videoWriter.close()
#         print('stop record')
#         response = jsonify({'message':'record stopped!'})
#         response.status_code = 200
#         return response
#     except NameError:
#         response = jsonify({'message':'no video recorder avaliable!'})
#         response.status_code = 200
#         return response

from flask import request,Response,jsonify
from app import db
from app.models import Crop_coordinate
from app.api.camera import bp
from app.api.errors import bad_request
from app.hardware.acousticbot2 import acousticBot2
import time
import PyCapture2
import cv2
import os
import math
#create a new global instance of the acousticBot2 class for this application
global acoBot
acoBot = acousticBot2()
global recording
recording=False
global outVideo
outVideo=None
global isCameraAvailable
isCameraAvailable=False
#endpoints for start cameras action of the acoBot
@bp.route("/start_camera")
def start_camera():
    global acoBot
    res = acoBot.enableCamera()
    acoBot.startCapture()
    if res== 0:
        return bad_request('cannot start camera',404)
    coords=Crop_coordinate.query.filter_by(name='acrobot').first()
    crop_coordinate_scaled={'left':coords.left,'right':coords.right,'top':coords.top,'bottom':coords.bottom}
    acoBot.clickCoordinates= crop_coordinate_scaled
    global isCameraAvailable
    isCameraAvailable=True
    response = jsonify({'message':'camera started!'})
    response.status_code = 200
    return response

@bp.route("/video_feed")
def video_feed():
    res = acoBot.enableCamera()
    acoBot.startCapture()
    if res== 0:
        return bad_request('cannot start camera',404)
    return Response(gen(),
    mimetype="multipart/x-mixed-replace; boundary=frame")
    

@bp.route("/stop_camera")
def stop_camera():
    try:
        global acoBot
        acoBot.stopCapture()
        global isCameraAvailable
        isCameraAvailable=False
        response = jsonify({'message':'camera stop!'})
        response.status_code = 200
        return response
    except AttributeError:
        response = jsonify({'message':'no camera is started!'})
        response.status_code = 200
        return response

##TODO
'''change crop coordinates according to the pycapture2'''
@bp.route("/crop_camera", methods=['GET', 'POST'])
def crop_camera():
    data=request.get_json() or {}
    if  'top' not in data  or 'left' not in data or not 'right' in data or 'bottom' not in data:
        return bad_request('must give up, left,right, down related crop relative size')
    
    coords=Crop_coordinate.query.filter_by(name='acrobot').first()
    coords.left=data['left']
    coords.right=data['right']
    coords.top=data['top']
    coords.bottom=data['bottom']
    crop_coordinate_scaled={'left':data['left'],'right':data['right'],'top':data['top'],'bottom':data['bottom']}
    acoBot.clickCoordinates= crop_coordinate_scaled
    db.session.commit()
    response = jsonify({'message':'image cropped!'})
    response.status_code = 200
    return response
#############################################

def gen():
    while isCameraAvailable:
        try:
            frameIn = acoBot.getImage()
            if len(frameIn)!=0:
                global_img = frameIn
                ret, jpeg = cv2.imencode('.jpg', frameIn)
                if recording:
                    print('recording')
                    if outVideo:
                       print(frameIn.shape)
                       print('recording')
                       print(math.ceil(acoBot.width),math.ceil(acoBot.height))
                       outVideo.write(frameIn)
                frameOut = jpeg.tobytes()
                time.sleep(0)
                yield (b'--frame\r\n'
                b'Content-Type: image/png\r\n\r\n' + frameOut + b'\r\n')
            else:
                ret, jpeg = cv2.imencode('.jpg', global_img)
                global_frame = jpeg.tobytes()
                time.sleep(0)
                yield (b'--frame\r\n'
                b'Content-Type: image/png\r\n\r\n' + global_frame + b'\r\n')
                break
        except AttributeError or PyCapture2.Fc2error as fc2Err:
            break

@bp.route("/video_fromFile", methods=['GET', 'POST'])
def video_fromFile():
    data=request.get_json() or {}
    print(data)
    basedir=os.getcwd()
    global filename
    filename=os.path.join(basedir,'video',data['filename'])
    if os.path.exists(filename):
        global isFromFile
        isFromFile=True
    response = jsonify({'message':'start streaming video from chosen file!'})
    response.status_code = 200
    return response
    
def gen1(file):
    camera = cv2.VideoCapture(file)
    while True:
        print('serving file')
        res,img = camera.read()
        print(res)
        if not res:
            break
        ret, jpeg = cv2.imencode('.jpg', img)
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
            b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')

@bp.route("/video_feedFromFile")
def video_feedFromFile():
    if isFromFile:
        return Response(gen1(filename),
        mimetype="multipart/x-mixed-replace; boundary=frame")
    return bad_request('No video file is opened!')

@bp.route("/get_files")
def get_fileName():
    basedir=os.getcwd()
    dir=os.path.join(basedir,'video')
    files_path = [x for x in os.listdir(dir)]
    response = jsonify({'data':files_path})
    response.status_code = 200
    return response
@bp.route('/start_record', methods=['POST'])
def start_record():
    if not acoBot:
        return Response(jsonify({'message':'camera not available!'}))
    name = os.path.join(os.getcwd(),'video',time.strftime("%d%b%Y-%H%M%S.avi", time.gmtime()))
    global recording 
    recording=True
    print('start record')
    #filename needs to be bytes for PyCapture2 function video.AVIOpen()
    #filename = str.encode(time.strftime("%d%b%Y-%H%M%S.avi", time.gmtime()))
    # fRateProp = acoBot.cam.getProperty(PyCapture2.PROPERTY_TYPE.FRAME_RATE)
    # framerate = fRateProp.absValue
    # print('Frame rate: {}'.format(framerate))
    # global videoWriter
    # videoWriter = PyCapture2.FlyCapture2Video()
    # videoWriter.AVIOpen(filename, framerate) 
    width = acoBot.width
    height = acoBot.height
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    global outVideo
    outVideo = cv2.VideoWriter(name,fourcc, 20.0, (math.ceil(height),math.ceil(width)))
    response = jsonify({'message':'record started!'})
    response.status_code = 200
    return response

@bp.route('/stop_record', methods=['POST'])
def stop_record():
    global recording 
    recording=False
    if not acoBot:
        return Response(jsonify({'message':'camera not available!'}))
    if outVideo!=None:
        outVideo.release()
        print('stop record')
        response = jsonify({'message':'record stopped!'})
        response.status_code = 200
        return response
    else:
        response = jsonify({'message':'no video recorder avaliable!'})
        response.status_code = 200
        return response

