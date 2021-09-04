import json
import sys
import time
from flask import render_template
from rq import get_current_job
from app import create_app, db
from app.models import User, Term, Task
from app.email import send_email
from instance.config import *

app = create_app()
app.app_context().push()

### to start the task queue>>
# redis-server
# rq worker yamz-tasks


def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta["progress"] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification(
            "task_progress", {"task_id": job.get_id(), "progress": progress}
        )
        if progress >= 100:
            task.complete = True
        db.session.commit()


def export_terms(user_id):
    try:
        user = User.query.get(user_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_terms = user.terms.count()
        for term in user.terms.order_by(Term.timestamp.asc()):
            data.append(
                {"term": term.term, "timestamp": term.timestamp.isoformat() + "Z"}
            )
            # time.sleep(5)
            i += 1
            _set_task_progress(100 * i // total_terms)

        send_email(
            "[YAMZ] Your Terms",
            SENDER_EMAIL,
            recipients=[user.email],
            text_body=render_template("email/export_terms.txt", user=user),
            html_body=render_template("email/export_terms.html", user=user),
            attachments=[
                (
                    "terms.json",
                    "application/json",
                    json.dumps({"terms": data}, indent=4),
                )
            ],
            sync=True,
        )
    except:
        _set_task_progress(100)
        # app.logger.error("Unhandled exception", exc_info=sys.exc_info())
