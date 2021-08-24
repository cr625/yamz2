import os

from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

login_manager = LoginManager()
login_manager.login_view = "auth.login"
bootstrap = Bootstrap()
db = SQLAlchemy()

migrate = Migrate()

basedir = os.path.abspath(os.path.dirname(__file__))


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="ASUFFICIENTLYCOMPLECATEDKEYTHATSHOULDBESTOREDINANENVIRONMENTVARIABLE",
        BOOTSTRAP_BTN_STYLE="dark",
        SQLALCHEMY_DATABASE_URI="postgresql://postgres:PASS@localhost/yamz",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        YAMZ_ADMIN_EMAIL="christopher.b.rauch@gmail.com",
    )

    from . import models

    # testing setup
    #    app.config["SECRET_KEY"] = "hard to guess string"
    #    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    #        basedir, "data.sqlite"
    #    )
    # app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    login_manager.init_app(app)
    bootstrap.init_app(app)
    migrate.init_app(app, db)

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
    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint)

    from .term import term as term_blueprint

    app.register_blueprint(term_blueprint, url_prefix="/term")

    @app.cli.command()
    def test():
        """Run the unit tests."""
        import unittest

        tests = unittest.TestLoader().discover("tests")
        unittest.TextTestRunner(verbosity=2).run(tests)

    return app
