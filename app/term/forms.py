from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    BooleanField,
    SelectField,
    SubmitField,
    FieldList,
)
from wtforms.validators import DataRequired, Length, Email, Regexp
from wtforms import ValidationError
from ..models import Role, User, DEFAULT_TAGS, DEFAULT_RELATIONSHIPS


class TermForm(FlaskForm):
    term = StringField("Term", validators=[DataRequired()])
    definition = TextAreaField("Definition", validators=[DataRequired()])
    source = StringField("Source")
    submit = SubmitField("Submit")
    metadata = SelectField("Metadata", choices=DEFAULT_TAGS, default=DEFAULT_TAGS[0])
    tag = StringField("Tag")


class UpdateTermForm(FlaskForm):
    term = StringField("Term", validators=[DataRequired()])
    tag_name = StringField("Name")
    tag_value = TextAreaField("Value", description="Add or edit name value pairs.")
    submit = SubmitField("Update")


class CreateTermForm(FlaskForm):
    term = StringField("Term", validators=[DataRequired()])
    tag_name = StringField("Name", default="description", validators=[DataRequired()])
    tag_value = TextAreaField(
        "Value",
        description="Add the first name value pair then save to add more.",
        validators=[DataRequired()],
    )
    submit = SubmitField("Save")


class CreateRelatedTermForm(FlaskForm):
    term = StringField("Term", validators=[DataRequired()])
    tag_name = StringField("Name", default="description", validators=[DataRequired()])
    tag_value = TextAreaField(
        "Value",
        description="Add the first name value pair then save to add more.",
        validators=[DataRequired()],
    )
    relationship_choices = SelectField(
        "Relationships", choices=DEFAULT_RELATIONSHIPS, default=DEFAULT_RELATIONSHIPS[0]
    )
    submit = SubmitField("Save")


class CommentForm(FlaskForm):
    body = TextAreaField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit")


class EmptyForm(FlaskForm):
    submit = SubmitField("Submit")


class TagForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    value = StringField("Value", validators=[DataRequired()])
    submit = SubmitField("Submit")
