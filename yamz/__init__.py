import os
from unittest import result
from yamz.database import getAllTerms

from flask import Flask, g, request


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
    )

    from . import database

    database.init_app(app)

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/")
    def index():
        results = getAllTerms()
        return str(results)

    @app.route("/ark:/99152/<term_concept_id>")
    def result(term_concept_id=None):
        if request.full_path.endswith("?"):
            return "ends with"

    return app
