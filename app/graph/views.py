from flask import render_template
from . import graph


@graph.route("/import")
def index():
    return render_template("/graph/import.html")
