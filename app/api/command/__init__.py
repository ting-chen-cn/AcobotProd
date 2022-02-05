from flask import Blueprint

bp = Blueprint('command', __name__)

from app.api.command import routes
