from flask import Blueprint

bp = Blueprint('objectManipulation', __name__)

from app.api.objectManipulation import routes
