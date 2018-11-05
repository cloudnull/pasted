import flask_wtf

import wtforms

from wtforms import validators


class PasteForm(flask_wtf.FlaskForm):
    content = wtforms.TextAreaField(
        'Content',
        validators=[
            validators.DataRequired()])
