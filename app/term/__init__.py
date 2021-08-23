from flask import Blueprint

term = Blueprint("term", __name__)

from . import views
from app.models import Permission


@term.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
