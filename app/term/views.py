from flask import flash, redirect, render_template, request, url_for, abort
from flask_login import current_user, login_required, login_user, logout_user

from .. import db
from ..models import Term, Permission, Track
from . import term
from .forms import TermForm


@term.route("/browse")
def browse():
    terms = Term.query.order_by(Term.term).all()
    return render_template("term/index.html", terms=terms)


@term.route("/<int:id>")
def show(id):
    term = Term.query.get_or_404(id)
    return render_template("term/display.html", term=term)


@term.route("/add", methods=["GET", "POST"])
@login_required
def add():
    form = TermForm()
    if form.validate_on_submit():
        term = Term(
            term=form.term.data,
            definition=form.definition.data,
            author_id=current_user.id,
        )
        db.session.add(term)
        db.session.commit()
        flash("Term added.", "success")
        return redirect(url_for("main.index"))
    return render_template("term/add.html", form=form)


@term.route("/update/<int:id>", methods=["GET", "POST"])
@login_required
def update(id):
    term = Term.query.get_or_404(id)
    if current_user != term.author and not current_user.can(Permission.ADMIN):
        abort(403)
    form = TermForm()
    if form.validate_on_submit():
        term.term = form.term.data
        term.definition = form.definition.data
        term.source = form.source.data
        db.session.add(term)
        db.session.commit()
        flash("The term has been updated.")
        return redirect(url_for("term.show", id=term.id))
    form.term.data = term.term
    form.definition.data = term.definition
    form.source.data = term.source
    return render_template("/term/update.html", form=form)


@term.route("/track/<int:id>")
@login_required
def track(id):
    term = Term.query.get_or_404(id)
    term.track(current_user.id)
    db.session.commit()
    return redirect(url_for("term.show", id=id))


@term.route("/untrack/<int:id>")
@login_required
def untrack(id):
    term = Term.query.get_or_404(id)
    term.untrack(current_user.id)
    db.session.commit()
    return redirect(url_for("term.show", id=id))


@term.route("/my")
@login_required
def show_my():
    author = current_user
    if author is None:
        abort(404)
    terms = author.terms.order_by(Term.term).all()
    return render_template("/term/my_terms.html", terms=terms)


@term.route("/tracked")
@login_required
def show_tracked():
    current_user
    if current_user is None:
        abort(404)
    # tracks = Track.query.filter_by(tracker_id=current_user.id).all()
    tracks = current_user.tracking.order_by(Track.tracked_id).all()
    return render_template("/term/tracked_terms.html", tracks=tracks)
