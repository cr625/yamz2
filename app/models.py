from datetime import datetime
from hashlib import md5
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager
import redis, rq, time, json, re, jwt
from instance.config import *
from time import time


class Permission:
    FOLLOW = 1
    # TRACK = 2 # don't forget to update the db when you add a new permission
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


DEFAULT_TAGS = [
    "user",
    "schema",
    "vocabulary",
    "source",
    "definition",
    "archive",
    "description",
]


def slugify(s):
    return re.sub("[^\w]+", "-", s).lower()


class Tag(db.Model):
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey("terms.id"))
    name = db.Column(db.String(64))
    value = db.Column(db.String(64))
    # slug = db.Column(db.String(64), unique=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, *args, **kwargs):
        super(Tag, self).__init__(*args, **kwargs)
        # self.slug = slugify(self.name, self.value)

    def __repr__(self):
        return "<Tag %s>" % self.name


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship("User", backref="role", lazy="dynamic")

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            "User": [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            "Moderator": [
                Permission.FOLLOW,
                Permission.COMMENT,
                Permission.WRITE,
                Permission.MODERATE,
            ],
            "Administrator": [
                Permission.FOLLOW,
                Permission.COMMENT,
                Permission.WRITE,
                Permission.MODERATE,
                Permission.ADMIN,
            ],
        }
        default_role = "User"
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = role.name == default_role
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return "<Role %r>" % self.name


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("users.id")),
    db.Column("followed_id", db.Integer, db.ForeignKey("users.id")),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    password_hash = db.Column(db.String(128))
    last_message_read_time = db.Column(db.DateTime)

    # create db relationships
    terms = db.relationship("Term", backref="author", lazy="dynamic")
    comments = db.relationship("Comment", backref="author", lazy="dynamic")
    tracking = db.relationship(
        "Track", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    voter = db.relationship(
        "Vote", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    comments = db.relationship("Comment", backref="author", lazy="dynamic")
    tasks = db.relationship("Task", backref="user", lazy="dynamic")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic")

    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )
    messages_sent = db.relationship(
        "Message", foreign_keys="Message.sender_id", backref="author", lazy="dynamic"
    )
    messages_received = db.relationship(
        "Message",
        foreign_keys="Message.recipient_id",
        backref="recipient",
        lazy="dynamic",
    )

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == YAMZ_ADMIN_EMAIL:
                self.role = Role.query.filter_by(name="Administrator").first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return (
            Message.query.filter_by(recipient=self)
            .filter(Message.timestamp > last_read_time)
            .count()
        )

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            SECRET_KEY,
            algorithm="HS256",
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])["reset_password"]
        except:
            return
        return User.query.get(id)

    @property
    def tracked_terms(self):
        return Term.query.join(Track, Track.tracker_id == self.id).filter(
            Track.tracker_id == self.id
        )

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_users(self):
        return self.followed

    def following_users(user):
        return user.followed

    def followed_terms(self):
        return (
            Term.query.join(followers, (followers.c.followed_id == Term.author_id))
            .filter(followers.c.follower_id == self.id)
            .order_by(Term.term)
        )

    # this is for terms for the users I follow and my own terms
    def my_followed_terms(self):
        followed = Term.query.join(
            followers, (followers.c.followed_id == Term.user_id)
        ).filter(followers.c.follower_id == self.id)
        own = Term.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Term.timestamp.desc())

    def is_tracking(self, term):
        if term.id is None:
            return False
        return self.tracking.filter_by(tracked_id=term.id).first() is not None

    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue(
            "app.tasks." + name, self.id, *args, **kwargs
        )
        task = Task(id=rq_job.get_id(), name=name, description=description, user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self, complete=False).first()

    def __repr__(self):
        return "<User %r>" % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


class Relationship(db.Model):
    __tablename__ = "relationships"
    parent_id = db.Column(db.Integer, db.ForeignKey("terms.id"), primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey("terms.id"), primary_key=True)
    predicate = db.Column(db.String(64), default="isExampleOf")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Term(db.Model):
    __tablename__ = "terms"
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(64))
    definition = db.Column(db.Text)
    source = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    created_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    modified_timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # data related to terms in tables/classes indicated in the first parameter
    tracker = db.relationship(
        "Track", backref="term", lazy="dynamic", cascade="all, delete-orphan"
    )
    votes = db.relationship(
        "Vote", backref="term", lazy="dynamic", cascade="all, delete-orphan"
    )
    children = db.relationship(
        "Relationship",
        foreign_keys=[Relationship.parent_id],
        backref=db.backref("parent", lazy="joined"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    parents = db.relationship(
        "Relationship",
        foreign_keys=[Relationship.child_id],
        backref=db.backref("child", lazy="joined"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    comments = db.relationship("Comment", backref="term", lazy="dynamic")

    tags = db.relationship(
        "Tag", backref="term", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return "<Term %r>" % self.term

    def exemplify(self, child, relationship="isExampleOf"):  # instanceOf
        rel = Relationship(parent_id=self.id, child_id=child.id)
        db.session.add(rel)
        db.session.commit()

    def tag(self, name, value):
        tag = Tag.query.filter_by(term_id=self.id, name=name, value=value).first()
        if tag is None:
            tag = Tag(
                term_id=self.id, name=name, value=value
            )  # compare this to the tag in the db you're doing it twice
            db.session.add(tag)
            db.session.commit()

    def vote(self, user_id, vote_type):
        vote = self.votes.filter_by(voter_id=user_id).first()
        if vote is None:
            v = Vote(voter_id=user_id, term_id=self.id, vote_type=vote_type)
            db.session.add(v)
            db.session.commit()
        elif vote.vote_type != vote_type:
            vote.vote_type = vote_type
            db.session.commit()

    def get_vote_count(self):
        if self.votes is None:
            return 0
        else:
            up_votes = self.votes.filter_by(
                vote_type="up"
            ).count()  # make vote.UP vote.DOWN properties instead
            down_votes = self.votes.filter_by(vote_type="down").count()
        return up_votes - down_votes

    def track(self, user_id):
        if not self.tracker.filter_by(tracker_id=user_id).first():
            t = Track(tracker_id=user_id, tracked_id=self.id)
            db.session.add(t)
            db.session.commit()

    def untrack(self, user_id):
        t = self.tracker.filter_by(tracker_id=user_id).first()
        if t:
            db.session.delete(t)

    def has_children(self):
        if not self:
            return False
        return self.children.count() > 0

    def has_parents(self):
        if not self:
            return False
        return self.parents.count() > 0

    def has_related(self):
        if not self:
            return False
        return self.parents.count() > 0 or self.children.count() > 0

    def has_comments(self):
        if not self:
            return False
        return self.comments.count() > 0

    def __repr__(self):
        return "<Term %r>" % self.term


class Track(db.Model):
    __tablename__ = "tracks"
    tracker_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    tracked_id = db.Column(db.Integer, db.ForeignKey("terms.id"), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    term_id = db.Column(db.Integer, db.ForeignKey("terms.id"))


class Vote(db.Model):
    __tablename__ = "votes"
    voter_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey("terms.id"), primary_key=True)
    vote_type = db.Column(db.Text)  # constrain up or down
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get("progress", 0) if job is not None else 100


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return "<Message {}>".format(self.body)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))
