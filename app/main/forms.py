from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

# Forms are consolidated here and imported where needed.


class CreateTermForm(FlaskForm):
    term = StringField("Term", validators=[DataRequired()])
    definition = TextAreaField("Definition", validators=[DataRequired()])
    submit = SubmitField("Save")
