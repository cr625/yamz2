from flask import Blueprint, render_template

bp = Blueprint("main", __name__)

# Homepage blueprint registered in __init__.py


@bp.route("/")
def index():
    return render_template("index.html")
