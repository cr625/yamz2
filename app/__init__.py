from instance.config import SECRET_KEY
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


def create_app(test_config="test_config.py"):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # set common config values
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # if not testing, config is loaded from config.py in the instance folder
    if test_config is None:
        app.config.from_pyfile("config.py")
    else:
        # whichever config file name you pass in also has to be in the instance folder
        app.config.from_pyfile(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    bootstrap.init_app(app)
    migrate.init_app(app, db)

    # apply the blueprints to the app
    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint)

    from .term import term as term_blueprint

    app.register_blueprint(term_blueprint, url_prefix="/term")

    # register command line functions
    @app.cli.command()
    def test():
        """Run the unit tests."""
        import unittest

        tests = unittest.TestLoader().discover("tests")
        unittest.TextTestRunner(verbosity=2).run(tests)

    return app
