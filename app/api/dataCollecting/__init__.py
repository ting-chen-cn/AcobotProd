from flask import Blueprint

bp = Blueprint('dataCollecting', __name__)

from app.api.dataCollecting import routes
