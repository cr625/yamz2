from flask import flash, redirect, render_template, request, url_for, abort
from flask_login import current_user, login_required, login_user, logout_user

from .. import db
from ..models import Relationship, Term, Permission, Track, Comment
from . import term
from .forms import TermForm, CommentForm


@term.route("/browse")
def browse():
    template = request.args.get('template')
    if template is not None:
        terms = Term.query.filter_by(source=template).order_by(Term.term).all()
        template = request.args.get('template').upper()
        return render_template('term/browse_by.html', terms=terms, template=template)
    else:
        terms = Term.query.order_by(Term.term).all()
        return render_template("term/index.html", terms=terms)

@term.route("/<int:id>")
def show(id):
    term = Term.query.get_or_404(id)
    children = db.session.query(Term).select_from(Relationship).filter_by(parent_id = id).join(Term, Relationship.child_id == Term.id)
    parents = db.session.query(Term).select_from(Relationship).filter_by(child_id = id).join(Term, Relationship.parent_id == Term.id)
    comments = "these are comments"
    # comments = db.session.query(Comment).filter_by(term_id=id).order_by(Comment.date.desc()).all()
   
       
    # children.count() > 0:
    # parents.count() > 0:
        
    return render_template("term/display.html", term=term, children=children, parents=parents, comments=comments)
    

@term.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = TermForm()
    if form.validate_on_submit():
        term = Term(
            term=form.term.data,
            definition=form.definition.data,
            author=current_user._get_current_object(),
        )
        db.session.add(term)
        db.session.commit()
        flash("Term added.", "success")
        return redirect(url_for("main.index"))
    return render_template("term/add.html", form=form)

@term.route("/add/<int:id>/", methods=["GET", "POST"])
@login_required
def add(id):
    relationship = request.args.get('relationship')
    if not relationship == "example":
        return "Only examples are supported right now."
    parent = Term.query.get_or_404(id)
    form = TermForm()
    if form.validate_on_submit():
        child = Term(
            term=form.term.data,
            definition=form.definition.data,
            source=form.source.data,
            author=current_user._get_current_object(),
        )
        db.session.add(child)
        db.session.commit()
        db.session.refresh(child)
        parent.exemplify(child, relationship)
        flash("Term added.", "success")
        return redirect(url_for("main.index"))
    return render_template("term/object.html", form=form, parent=parent, relationship=relationship)

@term.route("/comment/<int:id>", methods=["GET", "POST"])
@login_required
def comment(id):
    term = Term.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          term=term,
                          author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash("Comment added.", "success")
        return redirect(url_for("term.show", id=term.id))
    return render_template("term/comment.html", form=form, term=term)

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

@term.route("/delete/<int:id>", methods=["GET", "POST"])
@login_required
def delete(id):
    term = Term.query.get_or_404(id)
    if current_user != term.author and not current_user.can(Permission.ADMIN):
        abort(403)
    db.session.delete(term)
    db.session.commit()
    flash("The term has been deleted.")
    return redirect(url_for("main.index"))


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
    tracks = current_user.tracking
    terms = db.session.query(Term).select_from(Track).filter_by(tracker_id = current_user.id).join(Term, Track.tracked_id == Term.id)
    return render_template("/term/tracked_terms.html", tracks=tracks, terms=terms)


