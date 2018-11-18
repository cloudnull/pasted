import hashlib
import os
import urllib.parse as urlparse

import flask

import diskcache

import requests

from pasted import app
from pasted import cdn
from pasted import log


class LocalCache(object):
    """Context Manager for opening and closing access to the cache objects."""

    def __init__(self, cache_path=app.config['PASTE_DIR']):
        """Set the Path cache object.
        :param cache_file: File path to store cache
        :type cache_file: str
        """
        self.cache_path = cache_path

        if not os.path.isdir(self.cache_path):
            os.makedirs(self.cache_path)

    def __enter__(self):
        """Open the cache object.
        :returns: object
        """
        return self.open_cache

    def __exit__(self, *args, **kwargs):
        """Close cache object."""
        self.lc_close()

    @property
    def open_cache(self):
        """Return open caching opbject.
        :returns: object
        """
        return diskcache.Cache(directory=self.cache_path)

    def lc_open(self):
        """Open shelved data.
        :param cache_file: File path to store cache
        :type cache_file: str
        :returns: object
        """
        return self.open_cache

    def lc_close(self):
        """Close shelved data."""
        self.open_cache.close()


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
        return key, local_url(key=key, backend=backend), False

    cdn.upload(key=key, content=content.encode('utf-8'))
    log.info('Wrote paste to CDN', key=key)
    return key, local_url(key=key, backend=backend), True


def count(container=None):
    """Read the content from the CDN.

    :param container: Name of the CDN container to count.
    :type container: str
    :returns: int
    """
    with LocalCache() as c:
        object_count = c.get(b'object_count')
        if not object_count:
            log.info('No valid count object cached.')
        else:
            log.info('Cached object returned, count: %s.' % object_count)

        total_size = c.get(b'total_size')
        if not total_size:
            log.info('No valid size object cached.')
        else:
            log.info('Cached object returned, size: %s.' % total_size)

        if not all([object_count, total_size]):
            object_count, total_size = cdn.count(container=container)

            log.info('Count object cached.')
            c.set(
                b'object_count',
                object_count,
                expire=900
            )

            log.info('Size object cached.')
            c.set(
                b'total_size',
                total_size,
                expire=900
            )

    return object_count, total_size
