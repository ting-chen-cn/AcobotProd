import json,sys
from io import StringIO
from time import sleep
from flask import request,Response,jsonify
from app.api.command import bp
from app.api.errors import bad_request
from app.hardware.acoustic2Sound import acousticBot2SoundDevice as soundDriver
import numpy as np
from app import socketInstance


soundDriver = soundDriver()
def play(fre,amp,dur):
        soundDriver.playSignal(fre,amp,dur)
        sleep(1)
        return np.array([])
        
def generate(fre,amp,dur):
        res=soundDriver.generateSignal(fre,amp,dur)
        return res


@bp.route("/command", methods=['GET', 'POST'])
def command():
    data = request.get_json() or {}
    print(data['commandStr'])
    try:
        old_stdout = sys.stdout
        new_stdout = StringIO()
        sys.stdout = new_stdout
        command= compile(data['commandStr'],'','exec')
        ## get the command list from file
        
        commandList = getCommandList()
        # locals =  {'play':play,'generate':generate,'range':range,'print':print,'sleep':sleep,'result':None}
        exec(command, {"__builtins__": {}},commandList)
        output = new_stdout.getvalue()
        sys.stdout = old_stdout
        if output:
            socketInstance.emit('commandInfo',output,namespace='/command')
        if commandList['result']!='None':
            socketInstance.emit('commandInfo','The result of the command is {}'.format(commandList['result']),namespace='/command')
            response = jsonify({'message':None})
            response.status_code = 200
            return response
        socketInstance.emit('commandInfo','The command is executed successfully!',namespace='/command')
        response = jsonify({'message':None})
        response.status_code = 200
        return response
    except:
        return bad_request('Input cannot be exec command!')

def getCommandList():
    with open("commandDoc.txt", "r") as data:
        dictionary = json.loads(data.read())
        
    commandList={}
    for i in range(len(dictionary)):
        name =dictionary[i]['functionName']
        if dictionary[i]['type']=='user-defined': 
            commandList[name]=globals()[name]
        if  dictionary[i]['type']=='built-in':
            commandList[name]=globals()['__builtins__'][name]
        if  dictionary[i]['type'] !='user-defined' and dictionary[i]['type'] !='built-in':
            commandList[name]=dictionary[i]['value']

    return commandList

@bp.route("/getCommands")
def getCommands():
    with open("commandDoc.txt", "r") as data:
        commandList = json.loads(data.read())
    response = jsonify({'message':None,'data':commandList})
    response.status_code = 200
    return response


