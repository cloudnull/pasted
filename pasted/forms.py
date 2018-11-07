from flask_wtf import FlaskForm

from wtforms import TextAreaField
from wtforms.validators import DataRequired


class ImageForm(FlaskForm):
    pass


class PasteForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])


class SearchForm(FlaskForm):
    pass


class UrlForm(FlaskForm):
    pass
