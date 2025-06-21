# -*- coding: utf-8 -*-
"""static files view"""

import os

from flask import (
    Blueprint,
    Response,
    # current_app,
    send_file
)

from .config import CONFIG

static = Blueprint("static", __name__)


def safe_path(fspath):
    if fspath is None:
        return None
    return os.path.relpath(os.path.normpath(os.path.join("/", fspath)), "/")


@static.route("/covers/<sub1>/<sub2>/<book_id>.jpg")
def fb2_cover(sub1=None, sub2=None, book_id=None):
    """return cover image for book"""
    # ToDo: validate input
    # sub1 = validate_prefix(sub1)
    # sub2 = validate_prefix(sub2)
    # book_id = validate_id(book_id)

    max_age = int(CONFIG['CACHE_TIME_ST'])  # cache control

    if book_id is None:
        return Response("Cover not found", status=404)

    pagesdir = CONFIG['PAGES']
    coverfile = safe_path(f"/covers/{sub1}/{sub2}/{book_id}.jpg")

    fullpath = os.path.join(pagesdir, coverfile)

    if os.path.isfile(fullpath):
        return send_file(fullpath, mimetype='image/jpeg', max_age=max_age)
    else:
        coverfile = safe_path(CONFIG['DEFAULT_COVER'])
        fullpath = os.path.join(pagesdir, coverfile)
        return send_file(fullpath, mimetype='image/jpeg', max_age=max_age)
