from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp
from wtforms import ValidationError
from ..models import Role, User


class TermForm(FlaskForm):
    term = StringField("Term", validators=[DataRequired()])
    definition = TextAreaField("Definition", validators=[DataRequired()])
    source = StringField("Source")
    submit = SubmitField("Submit")
