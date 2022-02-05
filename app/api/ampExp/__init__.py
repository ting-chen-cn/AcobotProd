from flask import Blueprint

bp = Blueprint('ampExp', __name__)

from app.api.ampExp import routes
