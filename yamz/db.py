import psycopg2 as pgdb
import psycopg2.extras
import click

from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    if "db" not in g:
        g.db = pgdb.connect(
            database="yamz",
            user="postgres",
            password="PASS",
        )
        g.db.cursor_factory = psycopg2.extras.RealDictCursor

    return g.db


def getAllTerms():
    db = get_db()
    curs = db.cursor()
    curs.execute("SELECT * FROM si.terms LIMIT 10")
    return curs.fetchone()


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with db:
        with db.cursor() as curs:

            curs.execute("""CREATE SCHEMA IF NOT EXISTS YAMZ;""")

            curs.execute(
                """
                DROP TABLE IF EXISTS YAMZ.term;
                DROP TABLE IF EXISTS YAMZ.user;
                CREATE TABLE YAMZ.user (
                    id SERIAL PRIMARY KEY NOT NULL,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL
               );
                CREATE TABLE YAMZ.term (
                    id SERIAL PRIMARY KEY NOT NULL,
                    author_id INTEGER DEFAULT 0 NOT NULL,
                    term_string TEXT NOT NULL,
                    definition TEXT NOT NULL,
                    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (author_id) REFERENCES YAMZ.user (id)
                );"""
            )


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
