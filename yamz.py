from app import create_app, db
from app.models import User, Term, Message, Notification, Task
from flask_migrate import Migrate, upgrade

app = create_app()
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "Term": Term,
        "Message": Message,
        "Notification": Notification,
        "Task": Task,
    }


@app.cli.command()
def deploy():
    upgrade()
