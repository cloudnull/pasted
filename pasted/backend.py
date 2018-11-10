import hashlib
import os
import urllib.parse as urlparse

import flask

from flask import abort

import requests

from pasted import app
from pasted import cdn
from pasted import log


def local_url(key, backend):
    """Retuns a local URL.

    :param key: index item.
    :type key: str
    :param backend: function name.
    :type backend: str
    :returns: str
    """
    return flask.url_for(backend, pasted_id=key)


def remote_url(key):
    """Retuns a remote URL.

    The remote ley and CDN_ENDPOINT configuration item will be combined to
    return a remote URL.

    :param key: index item.
    :type key: str
    """
    return urlparse.urljoin(app.config['CDN_ENDPOINT'], key)


def read(key):
    """Read the content from the CDN.

    :param key: index item.
    :type key: str
    """
    r = requests.get(remote_url(key))
    if r.status_code == requests.codes.ok:
        log.info('Retrieved paste from CDN', key=key)
        return r'{}'.format(r.text)


def write(content, backend, truncate=None):
    """Write the content to a backend, and get a URL for it.

    :param content: data.
    :type content: str
    :param truncate: number of charactors to slice from the key.
    :type truncate: int
    :returns: str
    """
    key = hashlib.sha1(content.encode('utf-8')).hexdigest()
    if truncate:
        key = key[:truncate]

    if read(key):
        return local_url(key=key, backend=backend), False

    cdn.upload(key=key, content=content.encode('utf-8'))
    log.info('Wrote paste to CDN', key=key)
    return local_url(key=key, backend=backend), True
