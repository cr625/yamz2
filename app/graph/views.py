from flask import flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from .. import db
from . import graph


@graph.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("/graph/index.html")


@graph.route("/export_terms")
@login_required
def export_terms():
    if current_user.get_task_in_progress("export_terms"):
        flash("An export task is currently in progress")
    else:
        current_user.launch_task("export_terms", "Exporting terms...")
        db.session.commit()
    return redirect(url_for("main.user", username=current_user.username))
