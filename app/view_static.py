# -*- coding: utf-8 -*-
"""static files view"""

import os

from flask import (
    Blueprint,
    Response,
    current_app
)

from .config import CONFIG

# from werkzeug.datastructures import Headers

static = Blueprint("static", __name__)


@static.route("/cover/<sub1>/<sub2>/<book_id>.jpg")
def fb2_cover(sub1=None, sub2=None, book_id=None):
    """return cover image for book"""
    # sub1 = validate_prefix(sub1)
    # sub2 = validate_prefix(sub2)
    # book_id = validate_id(book_id)

    if book_id is None:
        return Response("Cover not found", status=404)

    pagesdir = CONFIG['PAGES']
    coverfile = f"cover/{sub1}/{sub2}/{book_id}.jpg"
    if os.path.isfile(coverfile):
        return current_app.send_from_directory(pagesdir, coverfile, max_age=CONFIG['CACHE_TIME_ST'])
    else:
        return current_app.send_from_directory(pagesdir, CONFIG['DEFAULT_COVER'], max_age=CONFIG['CACHE_TIME_ST'])
