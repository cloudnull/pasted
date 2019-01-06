import os
import time
import json
import urllib.parse as urlparse

import flask

import requests

from pasted import app
from pasted import auto
from pasted import backend
from pasted import csrf
from pasted import decorators
from pasted import exceptions
from pasted import forms
from pasted import log

CACHE_HEADERS = {
    'X-Frame-Options': 'SAMEORIGIN',
    "Cache-Control": 'public, max-age=120'
}


def _add_headers(headers_obj):
    for key, value in CACHE_HEADERS.items():
        headers_obj[key] = value
    return headers_obj


def _get_description(content, content_slice=48):
    try:
        first_line = content.splitlines()[0]
        if len(first_line) == 0:
            raise IndexError('Content has no value')
        elif slice is None:
            return 'Pasted-Content: {}'.format(first_line)
        elif len(first_line) > content_slice:
            return 'Pasted-Content: {} ...'.format(content_slice[:content_slice])
        else:
            return 'Pasted-Content: {}'.format(first_line)
    except Exception as e:
        log.warning('Content parsing failed: %s' % e)
        return 'Pasted-Object: Brought to you by pasted.tech'


@app.route('/')
@decorators.templated()
def index():
    urlform = forms.UrlForm()
    pasteform = forms.PasteForm()
    obj_count, obj_total_size = backend.count()
    log.info('object count %s' % obj_count)

    return flask.render_template(
        'index.html',
        urlform=urlform,
        pasteform=pasteform,
        obj_count=obj_count,
        obj_total_size=round((obj_total_size / 1024 / 1024), 3)
    )


@app.route('/api/pastes', methods=['POST'])
@auto.doc()
def create_paste():
    """Create Pastes.

    On successful POST this API will return a URL with the <pasted_id> for the
    newly created content.

    POST content must be in JSON format and contain the key "content"

    > "{'content': 'example'}"

    :returns: str
    """
    request = flask.request
    try:
        content = request.json['content']
        _, url, _ = backend.write(content, backend='show_paste')
    except ValueError:
        raise exceptions.BadRequest('Missing paste content.')
    else:
        return_url = urlparse.urljoin(request.url, url) + '.raw'
        return_headers = {
            'Content-Type': 'text/plain; charset="utf-8"',
            'Location': return_url
        }
        return_headers.update(CACHE_HEADERS)
        return return_url, 201, return_headers


@app.route('/api/links', methods=['POST'])
@auto.doc()
def create_links():
    """Create shortened links.

    On successful POST this API will return a URL with the <pasted_id> for the
    newly created content. The link shortener will validate the content is a
    "valid" URL before writting the specific content and returning the data.

    POST content must be in JSON format and contain the key "content"

    > "{'content': 'example'}"

    :returns: str
    """
    request = flask.request
    try:
        content = request.json['content']
        valid_url = urlparse.urlparse(content)
        if valid_url.scheme and valid_url.netloc:
            _, url, _ = backend.write(content, backend='show_link', truncate=16)
        else:
            raise exceptions.BadRequest('No valid URL provided')
    except ValueError:
        raise exceptions.BadRequest('Missing link content')
    else:
        return_url = urlparse.urljoin(request.url, url)
        return_headers = {
            'Content-Type': 'text/plain; charset="utf-8"',
            'Location': return_url
        }
        return_headers.update(CACHE_HEADERS)
        return return_url, 201, return_headers


@app.route('/info/tos')
def show_tos():
    return flask.render_template(
        'tos.html',
        pasted_page_description='Pasted Terms of Service.'
    )


@app.route('/info/cli_client')
def show_usage_cli_client():
    return flask.render_template(
        'usage_cli.html',
        pasted_page_description='Pasted CLI client information.'
    )


@app.route('/info/browser_plugin')
def show_usage_browser_plugin():
    return flask.render_template(
        'usage_browser.html',
        pasted_page_description='Pasted browser plugin information.'
    )


@app.route('/info/api')
def show_usage_api():
    return flask.render_template(
        'usage_api.html',
        api_doc=auto.generate(),
        pasted_page_description='Pasted API information.'
    )


