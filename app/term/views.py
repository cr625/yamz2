from flask import flash, redirect, render_template, request, url_for, abort
from flask_login import current_user, login_required

from .. import db
from ..models import Relationship, Term, Permission, Track, Comment, Tag
from . import term
from .forms import (
    TermForm,
    CommentForm,
    TagForm,
    UpdateTermForm,
    CreateTermForm,
    CreateRelatedTermForm,
)
from instance.config import *


@term.route("/")
@term.route("/index")
def index():
    page = request.args.get("page", 1, type=int)
    terms = Term.query.order_by(Term.term).paginate(page, TERMS_PER_PAGE, False)

    next_url = url_for("term.index", page=terms.next_num) if terms.has_next else None
    prev_url = url_for("term.index", page=terms.prev_num) if terms.has_prev else None

    return render_template(
        "term/index.html",
        terms=terms.items,
        next_url=next_url,
        prev_url=prev_url,
        page=page,
    )


@term.route("/filter")
def filter():
    template = request.args.get("template")
    if template is not None:
        terms = Term.query.filter_by(source=template).order_by(Term.term).all()
        template = request.args.get("template").upper()
        return render_template("term/browse_by.html", terms=terms, template=template)


@term.route("/browse")
def browse():
    page = request.args.get("page", 1, type=int)
    query = db.session.query(Term.source.distinct().label("source"))
    templates = [row.source for row in query.all()]
    terms = Term.query.order_by(Term.term).paginate(page=page, per_page=TERMS_PER_PAGE)
    next_url = url_for("term.browse", page=terms.next_num) if terms.has_next else None
    prev_url = url_for("term.browse", page=terms.prev_num) if terms.has_prev else None
    return render_template(
        "term/browse.html",
        terms=terms.items,
        templates=templates,
        next_url=next_url,
        prev_url=prev_url,
        page=page,
    )


@term.app_template_filter("template_source")
def template_source_filter(template):
    pass  # put the row comprehension here


@term.route("/browse/template")
def get_templates():
    # templates = db.session.query(distinct(Term.source))
    query = db.session.query(Term.source.distinct().label("source"))
    templates = [row.source for row in query.all()]
    return render_template("term/templates.html", templates=templates)


# /term/id returns a term using the display template including related terms, comments and vote count
@term.route("/ark:/99152/h<int:id>")
@term.route("/<int:id>")
def show(id):
    term = Term.query.get_or_404(id)
    tags = term.tags.order_by(Tag.name)
    children = (
        db.session.query(Term)
        .select_from(Relationship)
        .filter_by(parent_id=id)
        .join(Term, Relationship.child_id == Term.id)
    )
    parents = (
        db.session.query(Term)
        .select_from(Relationship)
        .filter_by(child_id=id)
        .join(Term, Relationship.parent_id == Term.id)
    )
    comments = term.comments.order_by(Comment.timestamp.desc()).all()
    vote_count = term.get_vote_count()
    # children.count() > 0
    # parents.count() > 0:

    return render_template(
        "term/display.html",
        term=term,
        tags=tags,
        children=children,
        parents=parents,
        comments=comments,
        vote_count=vote_count,
    )


@term.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = CreateTermForm()
    if form.validate_on_submit():
        author = current_user._get_current_object()
        term = Term(term=form.term.data.strip(), author=author, source=author.username)
        tag_name = form.tag_name.data.strip()
        tag_value = form.tag_value.data.strip()
        db.session.add(term)
        db.session.commit()
        db.session.refresh(term)
        if tag_name and tag_value:
            term.tag(tag_name, tag_value)
            db.session.commit()
        flash("Term added.", "success")
        return redirect(url_for("term.update", id=term.id))
    return render_template("term/create.html", form=form)


@term.route("/add/<int:id>/", methods=["GET", "POST"])
@login_required
def add(id):
    parent = Term.query.get_or_404(id)
    form = CreateRelatedTermForm()
    if form.validate_on_submit():
        author = current_user._get_current_object()
        relationship = form.relationship_choices.data
        child = Term(term=form.term.data.strip(), author=author, source=author.username)
        tag_name = form.tag_name.data.strip()
        tag_value = form.tag_value.data.strip()
        if tag_name and tag_value:
            child.tag(tag_name, tag_value)
        db.session.commit()
        db.session.add(child)
        db.session.commit()
        db.session.refresh(child)
        parent.instantiate(child, relationship)
        flash("Term added.", "success")
        return redirect(url_for("term.update", id=child.id))
    return render_template("term/add.html", form=form, parent=parent)


