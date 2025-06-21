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

# from werkzeug.datastructures import Headers
from werkzeug.security import safe_join

static = Blueprint("static", __name__)


@static.route("/covers/<sub1>/<sub2>/<book_id>.jpg")
def fb2_cover(sub1=None, sub2=None, book_id=None):
    """return cover image for book"""
    # sub1 = validate_prefix(sub1)
    # sub2 = validate_prefix(sub2)
    # book_id = validate_id(book_id)

    if book_id is None:
        return Response("Cover not found", status=404)

    pagesdir = CONFIG['PAGES']
    coverfile = os.path.relpath(os.path.normpath(os.path.join("/", f"/covers/{sub1}/{sub2}/{book_id}.jpg")), "/")

    print(pagesdir, coverfile)
    fullpath = os.path.join(pagesdir, coverfile)

    if os.path.isfile(fullpath):
        return send_file(fullpath, mimetype='image/jpeg', max_age=int(CONFIG['CACHE_TIME_ST']))
    else:
        fullpath = safe_join(pagesdir, CONFIG['DEFAULT_COVER'])
        return send_file(fullpath, mimetype='image/jpeg', max_age=int(CONFIG['CACHE_TIME_ST']))
