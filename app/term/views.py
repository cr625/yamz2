from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from .. import db
from ..models import Term
from . import term
from .forms import AddTermForm


@term.route("/add", methods=["GET", "POST"])
@login_required
def add():
    form = AddTermForm()
    if form.validate_on_submit():
        term = Term(
            term=form.term.data,
            definition=form.definition.data,
            examples=form.examples.data,
            author_id=current_user.id,
        )
        db.session.add(term)
        db.session.commit()
        flash("Term added.", "success")
        return redirect(url_for("main.index"))
    return render_template("term/add.html", form=form)
