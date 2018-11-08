from pasted import app


def start_app_debug():
    app.run(debug=True)


def start_app_prod():
    return app
