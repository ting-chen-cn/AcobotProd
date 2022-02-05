
from flask import request,Response,jsonify
from app import db
from app.models import Amplitude_experiment_parameter,User,Blob_detector_parameter
from app.api.ampExp import bp
from app.api.errors import bad_request
from app.hardware.ampMain import AmpExperiment
from app.hardware.acoustic2Camera import acousticBot2CameraDevice as CameraPyCapture
from app.hardware.acoustic2Sound import acousticBot2SoundDevice as soundDriver
from app.api import global_variables as global_
import json,os,logging,traceback
from app import socketInstance
from app.sockets import Pause

global pauseEvent
pauseEvent =Pause('amp_pause_thread')
global workDir
workDir=os.getcwd()
global ampExp
ampExp=None


@socketInstance.on('connect',namespace='/amp')
def connectToCommand():
    logging.info('Connecting to name space ''/amp'' from user id: {}'.format(request.sid))



@bp.route("/init")
def init():
    simulate = 0 # 1 = generated random images, 0 = get images over http
    id = 'acoBot2_amptest5' # Identifier of the experiment run
    desired_particles = 19 # How many particles should be on the plate, at least, for the experiment to start
    desired_stepSize = 10 # The experiment tries to adjust the amplitudes so that the 75% of the particles move less than this
    cycles = 5 # For each frequency, how many PTV steps is taken in total. The total number of exps cycles * number of frequencies
    minfreq = 500 # All notes from the scale below this frequency are discarded.
    maxfreq = 1000 # All notes from the scale above this frequency are discarded
    duration = 500 # in milliseconds, constant for all notes
    default_amp = 0.1 # starting amplitude: for 2*3*5 actuators = 0.02 for 2*3*20 actuators = 0.005
    min_amp = 0.01 # never decrease amplitude below this
    max_amp = 2 # never increase amplitude above this
    max_increase = 1.5 # never increase the amplitude more than 1.5 x from the previous experiment
    exps_before_reset = 10 # The balls are replaced to good locations every this many cycles
    basescale = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88] # C major

    ampExp=Amplitude_experiment_parameter(name='ampExp',simulate=simulate,id=id,desiredParticles=desired_particles,desiredStepSize=desired_stepSize,
    cycles=cycles,minfreq=minfreq,maxfreq=maxfreq,duration=duration,defaultAmp=default_amp,minAmp=min_amp,maxAmp=max_amp,
    maxIncrease=max_increase,expsBeforeReset=exps_before_reset,basescale=basescale)
    db.session.add(ampExp)
    db.session.commit()
    a=Amplitude_experiment_parameter.query.all()
    print(a)

@bp.route("/stop", methods=['GET', 'POST'])
def stop():
    global ampExp
    ampExp.stop()
    del ampExp
    response = jsonify({'message':'stop!'})
    response.status_code = 200
    return response


@socketInstance.on('startAgain',namespace='/amp')
def startAgain():
    pauseEvent.restart()
    logging.info('Experiment is restarted from client!')

@bp.route("/start", methods=['GET', 'POST'])
def start():
    payload=request.get_json() or {}
    parameters =Amplitude_experiment_parameter.query.filter_by(user_id=payload['user_id']).first()
    blob_params =Blob_detector_parameter.query.filter_by(user_id=payload['user_id']).first()
    if global_.camera is not None and global_.CAMERA_TYPE=='pycapture':
        workDir=os.getcwd()
        global ampExp
        ampExp=AmpExperiment(camera=global_.camera,sound=soundDriver(),parameters=parameters.to_dict(),blob_params=blob_params,workDir=workDir,pauseEvent=pauseEvent,socketInstance=socketInstance)
        try:
            ampExp.run()
            response = jsonify({'message':'Amplitute experiment is finished!'})
            response.status_code = 200
            return response
        except :
            socketInstance.emit('error',traceback.format_exc(),namespace='/amp')
            response = jsonify({'message':'Failed to start experiment! Please check it and start again.'})
            response.status_code = 200
            return response
    else:
        socketInstance.emit('error','The requests of amplitude experiment is not fullfilled. Please check it and start again.',namespace='/amp')
        response = jsonify({'message':'Failed to start experiment! Please check it and start again.'})
        response.status_code = 200
        return response

@bp.route("/getParameters", methods=['GET', 'POST'])
def getParameters():
    payload=request.get_json() or {}
    parameters =Amplitude_experiment_parameter.query.filter_by(user_id=payload['user_id']).first()
    # if parameters is None:
    #     response = jsonify({'message':'There is not a valid parameter list for the specified user!'})
    #     response.status_code = 200
    #     return response
    if parameters is not None:
        parameters_res=parameters.to_dict()
    else:
        parameters_res=None
    with open(os.path.join(workDir,"amplitude_experiment_parameters.json"), "r") as data:
        paraInfo = json.loads(data.read())
    response = jsonify({'message':'The parameter list of the specified user is available!','data':{'data':parameters_res,'paraInfo':paraInfo}})
    response.status_code = 200
    return response

@bp.route('/setParameters', methods=['GET', 'POST'])
def setParameters():
    payload=request.get_json() or {}
    data=payload['data']
    parameters = Amplitude_experiment_parameter.query.filter_by(user_id=payload['user_id']).first()# res:0 or 1
    if parameters is None:

        parameters = Amplitude_experiment_parameter(**data)
        user = User.query.filter_by(id=payload['user_id']).first()
        parameters.user_id = payload['user_id']
        parameters.user = user
        db.session.add(parameters)
        db.session.flush()
        db.session.commit()
        parameters_res = Amplitude_experiment_parameter.query.filter_by(user_id=payload['user_id']).first()
        response = jsonify({'message':'The parameter list of the specified user is setted in the database!','data':parameters_res.to_dict()})
        response.status_code = 200
        return response
    else:

        Amplitude_experiment_parameter.query.filter_by(user_id=payload['user_id']).update(data)
        db.session.flush()
        db.session.commit()
        parameters_res = Amplitude_experiment_parameter.query.filter_by(user_id=payload['user_id']).first()
        response = jsonify({'message':'The parameter list of the specified user is setted in the database!','data':parameters_res.to_dict()})
        response.status_code = 200
        return response

@bp.route("/delete", methods=['GET', 'POST'])
def delete():
    coords =Amplitude_experiment_parameter.query.filter().all()
    for x in range(len(coords)):
        db.session.delete(coords[x])
        print(x)
    db.session.commit()
    response = jsonify({'message':'database deleted successfully!'})
    response.status_code = 200
    return response
