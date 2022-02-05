from flask import Blueprint

bp = Blueprint('blobDetector', __name__)

from app.api.blobDetector import routes
