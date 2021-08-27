from flask import Blueprint

term = Blueprint("term", __name__)

from . import views
from app.models import Permission, Relationship


@term.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)

@term.app_context_processor
def inject_relationships():
    return dict(Relationship=Relationship)