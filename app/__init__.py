from ensurepip import bootstrap
import os
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy


bootstrap = Bootstrap()
db = SQLAlchemy()

basedir = os.path.abspath(os.path.dirname(__file__))


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="ASUFFICIENTLYCOMPLECATEDKEYTHATSHOULDBESTOREDINANENVIRONMENTVARIABLE",
        BOOTSTRAP_BTN_STYLE="primary",
        # SQLALCHEMY_DATABASE_URI="postgresql://postgres:PASS@localhost/yamz",
        # SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    from models import User, Role

    app.config["SECRET_KEY"] = "hard to guess string"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        basedir, "data.sqlite"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    bootstrap.init_app(app)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # apply the blueprints to the app
    from . import main

    app.register_blueprint(main.bp)
    app.add_url_rule("/", endpoint="index")

    from . import auth

    app.register_blueprint(auth.bp)

    from . import term

    app.register_blueprint(term.bp)

    @app.cli.command()
    def test():
        """Run the unit tests."""
        import unittest

        tests = unittest.TestLoader().discover("tests")
        unittest.TextTestRunner(verbosity=2).run(tests)

    return app