@term.route("/comment/add/<int:id>", methods=["GET", "POST"])
@login_required
def comment(id):
    term = Term.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            body=form.body.data, term=term, author=current_user._get_current_object()
        )
        db.session.add(comment)
        db.session.commit()
        flash("Comment added.", "success")
        return redirect(url_for("term.show", id=term.id))
    return render_template("term/comment.html", form=form, term=term)


@term.route("/comment/delete/<int:id>", methods=["GET", "POST"])
@login_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    if current_user != comment.author and not current_user.can(Permission.ADMIN):
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash("The comment has been deleted.")
    return redirect(url_for("term.show", id=comment.term_id))


@term.route("/comment/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_comment(id):
    comment = Comment.query.get_or_404(id)
    term = comment.term
    if current_user != comment.author and not current_user.can(Permission.ADMIN):
        abort(403)
    form = CommentForm()
    if form.validate_on_submit():
        comment.body = form.body.data
        db.session.add(comment)
        db.session.commit()
        flash("The comment has been updated.")
        return redirect(url_for("term.show", id=term.id))
    form.body.data = comment.body
    return render_template("/term/comment.html", form=form, term=term)


@term.route("/update/<int:id>", methods=["GET", "POST"])
@login_required
def update(id):
    term = Term.query.get_or_404(id)
    if current_user != term.author and not current_user.can(Permission.ADMIN):
        abort(403)
    tags = term.tags.order_by(Tag.name)
    edit_tag_id = request.args.get("edit_tag_id")
    form = UpdateTermForm()
    if form.validate_on_submit():
        term.term = form.term.data
        tag_name = form.tag_name.data.strip()
        tag_value = form.tag_value.data.strip()
        term.name = term.term
        db.session.add(term)
        db.session.commit()
        db.session.refresh(term)
        if tag_name and tag_value:
            term.tag(tag_name, tag_value)
        flash("The term has been updated.")
        return redirect(url_for("term.update", id=term.id))
    form.term.data = term.term
    if edit_tag_id is not None:
        tag = Tag.query.get_or_404(edit_tag_id)
        form.tag_name.data = tag.name
        form.tag_value.data = tag.value
    return render_template("/term/update.html", form=form, term=term, tags=tags)


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


# TODO: Make this a post request
@term.route("/vote/<int:id>/<vote_type>")
@login_required
def cast_vote(id, vote_type):
    term = Term.query.get_or_404(id)
    term.vote(current_user.id, vote_type)
    db.session.commit()
    return redirect(url_for("term.comment", id=id))


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
    tracks = current_user.tracking
    terms = (
        db.session.query(Term)
        .select_from(Track)
        .filter_by(tracker_id=current_user.id)
        .join(Term, Track.tracked_id == Term.id)
    )
    return render_template("/term/tracked_terms.html", tracks=tracks, terms=terms)


@term.route("/tag/<int:id>", methods=["GET", "POST"])
@login_required
def tag(id):
    form = TagForm()
    term = Term.query.get_or_404(id)
    if term is None:
        flash("Term id {} not found.".format(id))
        return redirect(url_for("main.index"))
    if form.validate_on_submit():
        name = form.name.data
        value = form.value.data
        term.tag(name=name, value=value)
        return redirect(url_for("term.show", id=term.id))
    return render_template("/term/tag.html", form=form, term=term)


@term.route("/tag/delete/<int:id>", methods=["GET", "POST"])
@login_required
def delete_tag(id):
    tag = Tag.query.get_or_404(id)
    term = tag.term
    if current_user != term.author and not current_user.can(Permission.ADMIN):
        abort(403)
    db.session.delete(tag)
    db.session.commit()
    flash("The metadata item has been deleted.")
    return redirect(url_for("term.update", id=term.id))
