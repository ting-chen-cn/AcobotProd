from flask import Blueprint

bp = Blueprint('modelFitting', __name__)

from app.api.modelFitting import routes
