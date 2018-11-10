from flask_wtf import FlaskForm

import wtforms

from wtforms.validators import DataRequired
from wtforms.validators import URL


class ImageForm(FlaskForm):
    pass


class PasteForm(FlaskForm):
    content = wtforms.TextAreaField('Content', validators=[DataRequired()])


class SearchForm(FlaskForm):
    pass


class UrlForm(FlaskForm):
    content = wtforms.StringField('Url', validators=[DataRequired(), URL()])
