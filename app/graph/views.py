import errno
import os

import magic
from flask import abort, flash, redirect, render_template, request, session, url_for

from flask_login import current_user, login_required
from instance.config import FILE_FORMATS, FILE_TYPES
from itsdangerous import exc
from werkzeug.utils import secure_filename

from .. import db
from . import graph
from .forms import UploadForm


@graph.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("/graph/index.html")


@graph.route("/results")
def show_results():
    return render_template("/graph/results.html")


@graph.route("/export_terms")
@login_required
def export_terms():
    if current_user.get_task_in_progress("export_terms"):
        flash("An export task is currently in progress")
    else:
        current_user.launch_task("export_terms", "Exporting terms...")
        db.session.commit()
    return redirect(url_for("main.user", username=current_user.username))


# use magic to determine file type
def validate_xml(stream):
    file_type = magic.from_buffer(stream.read(1024), mime=True)
    stream.seek(0)
    return file_type


@graph.route("/import_file", methods=["GET", "POST"])
@login_required
def import_file():
    form = UploadForm()
    if form.validate_on_submit():
        uploaded_file = request.files.get("file")
        if uploaded_file:
            try:
                os.makedirs("./app/graph/uploads/")
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            file_extension = uploaded_file.filename.rsplit(".", 1)[1]
            file_type = validate_xml(uploaded_file.stream)
            if file_extension not in FILE_FORMATS or file_type not in FILE_TYPES:
                flash(
                    "Unsupported file format {} ({})".format(file_extension, file_type),
                    "error",
                )
                return redirect(url_for("graph.import_file"))
            full_file_path = "./app/graph/uploads/" + secure_filename(
                uploaded_file.filename
            )
            uploaded_file.save(full_file_path)

            if current_user.get_task_in_progress("import_file"):
                flash("An import task is currently in progress")
            else:
                current_user.launch_task(
                    "import_file", "Importing  file...", file=full_file_path
                )
                db.session.commit()

            flash("File uploaded.", "success")
        else:
            flash("No file uploaded.")
            abort(400)
        return redirect(url_for("main.user", username=current_user.username))
    return render_template("/graph/import.html", form=form)  # make these using join

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
