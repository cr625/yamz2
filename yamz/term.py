from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from yamz.auth import login_required
from yamz.db import get_db

bp = Blueprint("term", __name__)


@bp.route("/")
def index():
    db = get_db()
    terms = db.execute(
        "SELECT p.id, term, definition, created, author_id, username"
        " FROM YAMZ.term p JOIN user u ON p.author_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    return render_template("term/index.html", terms=terms)
