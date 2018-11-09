import os
import urllib.parse as urlparse

import flask

from pasted import app
from pasted import backend
from pasted import decorators
from pasted import exceptions
from pasted import forms
from pasted import rate_limit


@app.route('/index')
@app.route('/pastes', methods=['POST', 'GET'])
@decorators.templated()
def index():
    form = forms.PasteForm()
    if form.validate_on_submit():
        request = flask.request
        content = request.form['content']
        url, created = backend.write(content)

        if created:
            flask.flash('Paste created', 'success')
        else:
            flask.flash('Paste found', 'primary')

        response = flask.make_response(
            flask.render_template(
                'return_content.html',
                url=url,
                content=content,
                remote_url=urlparse.urljoin(request.url, url)
            )
        )
        response.headers['X-XSS-Protection'] = '0'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        return response



    return dict(form=form)


@app.route('/api/search')
def search():
    return 'API call not implemented', 501


@app.route('/api/pastes', methods=['POST'])
def create_paste():
    request = flask.request
    try:
        content = request.json['content']
        url, _ = backend.write(content)
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
            return_headers = {'Content-Type': 'text/plain; charset="utf-8"'}
            return content, 200, return_headers
        else:
            raise exceptions.NotFound
    except exceptions.InvalidKey:
        flask.abort(404)
    except exceptions.NotFound:
        flask.abort(404)


@app.errorhandler(404)
def handle_not_found(error):
    flask.flash('Paste object was not found', 'warning')
    return flask.render_template('not_found.html'), 404


@app.errorhandler(403)
def handle_bad_request(error):
    flask.flash('Past submission failed', 'warning')
    return flask.render_template('not_found.html'), 403


@app.errorhandler(400)
def handle_bad_request(error):
    flask.flash('Paste search failed', 'warning')
    return flask.render_template('not_found.html'), 400


@app.errorhandler(501)
def handle_bad_request(error):
    flask.flash('Functionality Not Implemented', 'danger')
    return flask.render_template('not_found.html'), 501


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
        mimetype='image/x-icon'
    )
