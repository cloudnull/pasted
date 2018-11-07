import hashlib
import os
import tempfile

import flask

from flask import abort

from pasted import app
from pasted import cdn
from pasted import log
from pasted import exceptions


def _local_path(key):
    return os.path.expanduser('%s/%s' % (app.config['PASTE_DIR'], key))


def local_url(key):
    return flask.url_for('show_paste', paste_id=key)


def remote_url(key):
    return '%s/%s' % (app.config['CDN_ENDPOINT'], key)


def read(key):
    """Read the content from the local system.

    If the file is not local (for example, it was uploaded to a CDN), this will
    raise NotFound.
    """

    try:
        if len(key) != 40 or not int(key, 16):
            abort(400)
    except ValueError:
        abort(400)

    path = _local_path(key)
    if not os.path.isfile(path):
        abort(404)

    with open(path, 'r') as f:
        return f.read()


def write(content):
    """Write the content to a backend, and get a URL for it."""
    key = hashlib.sha1(content.encode('utf-8')).hexdigest()

    path = _local_path(key)
    with open(path, 'w') as f:
        f.write(content)

    log.info('Wrote paste to local filesystem', key=key)
    return local_url(key)
