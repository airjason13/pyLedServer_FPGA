import os
from global_def import log
from flask import render_template

from main import app

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY


def refresh_template():
    return render_template("index.html")


@app.route("/")
def index():
    log.debug("flask route index")
    return refresh_template()
