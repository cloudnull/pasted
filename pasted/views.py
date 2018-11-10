import os
import urllib.parse as urlparse

import flask

from pasted import app
from pasted import backend
from pasted import decorators
from pasted import exceptions
from pasted import forms


CACHE_HEADERS = {
    'X-Frame-Options': 'SAMEORIGIN',
    "Cache-Control": 'public, max-age=0',
    "Pragma": "no-cache",
    "Expires": "0"
}


def _add_headers(headers_obj):
    for key, value in CACHE_HEADERS.items():
        headers_obj[key] = value
    return headers_obj



@app.route('/')
@decorators.templated()
def index():
    request = flask.request
    urlform = forms.UrlForm()
    pasteform = forms.PasteForm()
    if urlform.validate_on_submit():
        content = request.form['content']
        key, pasted_id, created = backend.write(content, backend='show_link', truncate=16)
        if created:
            flask.flash('Link created', 'success')
            status = 201
        else:
            flask.flash('Link found', 'primary')
            status = 200

        return flask.render_template('index.html', urlform=urlform), status
    elif pasteform.validate_on_submit():
        content = request.form['content']
        _, url, created = backend.write(content, backend='show_paste')

        if created:
            flask.flash('Paste created', 'success')
            status = 201
        else:
            flask.flash('Paste found', 'primary')
            status = 200
        return flask.render_template('index.html', pasteform=pasteform), status

    return flask.render_template('index.html', urlform=urlform, pasteform=pasteform)


@app.route('/pastes', methods=['POST', 'GET'])
@decorators.templated()
def pastes_index():
    request = flask.request
    pasteform = forms.PasteForm()
    if pasteform.validate_on_submit():
        content = request.form['content']
        _, url, created = backend.write(content, backend='show_paste')

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
                form=pasteform
            ),
            status
        )
        response.headers['X-XSS-Protection'] = '0'
        response.headers = _add_headers(response.headers)
        return response
    else:
        return flask.render_template('post_pastes.html', pasteform=pasteform)


@app.route('/api/search')
def search():
    return 'API call not implemented', 501


@app.route('/api/pastes', methods=['POST'])
def create_paste():
    request = flask.request
    try:
        content = request.json['content']
        _, url, _ = backend.write(content, backend='show_paste')
    except ValueError:
        raise exceptions.BadRequest('Missing paste content.')
    else:
        return_headers = {'Content-Type': 'text/plain; charset="utf-8"'}
        return_headers.update(CACHE_HEADERS)
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
        response.headers = _add_headers(response.headers)
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
def links_index(request=None):
    request = flask.request
    urlform = forms.UrlForm()
    if urlform.validate_on_submit():
        content = request.form['content']
        key, local_pasted_url, created = backend.write(content, backend='show_link', truncate=16)
        if created:
            flask.flash('Link created', 'success')
            status = 201
        else:
            flask.flash('Link found', 'primary')
            status = 200

        response = flask.make_response(
            flask.render_template(
                'return_link.html',
                go_to_remote_url=local_pasted_url,
                content=content,
                remote_url=urlparse.urljoin(
                    request.url_root,
                    local_pasted_url
                ),
                help_url=urlparse.urljoin(request.url_root, 'links/' + key),
                form=urlform
            ),
            status
        )
        response.headers['X-XSS-Protection'] = '0'
        response.headers = _add_headers(response.headers)
        return response
    else:
        return flask.render_template('post_links.html', urlform=urlform)


@app.route('/links/<pasted_id>')
def show_link_data(pasted_id):
    request = flask.request
    content = backend.read(pasted_id)
    if content:
        response = flask.make_response(
            flask.render_template(
                'return_link.html',
                go_to_remote_url='/l/{}'.format(pasted_id),
                content=content,
                remote_url=urlparse.urljoin(
                    request.url_root,
                    backend.local_url(pasted_id, backend='show_link')
                )
            )
        )
        response.headers = _add_headers(response.headers)
        return response
    else:
        flask.abort(404)


@app.route('/l/<pasted_id>')
def show_link(pasted_id):
    content = backend.read(pasted_id)
    if content:
        return flask.redirect(content, code=308), CACHE_HEADERS
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
