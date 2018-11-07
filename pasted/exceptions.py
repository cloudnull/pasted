class ApiException(Exception):
    status_code = None

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        return rv


class BadRequest(ApiException):
    status_code = 400


class RateLimitExceeded(ApiException):
    status_code = 429


class NotFound(Exception):
    pass
