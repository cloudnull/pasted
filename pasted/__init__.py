import logging
import logging.handlers
import os

import flask


app = flask.Flask(__name__, instance_relative_config=True)

# start with a default configuration
app.config.from_object('pasted.config')

app.config.from_pyfile('/etc/pasted.conf.py', silent=True)

try:
    app.config.from_envvar('PASTED_SETTINGS', silent=True)
except RuntimeError:
    pass

# ensure the local PASTE_DIR exists
if not os.path.exists(app.config['PASTE_DIR']):
    os.mkdir(path=app.config['PASTE_DIR'])

formatter = logging.Formatter(
    fmt='[%(asctime)s.%(msecs)03d] pid=%(process)d %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

if app.debug:
    for handler in app.logger.handlers:
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)

import pasted.views  # flake8: noqa
