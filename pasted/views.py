import os
import urllib.parse as urlparse

import flask

from pasted import app
from pasted import backend
from pasted import decorators
from pasted import exceptions
from pasted import forms
from pasted import rate_limit


def _rate_limit(request):
    if request.headers.getlist("X-Forwarded-For"):
       ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
       ip = request.remote_addr
    rate_limit.throttle(ip)


@app.route('/index')
@app.route('/pastes', methods=['POST', 'GET'])
@decorators.templated()
def index():
    form = forms.PasteForm()
    if form.validate_on_submit():
        request = flask.request
        _rate_limit(request)
        content = request.form['content']
        url = backend.write(content)
        return flask.render_template('return_content.html',
                                     url=url,
                                     content=content,
                                     remote_url=urlparse.urljoin(
                                         request.url,
                                         url)
                                     )
    return dict(form=form)


@app.route('/api/search')
def search():
    return flask.render_template('not_found.html'), 501


@app.route('/api/pastes', methods=['POST'])
def create_paste():
    request = flask.request
    try:
        content = request.json['content']
        _rate_limit(request)
        url = backend.write(content)
    except ValueError as e:
        raise exceptions.BadRequest('Missing paste content. Error [ %s ]' % e)
    else:
        return urlparse.urljoin(request.url, url) + '.raw'


@app.route('/pastes/<paste_id>')
def show_paste(paste_id):
    request = flask.request
    content = backend.read(paste_id)
    if content:
        return flask.render_template('return_content.html',
                                     url=backend.local_url(paste_id),
                                     content=content,
                                     remote_url=request.url)
    else:
        flask.abort(404)


@app.route('/pastes/<paste_id>.raw')
def show_paste_raw(paste_id):
    try:
        content = backend.read(paste_id)
        if content:
            return content, 200, {'Content-Type': 'text/plain; charset="utf-8"'}
        else:
            raise exceptions.NotFound
    except exceptions.InvalidKey:
        flask.abort(404)
    except exceptions.NotFound:
        flask.abort(404)


@app.errorhandler(404)
def handle_not_found(error):
    return flask.render_template('not_found.html'), 404


@app.errorhandler(400)
def handle_bad_request(error):
    return flask.render_template('not_found.html'), 400


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
