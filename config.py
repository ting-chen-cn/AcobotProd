'''Configuration Handling
    This is where we set the configuration for flask. 
    The Config object is the place where Flask itself puts certain configuration values.
    The SECRET_KEY is a secret key that will be used for securely signing the session cookie and can be used for any other security related needs by extensions or your application.
    Then you can import this Config object in the app __init__.py file usage is as follows:
    app.config.from_object(Config)
'''
import os
basedir = os.path.abspath(os.path.dirname(__file__))
class Config(object):
    DEBUG = True 
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-know'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db') #the database is located at the base directory of the application named as app.db
    SQLALCHEMY_TRACK_MODIFICATIONS = False # This ensure not to send a signal to the application every time a change is about to be made in the database.