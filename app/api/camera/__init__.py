from flask import Blueprint

bp = Blueprint('camera', __name__)

from app.api.camera import routesCombine
