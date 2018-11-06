import hashlib

import fcntl
import json
import time

try:
    import anydbm as dbm
except ImportError:
    import dbm

from pasted import app
from pasted import exceptions
from pasted import log


MAX_THROTTLES = 3


class DBMContext(object):
    """A context manager to access a file in a concurrent-safe manner."""
    __slots__ = ('filename', 'mode', 'readonly', 'lockfile', 'db')

    def __init__(self, filename, readonly=False, mode=0o644):
        self.filename = filename
        self.mode = mode
        self.readonly = readonly
        self.lockfile = open(filename + '.lock', 'w+b')

    def __enter__(self):
        fcntl.lockf(
            self.lockfile.fileno(),
            fcntl.LOCK_SH if self.readonly else fcntl.LOCK_EX)
        self.db = dbm.open(self.filename, flag='c', mode=self.mode)
        return self.db

    def __exit__(self, exval, extype, tb):
        self.db.close()
        fcntl.lockf(self.lockfile.fileno(), fcntl.LOCK_UN)
        self.lockfile.close()


def _serialize(t):
    """Converts a tuple to a string."""
    return json.dumps(t, separators=(',', ':'))


def _deserialize(s):
    """Converts a string to a tuple."""
    return tuple(json.loads(s))


def throttle(request):
    ip = hashlib.sha1(request.encode('utf-8')).hexdigest()
    if app.config['TESTING']:
        # ignore rate limiting in debug mode
        return True

    rate = 10.0  # unit: messages
    per = 10.0   # unit: seconds

    with DBMContext(app.config['RATE_LIMIT_DBM_FILE']) as db:
        db.setdefault(ip, _serialize((rate, time.time(), 0)))
        allowance, last_check, throttle_count = _deserialize(db[ip].decode('utf8'))

        current = time.time()
        time_passed = current - last_check
        last_check = current
        if time_passed < per and allowance < 1:
            db[ip] = _serialize((allowance, last_check, throttle_count))
            log.warning('Deny', ip=ip, allowance=round(allowance, 1))
            raise exceptions.RateLimitExceeded(
                'Rate limit exceeded. Rate is [%s]. Retry after %s seconds.' % (rate, per))
        elif time_passed > per:
            allowance = rate

        allowance -= 1
        db[ip] = _serialize((allowance, last_check, throttle_count))

        log.warning('Allow', ip=ip, allowance=round(allowance, 1))

        return True
