from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager
import enum


class Relationship(enum.Enum):
    isExampleOf = 'example'
    isTypeOf = 'type'
    isCategoryOf = 'category'


class Permission:
    FOLLOW = 1
    # TRACK = 2 # don't forget to update the db when you add a new permission
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


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

    # create db relationships
    terms = db.relationship("Term", backref="author", lazy="dynamic")
    comments = db.relationship("Comment", backref="author", lazy="dynamic")
    tracking = db.relationship(
        "Track", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    voter = db.relationship("Vote", backref="user",
                            lazy="dynamic", cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config["YAMZ_ADMIN_EMAIL"]:
                self.role = Role.query.filter_by(name="Administrator").first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    @property
    def tracked_terms(self):
        return Term.query.join(Track, Track.tracker_id == self.id).filter(
            Track.tracker_id == self.id
        )

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

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

    def is_tracking(self, term):
        if term.id is None:
            return False
        return self.tracking.filter_by(tracked_id=term.id).first() is not None

    def __repr__(self):
        return "<User %r>" % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('terms.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('terms.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Relationship(db.Model):
    __tablename__ = "relationships"
    parent_id = db.Column(db.Integer, db.ForeignKey(
        "terms.id"), primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey(
        "terms.id"), primary_key=True)
    predicate = db.Column(db.String(64), default="isExampleOf")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Term(db.Model):
    __tablename__ = "terms"
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(64), unique=True)
    definition = db.Column(db.Text)
    source = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # data related to terms in tables/classes indicated in the first parameter
    tracker = db.relationship("Track", backref="term",
                              lazy="dynamic", cascade="all, delete-orphan")
    votes = db.relationship("Vote", backref="term",
                             lazy="dynamic", cascade="all, delete-orphan")
    children = db.relationship('Relationship',
                               foreign_keys=[Relationship.parent_id],
                               backref=db.backref('parent', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    parents = db.relationship('Relationship',
                              foreign_keys=[Relationship.child_id],
                              backref=db.backref('child', lazy='joined'),
                              lazy='dynamic',
                              cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='term', lazy='dynamic')

    def __repr__(self):
        return "<Term %r>" % self.term

    def exemplify(self, child, relationship="isExampleOf"):
        rel = Relationship(parent_id=self.id, child_id=child.id)
        db.session.add(rel)
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
            up_votes = self.votes.filter_by(vote_type="up").count() # make vote.UP vote.DOWN properties instead
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

    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

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

    def follow(self, term):
        if not self.is_following(term):
            f = Follow(follower=self, followed=term)
            db.session.add(f)

    def unfollow(self, term):
        f = self.followed.filter_by(followed_id=term.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, term):
        if term.id is None:
            return False
        return self.followed.filter_by(
            followed_id=term.id).first() is not None

    def is_followed_by(self, term):
        if term.id is None:
            return False
        return self.followers.filter_by(
            follower_id=term.id).first() is not None

    def __repr__(self):
        return "<Term %r>" % self.term


class Track(db.Model):
    __tablename__ = "tracks"
    tracker_id = db.Column(db.Integer, db.ForeignKey(
        "users.id"), primary_key=True)
    tracked_id = db.Column(db.Integer, db.ForeignKey(
        "terms.id"), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    term_id = db.Column(db.Integer, db.ForeignKey('terms.id'))


class Vote(db.Model):
    __tablename__ = "votes"
    voter_id = db.Column(db.Integer, db.ForeignKey(
        "users.id"), primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey(
        "terms.id"), primary_key=True)
    vote_type = db.Column(db.Text) # constrain up or down
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
