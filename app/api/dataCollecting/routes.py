
from flask import request,Response,jsonify
from app import db
from app.models import Amplitude_experiment_parameter,Blob_detector_parameter
from app.api.dataCollecting import bp
from app.api.errors import bad_request
from app.hardware.dataCollection import DataCollection
from app.hardware.acoustic2Sound import acousticBot2SoundDevice as soundDriver
from app.api import global_variables as global_
import os,logging, traceback
from app import socketInstance
from app.sockets import Pause

global pauseEvent
pauseEvent =Pause('data_pause_thread')

global workDir
workDir=os.getcwd()

global parameters
parameters=None

@socketInstance.on('startAgain',namespace='/data')
def startAgain():
    pauseEvent.restart()
    logging.info('Experiment is restarted from client!')

@bp.route("/get_dataFileNames")
def get_dataFileNames():
    '''
      This /get_fileName endpoint is used to get the collected data files' name from the './tunedAmp' folder for users.
    '''
    global workDir
    files_path = [x for x in os.listdir(os.path.join(workDir,'tunedAmp')) if x.endswith('.csv')]
    response = jsonify({'data':files_path})
    response.status_code = 200
    return response

@bp.route("/set_dataFile", methods=['GET', 'POST'])
def set_dataFile():
    '''
      This /set_dataFile endpoint is used to set the selected data file' name ready to use.
    '''
    data=request.get_json() or {}
    
    global filename, workDir
    filename=os.path.join(workDir,'tunedAmp',data['filename'])
    if os.path.exists(filename):
        global_.isFromFile=True
    response = jsonify({'message':'selected the data file!'})
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

@bp.route("/start", methods=['GET', 'POST'])
def start():
    payload=request.get_json() or {}
    blob_params =Blob_detector_parameter.query.filter_by(user_id=payload['user_id']).first()
    if global_.camera is not None and global_.CAMERA_TYPE=='pycapture':
        global parameters, workDir
        if parameters is None:
            parameters['filename']='freqAmpData-1.csv'
        dataCollection=DataCollection(camera=global_.camera,sound=soundDriver(),parameters=parameters,blob_params=blob_params,workDir=workDir,pauseEvent=pauseEvent,socketInstance=socketInstance)
        try:
            dataCollection.run()
        except :
            socketInstance.emit('error',traceback.format_exc(),namespace='/data')
            response = jsonify({'message':'Failed to start experiment! Please check it and start again.'})
            response.status_code = 200
            return response
        response = jsonify({'message':'Amplitute experiment is finished!'})
        response.status_code = 200
        return response
    else:
        socketInstance.emit('error','The requests of amplitude experiment is not fullfilled. Please check it and start again.',namespace='/data')
        response = jsonify({'message':'Failed to start experiment! Please check it and start again.'})
        response.status_code = 200
        return response
