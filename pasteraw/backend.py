import hashlib
import os
import tempfile

import flask

from pasteraw import app
from pasteraw import base36
from pasteraw import cdn
from pasteraw import log


class InvalidKey(ValueError):
    pass


class NotFound(Exception):
    pass


def _validate_key(key):
    """Keys must be base36 encoded."""
    if not base36.validate(key):
        raise InvalidKey(key)
    return True


def _local_path(key):
    _validate_key(key)
    return os.path.expanduser('%s/%s' % (app.config['PASTE_DIR'], key))


def local_url(key):
    _validate_key(key)
    return flask.url_for('show_paste', paste_id=key)


def remote_url(key):
    _validate_key(key)
    return '%s/%s' % (app.config['CDN_ENDPOINT'], key)


def read(key):
    """Read the content from the local system.

    If the file is not local (for example, it was uploaded to a CDN), this will
    raise NotFound.

    """
    path = _local_path(key)
    if not os.path.isfile(path):
        raise NotFound('Not a local file: %s' % path)
    with open(path, 'r') as f:
        return f.read()


def write(content):
    """Write the content to a backend, and get a URL for it."""
    key = hashlib.sha1(content.encode('utf-8')).hexdigest()
    print(key)
    # ensure the PASTE_DIR exists
    if app.config['PASTE_DIR'] is None:
        app.config['PASTE_DIR'] = tempfile.mkdtemp(prefix='pasteraw-')
        log.info(
            'PASTE_DIR not set; created temporary dir',
            tmp_dir=app.config['PASTE_DIR'])
    elif not os.path.isdir(app.config['PASTE_DIR']):
        msg = 'Paste directory does not exist'
        log.warning(msg, paste_dir=app.config['PASTE_DIR'])
        raise IOError(msg)

    path = _local_path(key)
    with open(path, 'w') as f:
        f.write(content)
    log.info('Wrote paste to local filesystem', key=key)
    return local_url(key)
