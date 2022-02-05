import os,logging
from flask import Flask,send_from_directory,request,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from flask_socketio import SocketIO

socketInstance = SocketIO()
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    #######Serving a front end created with create-react-app with Flask
    ###### https://stackoverflow.com/questions/44209978/serving-a-front-end-created-with-create-react-app-with-flask?noredirect=1&lq=1
    
    app = Flask(__name__,static_url_path='',static_folder='../build/',template_folder="../build/")

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)


    from app.api.auth import bp as api_auth
    app.register_blueprint(api_auth,url_prefix='/api/auth')

    from app.api.camera import bp as api_camera
    app.register_blueprint(api_camera,url_prefix='/api/camera')

    from app.api.command import bp as api_command
    app.register_blueprint(api_command,url_prefix='/api/command')

    from app.api.ampExp import bp as api_ampExp
    app.register_blueprint(api_ampExp,url_prefix='/api/ampExp')

    from app.api.dataCollecting import bp as api_dataCollecting
    app.register_blueprint(api_dataCollecting,url_prefix='/api/dataCollecting')

    from app.api.modelFitting import bp as api_modelFitting
    app.register_blueprint(api_modelFitting,url_prefix='/api/modelFitting')

    from app.api.objectManipulation import bp as api_objectManipulation
    app.register_blueprint(api_objectManipulation,url_prefix='/api/objectManipulation')

    from app.api.blobDetector import bp as api_blobDetector
    app.register_blueprint(api_blobDetector,url_prefix='/api/blobDetector')

    @app.route("/")
    def serve():
        """serves React App"""
        return send_from_directory(app.static_folder, "index.html")


    @app.route("/<path:path>")
    def static_proxy(path):
        """static folder serve"""
        file_name = path.split("/")[-1]
        dir_name = os.path.join(app.static_folder, "/".join(path.split("/")[:-1]))
        return send_from_directory(dir_name, file_name)


    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith("/api/"):
            return jsonify(message="Resource not found"), 404
        return send_from_directory(app.static_folder, "index.html")


    @app.errorhandler(405)
    def handle_405(e):
        if request.path.startswith("/api/"):
            return jsonify(message="Mehtod not allowed"), 405
        return e

    socketInstance.init_app(app, cors_allowed_origins="*", async_mode='eventlet')
    return app


from app import models,sockets