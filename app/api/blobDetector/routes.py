
from flask import request,Response,jsonify
from app import db
from app.models import Blob_detector_parameter, User
from app.api.blobDetector import bp
from app.api.errors import bad_request
from app.api import global_variables as global_
import cv2
import os


@bp.route("/init")
def init():
    blobDetector=Blob_detector_parameter(id=1,name='blobDetector',minThreshold= 10,
    maxThreshold= 1000,filterByColor= False,blobColor= 200,
    filterByArea= True,minArea= 150,maxArea= 1500,filterByCircularity= False,
    minCircularity= 0.1,filterByConvexity= False,minConvexity= 0.87,filterByInertia= False,
    minInertiaRatio= 0.01)
    db.session.add(blobDetector)
    db.session.commit()
    
    b=Blob_detector_parameter.query.first()
    return b.to_dict()



@bp.route("/getParameters", methods=['GET', 'POST'])
def getParameters():
    payload=request.get_json() or {}
    parameters =Blob_detector_parameter.query.filter_by(user_id=payload['user_id']).first()
    if parameters is None:
        response = jsonify({'message':'There is not a valid parameter list for the specified user!'})
        response.status_code = 200
        return response
    parameters_res=parameters.to_dict()
    response = jsonify({'message':'The parameter list of the specified user is available!','data':parameters_res})
    response.status_code = 200
    return response

@bp.route('/setParameters', methods=['GET', 'POST'])
def setParameters():
    payload=request.get_json() or {}
    data=payload['data']
    parameters = Blob_detector_parameter.query.filter_by(user_id=payload['user_id']).first()# res:0 or 1
    if parameters is None:
        parameters = Blob_detector_parameter(**data)
        user = User.query.filter_by(id=payload['user_id']).first()
        parameters.user_id = payload['user_id']
        parameters.user = user
        db.session.add(parameters)
        db.session.flush()
        db.session.commit()
        parameters_res = Blob_detector_parameter.query.filter_by(user_id=payload['user_id']).first()
        response = jsonify({'message':'The parameter list of the specified user is setted in the database!','data':parameters_res.to_dict()})
        response.status_code = 200
        return response
    else:
        Blob_detector_parameter.query.filter_by(user_id=payload['user_id']).update(data)
        db.session.flush()
        db.session.commit()
        parameters_res = Blob_detector_parameter.query.filter_by(user_id=payload['user_id']).first()
        if global_.blob_detector:
            print('updating...')
            params = setPara(parameters_res)
            global_.blob_detector = cv2.SimpleBlobDetector_create(params)
        response = jsonify({'message':'The parameter list of the specified user is setted in the database!','data':parameters_res.to_dict()})
        response.status_code = 200
        return response
def setPara(parameters):
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

@bp.route('/setBlobDetector', methods=['GET', 'POST'])
def setBlobDetector():
    payload=request.get_json() or {}
    parameters =Blob_detector_parameter.query.filter_by(user_id=payload['user_id']).first()
    if parameters is None or not global_.isCameraOpen:
        return bad_request('Cannot find the parameters need for blob detector,or there is no camera picture available.')
    else:
        params=setPara(parameters)
        global_.blob_detector = cv2.SimpleBlobDetector_create(params)
        response = jsonify({'message':'The blob detector is setted successfully!'})
        response.status_code = 200
        return response

@bp.route('/deleteBlobDetector', methods=['GET', 'POST'])
def deleteBlobDetector():
    global_.blob_detector = None
    response = jsonify({'message':'The blob detector is deleted successfully!'})
    response.status_code = 200
    return response

@bp.route("/delete", methods=['GET', 'POST'])
def delete():
    coords =Blob_detector_parameter.query.filter().all()
    for x in range(len(coords)):
        db.session.delete(coords[x])
        print(x)
    db.session.commit()
    response = jsonify({'message':'database deleted successfully!'})
    response.status_code = 200
    return response