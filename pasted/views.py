import os
import urllib.parse as urlparse

import flask

from pasted import app
from pasted import backend
from pasted import decorators
from pasted import exceptions
from pasted import forms
from pasted import rate_limit


@app.route('/')
@decorators.templated()
def index():
    return flask.render_template('index.html')


@app.route('/pastes', methods=['POST', 'GET'])
@decorators.templated()
def pastes_index():
    form = forms.PasteForm()
    request = flask.request
    if form.validate_on_submit():
        content = request.form['content']
        url, created = backend.write(content, backend='show_paste')

        if created:
            flask.flash('Paste created', 'success')
            status = 201
        else:
            flask.flash('Paste found', 'primary')
            status = 200

        raw_request_url = urlparse.urljoin(request.url, url) + '.raw'
        response = flask.make_response(
            flask.render_template(
                'return_paste.html',
                url=url,
                content=content,
                remote_url=urlparse.urljoin(request.url, url),
                paste_url=raw_request_url,
                form=form
            ),
            status
        )
        response.headers['X-XSS-Protection'] = '0'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        return response
    else:
        return flask.render_template('post_pastes.html', form=form)


@app.route('/api/search')
def search():
    return 'API call not implemented', 501


@app.route('/api/pastes', methods=['POST'])
def create_paste():
    request = flask.request
    try:
        content = request.json['content']
        url, _ = backend.write(content)
    except ValueError:
        raise exceptions.BadRequest('Missing paste content.')
    else:
        return_headers = {'Content-Type': 'text/plain; charset="utf-8"'}
        return urlparse.urljoin(request.url, url) + '.raw', 201, return_headers


@app.route('/pastes/<pasted_id>')
def show_paste(pasted_id):
    request = flask.request
    content = backend.read(pasted_id)
    if content:
        response = flask.make_response(
            flask.render_template(
                'return_paste.html',
                url=backend.local_url(pasted_id, backend='show_paste'),
                content=content,
                remote_url=request.url,
            )
        )
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        return response

    else:
        flask.abort(404)


@app.route('/pastes/<pasted_id>.raw')
def show_paste_raw(pasted_id):
    try:
        content = backend.read(pasted_id)
        if content:
            return_headers = {'Content-Type': 'text/plain; charset="utf-8"'}
            return content, 200, return_headers
        else:
            raise exceptions.NotFound
    except exceptions.InvalidKey:
        flask.abort(404)
    except exceptions.NotFound:
        flask.abort(404)


@app.route('/links', methods=['POST', 'GET'])
@decorators.templated()
def links_index():
    form = forms.UrlForm()
    request = flask.request
    if form.validate_on_submit():
        content = request.form['content']
        url, created = backend.write(content, backend='show_link', truncate=16)
        if created:
            flask.flash('Link created', 'success')
            status = 201
        else:
            flask.flash('Link found', 'primary')
            status = 200

        response = flask.make_response(
            flask.render_template(
                'return_link.html',
                url=url,
                content=content,
                remote_url=urlparse.urljoin(request.url, url),
                form=form
            ),
            status
        )
        response.headers['X-XSS-Protection'] = '0'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers['Cache-Control'] = 'public, max-age=0'
        return response
    else:
        return flask.render_template('post_links.html', form=form)


@app.route('/links/<pasted_id>')
def show_link(pasted_id):
    request = flask.request
    content = backend.read(pasted_id)
    if content:
        return flask.redirect(content, code=308)
    else:
        flask.abort(404)


@app.route('/links/<pasted_id>.show')
def show_link_data(pasted_id):
    request = flask.request
    content = backend.read(pasted_id)
    if content:
        response = flask.make_response(
            flask.render_template(
                'return_link.html',
                url=backend.local_url(pasted_id, backend='show_link'),
                content=request.url,
                remote_url=content
            )
        )
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers['Cache-Control'] = 'public, max-age=0'
        return response

    else:
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
    flask.flash('Paste failed', 'warning')
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
