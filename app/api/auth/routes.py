
from flask import request,jsonify
from app import db
from app.models import User,Role
from app.api.auth import bp
from app.api.errors import bad_request
import logging


from threading import Lock
bp._before_request_lock = Lock()
bp._got_first_request = False
def init_public_bp():
    if bp._got_first_request:
        return  # or pass
    with bp._before_request_lock:
        bp._got_first_request = True
        roles =Role.query.filter().all()
        for x in range(len(roles)):
            db.session.delete(roles[x])
        db.session.commit()
        role = Role.query.filter().first()
        if role is None:
            logging.info('Add the admin Role')
            role = Role(has_admin=False,user_id=None)
            db.session.add(role)
            db.session.commit()

bp.before_request(init_public_bp)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    data=request.get_json() or {}
    if not data['username']   or not data['password'] :
        logging.info('Login failed with data {}'.format(data))
        return bad_request('must include username, email and password fields')
    user = User.query.filter_by(username=data['username']).first()
    if user is None or not user.check_password(data['password']):
        logging.info('Login failed with data {}'.format(data))
        return bad_request('Invalid username or password',404)
    role = Role.query.filter().first()
    res = user.to_dict()
    if role is None:
        role = Role(has_admin=True,user_id=user.id)
        db.session.add(role)
        db.session.commit()
        res['admin']=True
    else:
        if role.has_admin==False:
            role.has_admin=True
            role.user_id=user.id
            db.session.commit()
            res['admin']=True
        else:
            if role.user_id==user.id:
                res['admin']=True
            else:
                res['admin']=False
    logging.info('{} have successfully logged in!'.format(res['username']))
    return jsonify({'data':res,'message':'{} have successfully logged in!'.format(res['username'])})

@bp.route('/register', methods=['GET', 'POST'])
def register():
    data=request.get_json() or {}
    if not data['username']   or not data['password'] :
        return bad_request('must include username, email and password fields')
    userExist = User.query.filter_by(username=data['username']).first()
    if userExist is  not None :
        return bad_request('Please use a different username.')
    user = User(username=data['username'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    userRes = User.query.filter_by(username=data['username']).first()
    role = Role.query.filter().first()
    res = userRes.to_dict()
    if role is None:
        role = Role(has_admin=True,user_id=user.id)
        db.session.add(role)
        db.session.commit()
        res['admin']=True
    else:
        if role.has_admin==False:
            role.has_admin=True
            role.user_id=user.id
            db.session.commit()
            res['admin']=True
        else:
            if role.user_id==user.id:
                res['admin']=True
            else:
                res['admin']=False
    logging.info('{} have successfully logged in!'.format(res['username']))
    return jsonify({'data':res,'message':'{} have successfully logged in!'.format(res['username'])})

@bp.route('/logout', methods=['GET', 'POST'])
def logout():
    data=request.get_json() or {}
    if 'id' in data:
        role = Role.query.filter_by().first()
        if role is not None and role.user_id==data['id']:
            role.has_admin=False
            role.user_id=None
            db.session.commit()
        logging.info('Current user logged out!')
        response = jsonify({'message':'Current user logged out!'})
        response.status_code = 200
        return response
    else:
        logging.info('There is no user!')
        response = jsonify({'message':'There is no user!'})
        response.status_code = 200
        return response