from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from .forms import UploadForm

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


@graph.route("/export_file")
@login_required
def export_file():
    if current_user.get_task_in_progress("export_file"):
        flash("An export task is currently in progress")
    else:
        current_user.launch_task("export_file", "Exporting file...")
        db.session.commit()
    return redirect(url_for("main.user", username=current_user.username))


@graph.route("/import", methods=["GET", "POST"])
@login_required
def upload_file():
    form = UploadForm()
    if form.validate_on_submit():
        uploaded_file = request.files.get("file")
        if uploaded_file:
            uploaded_file.save("./app/graph/uploads/" + uploaded_file.filename)
        return redirect(url_for("main.user", username=current_user.username))
    return render_template("/graph/import.html", form=form)

    # upload_file = request.files["file"]
    # if upload_file:
    #    filename = upload_file.filename
    #    current_user.launch_task("upload_file", "Uploading file...", filename=filename)
    #    db.session.commit()
    # return redirect(url_for("main.user", username=current_user.username))

    # if current_user.get_task_in_progress("upload_file"):
    #    flash("An upload task is currently in progress")
    # else:
    #    current_user.launch_task("upload_file", "Uploading file...")
    #    db.session.commit()
    # return redirect(url_for("main.user", username=current_user.username))
