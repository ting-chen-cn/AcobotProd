
from flask import request,Response,jsonify
from app import db
from app.api.modelFitting import bp
from app.api.errors import bad_request
from app.hardware.modelFitting import ModelFitting
from app.api import global_variables as global_
from app import socketInstance
import os,traceback,time


global workDir
workDir=os.getcwd()

@bp.route("/get_dataFileNames")
def get_dataFileNames():
    '''
      This /get_fileName endpoint is used to get the collected data files' name from the './DataCollecting' folder for users.
    '''
    global workDir
    files_path = [x for x in os.listdir(os.path.join(workDir,'DataCollecting')) if x.endswith('.csv')]
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
    filename=os.path.join(workDir,'DataCollecting',data['filename'])
    if os.path.exists(filename):
        global_.isFromFile=True
    response = jsonify({'message':'selected the data file!'})
    response.status_code = 200
    return response



@bp.route("/start", methods=['GET', 'POST'])
def start():
    try:
        global filename, workDir
        if filename is None:
            filename="../../../ampExp/result/DataCollection.csv"
    except :
            socketInstance.emit('error','error happend',namespace='/model')
            socketInstance.sleep(0.1)
            socketInstance.emit('error',traceback.format_exc(),namespace='/model')
            response = jsonify({'message':'Failed to start experiment! Please check it and start again.'})
            response.status_code = 200
            return response
    socketInstance.emit('info','ModelFitting experiment is starting!',namespace='/model')
    socketInstance.sleep(0.1)
    modelFitting=ModelFitting(filename=filename,workDir=workDir,socketInstance=socketInstance)
    modelFitting.fitmain()
    try:
            modelFitting.fitmain()
    except BaseException :
            socketInstance.emit('error',traceback.format_exc(),namespace='/model')
            response = jsonify({'message':'Failed to start experiment! Please check it and start again.'})
            response.status_code = 200
            return response
    socketInstance.emit('info','ModelFitting experiment is finished!',namespace='/model')
    response = jsonify({'message':'ModelFitting experiment is finished!'})
    response.status_code = 200
    return response
