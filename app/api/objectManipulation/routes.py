
from flask import request,Response,jsonify
from app.models import Blob_detector_parameter
from app.api.objectManipulation import bp
from app.api.errors import bad_request
from app.hardware.objectManipulation import ObjectManipulation
from app.hardware.dataCollection import DataCollection
from app.hardware.acoustic2Camera import acousticBot2CameraDevice as CameraPyCapture
from app.hardware.acoustic2Sound import acousticBot2SoundDevice as soundDriver
from app.api import global_variables as global_
from app import socketInstance
from app.sockets import Pause
import os,ast,traceback,logging

global workDir
workDir=os.getcwd()

global parameters
parameters=None

global pauseEvent
pauseEvent =Pause('data_pause_thread')

@socketInstance.on('startAgain',namespace='/manipulation')
def startAgain():
    pauseEvent.restart()
    logging.info('Experiment is restarted from client!')

@bp.route("/start", methods=['GET', 'POST'])
def start():
    payload=request.get_json() or {}
    global parameters
    if parameters is None:
        socketInstance.emit('error','The parameters required for the experiment is none.',namespace='/manipulation')
        return bad_request('The parameters required for the experiment is none.')
    blob_params =Blob_detector_parameter.query.filter_by(user_id=payload['user_id']).first()
    ObjectM=ObjectManipulation(camera=global_.camera,sound=soundDriver(),parameters=parameters,blob_params=blob_params,workDir=workDir,pauseEvent=pauseEvent,socketInstance=socketInstance)
    try:
        ObjectM.runObjectManipulation()
    except BaseException:
        socketInstance.emit('error',traceback.format_exc(),namespace='/manipulation')
        return bad_request(traceback.format_exc())
    response = jsonify({'message':'Amplitute experiment is finished!'})
    response.status_code = 200
    return response

@bp.route('/setParameters', methods=['GET', 'POST'])
def setParameters():
    payload=request.get_json() or {}
    data=payload['data']
    global parameters
    parameters =data['parameters']
    response = jsonify({'message':'The parameter list of the specified user is setted!','data':parameters})
    response.status_code = 200
    return response

@bp.route("/get_dataFileNames")
def get_dataFileNames():
    '''
      This /get_fileName endpoint is used to get the model files' name from the './ModelFitting' folder for users.
    '''
    global workDir
    files_path = [x for x in os.listdir(os.path.join(workDir,'ModelFitting')) if x.endswith('.pkl')]
    response = jsonify({'data':files_path})
    response.status_code = 200
    return response

@bp.route("/get_tuned_amp")
def get_tuned_amp():
    global workDir
    files_path = [x for x in os.listdir(os.path.join(workDir,'tunedAmp')) if x.endswith('.csv')]
    response = jsonify({'data':files_path})
    response.status_code = 200
    return response


@bp.route("/get_controller_default")
def get_controller_default():
    f = open('./app/hardware/controllers/defualtController.py', "r")
    res=f.read()
    f.close()
    response = jsonify({'data':res})
    response.status_code = 200
    return response

@bp.route("/get_controllers")
def get_controllers():
    
    global workDir
    files_path = [x for x in os.listdir(os.path.join(workDir,'./app/hardware/controllers')) if x.endswith('.py')]
    response = jsonify({'data':files_path})
    response.status_code = 200
    return response
    
@bp.route("/save_controller", methods=['GET', 'POST'])
def save_controller():
    payload=request.get_json() or {}
    global workDir
    filename = os.path.join(workDir,'./app/hardware/controllers',payload['filename'])
    f = open(filename, mode = "w")
    f.write(payload['content'])
    f.close
    response = jsonify({'message':'Saved controller.'})
    response.status_code = 200
    return response