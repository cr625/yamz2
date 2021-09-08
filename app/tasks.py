import json
from operator import sub
import sys
import time
from flask import render_template
from rq import get_current_job
from app import create_app, db
from app.models import User, Term, Task
from app.email import send_email
from instance.config import *

from rdflib import Graph, RDF, URIRef, Literal
from rdflib.namespace import DC, RDFS, FOAF, SKOS

app = create_app()
app.app_context().push()

### to start the task queue>>
# redis-server
# rq worker yamz-tasks
basedir = os.path.abspath(os.path.dirname(__file__))


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


# properties are delimited by #. If it ends in /, don't slice it. If the term is delimted by /, get the substring
def check_char(x):
    i = -1
    if "#" in x:
        i = x.rfind("#")
    elif "/" in x and not x.endswith("/"):
        i = x.rfind("/")
    return x[i + 1 :].strip()


def import_file(user_id, **kwargs):
    _set_task_progress(0)
    user = User.query.get(user_id)
    i = 0
    while i < 60:
        # time.sleep(1)
        i += 1
        _set_task_progress(100 * i // 60)
    file = kwargs.get("file")
    file_graph = Graph()
    file_graph = file_graph.parse(file)

    entries = []
    for o in file_graph.objects(None, RDFS.isDefinedBy):
        if o not in entries:
            entries.append(o)
        schema = o

    # schema = file_graph.value(None, RDFS.isDefinedBy)

    source = schema if schema else "DCMI"

    for subject, predicate, obj in file_graph.triples((None, None, None)):
        if (subject, predicate, obj) not in file_graph:
            # app.logger.error("No triples found.")
            # return {"message": "No triples found."}, 400
            raise Exception("No triples found.")
        if isinstance(subject, URIRef):
            subject = file_graph.compute_qname(subject)[-1]
        if isinstance(predicate, URIRef):
            predicate = file_graph.compute_qname(predicate)[-1]
        if isinstance(obj, URIRef):
            predicate = file_graph.compute_qname(obj)[-1]

        # if it's not a URIRef then it is a literal or a bnode so pass it through

        term = Term.query.filter_by(term=subject, source=source).first()
        if term is None:
            term = Term(term=subject, source=source, definition="", author_id=user_id)
            db.session.add(term)
            db.session.commit()
            db.session.refresh(term)
        else:
            term.tag(name=predicate, value=obj)


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
