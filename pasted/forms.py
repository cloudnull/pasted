from flask_wtf import FlaskForm

from wtforms import TextAreaField
from wtforms.validators import DataRequired

class PasteForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])

class UrlForm(FlaskForm):
    pass

class ImageForm(FlaskForm):
    pass