@app.route('/links', methods=['POST', 'GET'])
@decorators.templated()
def links_index():
    urlform = forms.UrlForm()
    if urlform.validate_on_submit():
        key, url, created = backend.write(urlform.content.data, backend='show_link', truncate=16)
        if created:
            flask.flash('Link created', 'success')
        else:
            flask.flash('Link found', 'primary')

        response = flask.make_response(
            flask.redirect(flask.url_for('show_link_data', pasted_id=key))
        )
        response.headers['X-XSS-Protection'] = '0'
        response.headers = _add_headers(response.headers)
        return response
    else:
        log.warning('Form validation failed')
        for values in urlform.errors.values():
            for value in values:
                log.warning('urlform errors', error=value)
                flask.flash(value, 'danger')
        return flask.render_template(
            'post_links.html',
            urlform=urlform,
            pasted_page_description='Shorten links, make connections.'
        )


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
                ),
                pasted_page_description=_get_description(
                    content=content,
                    content_slice=256
                )
            )
        )
        response.headers = _add_headers(response.headers)
        return response
    else:
        flask.abort(404)


@app.route('/l/<pasted_id>')
@auto.doc()
def show_link(pasted_id):
    """Show or visit a shortened link.

    This method will redirect with a 308 forwarding the original method to the
    redirected URL.

    :param paste_id: ID number (sha1) of a valid paste.
    :type paste_id: str
    :returns: str
    """
    request = flask.request
    content = backend.read(pasted_id)
    if content:
        return_url = urlparse.urljoin(
            request.url_root,
            backend.local_url(pasted_id, backend='show_link')
        )
        return_headers = {
            'Referer': return_url,
            'Referrer-Policy': 'unsafe-url'
        }
        return_headers.update(CACHE_HEADERS)
        return flask.redirect(content, code=308), return_headers
    else:
        flask.abort(404)


@app.route('/pastes', methods=['POST', 'GET'])
@decorators.templated()
def pastes_index():
    pasteform = forms.PasteForm()
    if pasteform.validate_on_submit():
        key, url, created = backend.write(pasteform.content.data, backend='show_paste')
        if created:
            flask.flash('Paste created', 'success')
        else:
            flask.flash('Paste found', 'primary')

        response = flask.make_response(
            flask.redirect(flask.url_for('show_paste', pasted_id=key))
        )
        response.headers['X-XSS-Protection'] = '0'
        response.headers['X-RAW-Location'] = flask.url_for(
            'show_paste_raw', pasted_id=key, _external=True
        )
        response.headers = _add_headers(response.headers)
        return response
    else:
        log.warning('Form validation failed')
        for values in pasteform.errors.values():
            for value in values:
                log.warning('urlform errors', error=value)
                flask.flash(value, 'danger')
        return flask.render_template(
            'post_pastes.html',
            pasteform=pasteform,
            pasted_page_description='Create content, tell a story.'
        )


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
                pasted_page_description=_get_description(content=content)
            )
        )
        response.headers = _add_headers(response.headers)
        return response

    else:
        flask.abort(404)


@app.route('/pastes/<pasted_id>.raw')
@auto.doc()
def show_paste_raw(pasted_id):
    """Show the raw content of a paste.

    All requests will be forwarded to the CDN provider and any returned object
    will be formatted as raw text encoded UTF-8.

    :param paste_id: ID number (sha1) of a valid paste
    :type paste_id: str
    :returns: str
    """
    request = flask.request
    content = backend.read(pasted_id)
    if content:
        return_headers = {
            'Content-Type': 'text/plain; charset="utf-8"',
            'Location': urlparse.urljoin(
                request.url_root,
                backend.local_url(pasted_id, backend='show_paste')
            )
        }
        return_headers.update(CACHE_HEADERS)
        return content, 200, return_headers
    else:
        flask.abort(404)


@app.route('/robots.txt', methods=['GET'])
def robots():
    response = flask.make_response(
        flask.render_template('robots.txt'),
        200
    )
    response.headers['Content-Type'] = 'text/plain; charset="utf-8"'
    response.headers = _add_headers(response.headers)
    return response


@app.errorhandler(404)
def handle_not_found(error):
    return flask.render_template(
        'error_general.html',
        error=error,
        pasted_page_description=_get_description(content=error)
    ), 404


@app.errorhandler(403)
def handle_bad_request(error):
    return flask.render_template(
        'error_general.html',
        error=error,
        pasted_page_description=_get_description(content=error)
    ), 403


@app.errorhandler(400)
def handle_bad_request(error):
    return flask.render_template(
        'error_general.html',
        error=error,
        pasted_page_description=_get_description(content=error)
    ), 400


@app.errorhandler(501)
def handle_bad_request(error):
    return flask.render_template(
        'error_general.html',
        error=error,
        pasted_page_description=_get_description(content=error)
    ), 501


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
        os.path.join(
            app.root_path,
            'static'
        ),
        'favicon.ico',
        mimetype='image/x-icon'
    )
