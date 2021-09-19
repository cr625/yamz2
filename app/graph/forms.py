from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import SubmitField, StringField
from wtforms.validators import URL


class UploadForm(FlaskForm):
    file = FileField(
        "File", validators=[FileRequired()]
    )  # TODO: Add file size limit, add filters
    submit = SubmitField("Submit")


class ImportUrlForm(FlaskForm):
    url = StringField("URL", validators=[URL()])
    submit = SubmitField("Submit")
