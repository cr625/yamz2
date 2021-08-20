import psycopg2
import psycopg2.extras

from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(
            database="seaice",
            user="postgres",
            password="PASS",
        )
    return g.db


def getAllTerms():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM si.terms LIMIT 10")
    return cur.fetchone()
    


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
