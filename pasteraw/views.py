import os

import flask

from pasteraw import app
from pasteraw import backend
from pasteraw import decorators
from pasteraw import exceptions
from pasteraw import forms
from pasteraw import rate_limit


def _rate_limit(headers):
    request = flask.request
    headers = request.headers
    if headers.getlist("X-Forwarded-For"):
       ip = headers.getlist("X-Forwarded-For")[0]
    else:
       ip = request.remote_addr
    rate_limit.throttle(ip)


@app.route('/', methods=['POST', 'GET'])
@decorators.templated()
def index():
    form = forms.PasteForm()
    form.meta.csrf=False
    if form.validate_on_submit():
        request = flask.request
        _rate_limit(request.headers)
        url = backend.write(flask.request.form['content'])
        return flask.redirect(url)
    return dict(form=form)


@app.route('/pastes', methods=['POST'])
def create_paste():
    try:
        request = flask.request
        content = request.json['content']
        _rate_limit(request.headers)
        url = backend.write(content)
    except ValueError as exp:
        raise exceptions.BadRequest('Missing paste content %s' % exp)
    else:
        return flask.redirect(url)
 


@app.route('/<paste_id>')
def show_paste(paste_id):
    """Either returns a locally-stored paste or redirects to CDN.

    Redirecting to the CDN handles both legacy paste URLs and pastes that used
    to be stored locally, but have since been moved to the CDN.

    """
    try:
        content = backend.read(paste_id)
        return content, 200, {'Content-Type': 'text/plain; charset="utf-8"'}
    except backend.InvalidKey:
        flask.abort(404)
    except backend.NotFound:
        # The file is not here, but maybe it's on the CDN?
        url = backend.remote_url(paste_id)
        return flask.redirect(url, 301)


@app.errorhandler(404)
def handle_not_found(error):
    return flask.render_template('not_found.html'), 404


@app.errorhandler(exceptions.BadRequest)
def handle_bad_request(error):
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(exceptions.RateLimitExceeded)
def handle_rate_limit_exceeded(error):
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/x-icon')
