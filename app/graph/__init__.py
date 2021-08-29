from flask import Blueprint

graph = Blueprint("graph", __name__)

from . import views
