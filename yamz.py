from app import create_app, db
from app.models import User, Role
from flask_migrate import Migrate, upgrade
from celery import Celery

app = create_app()
migrate = Migrate(app, db)

celery = Celery(app.name, broker=app.config["CELERY_BROKER_URL"])
celery.conf.update(app.config)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)


@app.cli.command()
def deploy():
    upgrade()
