from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from .auth import login_required
from .database import get_db

from .forms import CreateTermForm

bp = Blueprint("term", __name__)


@bp.route("/term")
def index():
    """Show all my terms, most recent first."""
    db = get_db()
    curs = db.cursor()
    curs.execute(
        """SELECT p.id, term_string, definition, created, author_id, username
           FROM YAMZ.term p JOIN YAMZ.user u ON p.author_id = u.id
           ORDER BY created DESC;"""
    )
    terms = curs.fetchall()
    return render_template("term/index.html", terms=terms)


def get_term(id, check_author=True):
    """Get a term and its author by id.
    Checks that the id exists and optionally that the current user is
    the author.
    :param id: id of term to get
    :param check_author: require the current user to be the author
    :return: the term with author information
    :raise 404: if a term with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    db = get_db()
    curs = db.cursor()
    curs.execute(
        """
        SELECT p.id, term_string, definition, created, author_id, username
        FROM YAMZ.term p JOIN YAMZ.user u ON p.author_id = u.id
         WHERE p.id = %s""",
        (id,),
    )
    term = curs.fetchone()

    if term is None:
        abort(404, f"Term id {id} doesn't exist.")

    if check_author and term["author_id"] != g.user["id"]:
        abort(403)

    return term


@bp.route("/term/<int:id>/")
def show(id):
    """Show a term and its definition."""
    term = get_term(id)
    return render_template("term/display.html", term=term)


@bp.route("/term/add", methods=("GET", "POST"))
@login_required
def add():
    """Create a new term."""
    form = CreateTermForm()
    if form.validate_on_submit():
        term = form.term.data
        definition = form.definition.data
        db = get_db()
        curs = db.cursor()
        curs.execute(
            """
            INSERT INTO YAMZ.term (term_string, definition, author_id)
            VALUES (%s, %s, %s);""",
            (term, definition, g.user["id"]),
        )
        db.commit()
        flash("Your term was added!")
        return redirect(url_for("term.index"))
    return render_template("term/add.html", form=form)


@bp.route("/term/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new term for the current user."""
    if request.method == "POST":
        term = request.form["term"]
        definition = request.form["definition"]
        error = None

        if not term:
            error = "Term is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            curs = db.cursor()
            curs.execute(
                "INSERT INTO YAMZ.term (term_string, definition, author_id) VALUES (%s, %s, %s)",
                (term, definition, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("term.index"))

    return render_template("term/create.html")


@bp.route("/term/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a term, if the current user is the author."""
    term = get_term(id)

    if request.method == "POST":
        term = request.form["term"]
        definition = request.form["definition"]
        error = None

        if not term:
            error = "Term is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            curs = db.cursor()
            curs.execute(
                "UPDATE YAMZ.term SET term_string = %s, definition = %s WHERE id = %s",
                (term, definition, id),
            )
            db.commit()
            return redirect(url_for("term.index"))

    return render_template("term/update.html", term=term)


@bp.route("/term/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.
    Ensures that the term exists and that the logged in user is the
    author of the term.
    """
    get_term(id)
    db = get_db()
    curs = db.cursor()
    curs.execute("DELETE FROM YAMZ.term WHERE id = %s", (id,))
    db.commit()
    return redirect(url_for("term.index"))
