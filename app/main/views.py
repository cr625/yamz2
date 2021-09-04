from datetime import datetime

from flask import (
    abort,
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from flask_sqlalchemy import get_debug_queries
from instance.config import *

from .. import db
from ..decorators import admin_required, permission_required
from ..models import Message, Notification, Permission, Role, Term, Track, User
from . import main
from .forms import (
    EditProfileAdminForm,
    EditProfileForm,
    EmptyForm,
    FollowForm,
    MessageForm,
)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/home")
@login_required
def home():
    author = current_user
    if author is None:
        abort(404)
    terms = author.terms.order_by(Term.term).all()
    return render_template("home.html", terms=terms)


@main.route("/user/<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    my_terms = current_user.terms.order_by(Term.term).all()
    user_terms = user.terms.order_by(Term.term).all()
    tracked_terms = (
        db.session.query(Term)
        .select_from(Track)
        .filter_by(tracker_id=current_user.id)
        .join(Term, Track.tracked_id == Term.id)
    )
    followed_terms = current_user.followed_terms()
    # shortcut to turn the object into a dictionary
    followed_users = [row.username for row in current_user.followed_users()]
    following_users = [row.username for row in user.following_users()]
    form = FollowForm()
    return render_template(
        "user.html",
        user=user,
        user_terms=user_terms,
        my_terms=my_terms,
        tracked_terms=tracked_terms,
        followed_users=followed_users,
        following_users=following_users,
        followed_terms=followed_terms,
        form=form,
    )


@main.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash("Your profile has been updated.")
        return redirect(url_for(".user", username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", form=form)


@main.route("/edit-profile/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash("The profile has been updated.")
        return redirect(url_for(".user", username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template("edit_profile.html", form=form, user=user)


@main.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username):
    form = FollowForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User {} not found.".format(username))
            return redirect(url_for("main.index"))
        if user == current_user:
            flash("You cannot follow yourself!")
            return redirect(url_for("main.user", username=username))
        current_user.follow(user)
        db.session.commit()
        flash("You are following {}!".format(username))
        return redirect(url_for("main.user", username=username))
    else:
        return redirect(url_for("main.index"))


@main.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
    form = FollowForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User {} not found.".format(username))
            return redirect(url_for("main.index"))
        if user == current_user:
            flash("You cannot unfollow yourself!")
            return redirect(url_for("main.user", username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash("You are not following {}.".format(username))
        return redirect(url_for("main.user", username=username))
    else:
        return redirect(url_for("main.index"))


@main.route("/user/<username>/popup")
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return render_template("user_popup.html", user=user, form=form)


@main.route("/send_message/<recipient>", methods=["GET", "POST"])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user, body=form.message.data)
        db.session.add(msg)
        db.session.commit()
        flash("Your message has been sent.")
        return redirect(url_for("main.user", username=recipient))
    return render_template(
        "send_message.html", title="Send Message", form=form, recipient=recipient
    )


@main.route("/messages")
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    db.session.commit()
    page = request.args.get("page", 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()
    ).paginate(page, TERMS_PER_PAGE, False)
    message_items = messages.items

    next_url = (
        url_for("main.messages", page=messages.next_num) if messages.has_next else None
    )
    prev_url = (
        url_for("main.messages", page=messages.prev_num) if messages.has_prev else None
    )
    return render_template(
        "messages.html", messages=messages.items, next_url=next_url, prev_url=prev_url
    )


@main.route("/notifications")
@login_required
def notifications():
    since = request.args.get("since", 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since
    ).order_by(Notification.timestamp.asc())
    return jsonify(
        [
            {"name": n.name, "data": n.get_data(), "timestamp": n.timestamp}
            for n in notifications
        ]
    )
