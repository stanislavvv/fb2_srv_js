# -*- coding: utf-8 -*-
"""static files view"""

import os
import io
import time
import zipfile
import lxml.etree as et

from bs4 import BeautifulSoup
from flask import (
    Blueprint,
    Response,
    current_app,
    send_file,
    url_for,
    redirect,
    render_template
)

from .validate import (
    safe_path,
    validate_id,
    validate_zip,
    validate_fb2
)
from .config import CONFIG, URL, LANG

static = Blueprint("static", __name__)


def redir_invalid(redir_name):
    """return Flask redirect"""
    location = url_for(redir_name)
    code = 302  # for readers
    return redirect(location, code, Response=None)


def fb2_out(zip_file: str, filename: str):
    """return .fb2.zip for downloading"""
    if filename.endswith('.zip'):  # will accept any of .fb2 or .fb2.zip
        filename = filename[:-4]
    zipdir = current_app.config['ZIPS']
    zippath = zipdir + "/" + zip_file
    try:
        data = ""
        with zipfile.ZipFile(zippath) as z_file:
            with z_file.open(filename) as fb2:
                data = fb2.read()
        return data
    except Exception as ex:  # pylint: disable=W0703
        print(ex)
        return None


def html_out(zip_file: str, filename: str):
    """create html from fb2 for reading"""
    transform = CONFIG['TRANSFORM']
    zipdir = CONFIG['ZIPS']
    zippath = zipdir + "/" + zip_file
    try:
        with zipfile.ZipFile(zippath) as z_file:
            with z_file.open(filename) as fb2:
                data = io.BytesIO(fb2.read())
                b_soap = BeautifulSoup(data, 'xml')
                doc = b_soap.prettify()
                dom = et.fromstring(bytes(doc, encoding='utf8'))
                html = transform(dom)
                return str(html)
    except Exception as ex:  # pylint: disable=W0703
        print(ex)
        return None


def create_html_response(data, tpl_name, cache_period=int(CONFIG['CACHE_TIME'])):
    """return html response from opds data"""
    title = data["title"]
    path = data["path"]
    if "urlparams" in data:
        urlparams = data["urlparams"]
    else:
        urlparams = ""
    page = render_template(tpl_name, title=title, path=path, urlparams=urlparams, data=data)
    resp = Response(page, mimetype='text/html')
    resp.headers['Cache-Control'] = "max-age=%d, must-revalidate" % cache_period
    return resp


@static.route(URL["cover"] + "<sub1>/<sub2>/<book_id>.jpg")
def fb2_cover(sub1=None, sub2=None, book_id=None):
    """return cover image for book"""
    sub1 = validate_id(sub1)
    sub2 = validate_id(sub2)
    book_id = validate_id(book_id)

    max_age = int(CONFIG['CACHE_TIME_ST'])  # cache control

    if book_id is None:
        return Response("Cover not found", status=404)

    pagesdir = CONFIG['PAGES']
    coverfile = safe_path(f"/covers/{sub1}/{sub2}/{book_id}.jpg")

    fullpath = os.path.join(pagesdir, coverfile)

    if os.path.isfile(fullpath):
        return send_file(fullpath, mimetype='image/jpeg', max_age=max_age)
    coverfile = safe_path(CONFIG['DEFAULT_COVER'])
    fullpath = os.path.join(pagesdir, coverfile)
    return send_file(fullpath, mimetype='image/jpeg', max_age=max_age)


@static.route(URL["dl"] + "<zip_file>/<filename>")
def fb2_download(zip_file=None, filename=None):
    """send fb2.zip on download request"""
    if filename.endswith('.zip'):  # will accept any of .fb2 or .fb2.zip with right filename in .zip
        filename = filename[:-4]
    if not zip_file.endswith('.zip'):
        zip_file = zip_file + '.zip'
    zip_file = validate_zip(zip_file)
    filename = validate_fb2(filename)
    if zip_file is None or filename is None:
        return redir_invalid(CONFIG['REDIR_FROM_ERR'])
    fb2data = fb2_out(zip_file, filename)
    if fb2data is not None:  # pylint: disable=R1705
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:  # pylint: disable=C0103
            data = zipfile.ZipInfo(filename)
            data.date_time = time.localtime(time.time())[:6]
            data.compress_type = zipfile.ZIP_DEFLATED
            data.file_size = len(fb2data)
            zf.writestr(data, fb2data)
        memory_file.seek(0)
        zip_name = filename + ".zip"
        # pylint: disable=E1123
        max_age = int(CONFIG['CACHE_TIME_ST'])  # cache control
        return send_file(memory_file, download_name=zip_name, as_attachment=True, max_age=max_age)
    return Response("Book not found", status=404)


@static.route(URL["read"] + "<zip_file>/<filename>")
def fb2_read(zip_file=None, filename=None):
    """translate fb2 to html for read request"""
    if filename.endswith('.zip'):  # will accept any of .fb2 or .fb2.zip with right filename in .zip
        filename = filename[:-4]
    if not zip_file.endswith('.zip'):
        zip_file = zip_file + '.zip'
    zip_file = validate_zip(zip_file)
    filename = validate_fb2(filename)
    if zip_file is None or filename is None:
        return redir_invalid(CONFIG['REDIR_FROM_ERR'])
    data = html_out(zip_file, filename)
    cachectl = "maxage=%d, must-revalidate" % int(CONFIG['CACHE_TIME_ST'])

    if data is not None:  # pylint: disable=R1705
        resp = Response(data, mimetype='text/html')
        resp.headers['Cache-Control'] = cachectl
        return resp
    return Response("Book not found", status=404)


@static.route("/")
def webroot():
    data = {
        "title": CONFIG["TITLE"],
        "approot": CONFIG["APPLICATION_ROOT"],
        "path": "/",
    }
    tpl = "index.html"
    return create_html_response(data, tpl)


@static.route("/interface.js")
def interface_js():
    start = URL["start"]
    approot = CONFIG["APPLICATION_ROOT"]
    data = {
        "title": CONFIG["TITLE"],  # mandatory param
        "approot": approot,
        "path": "/interface.js",  # mandatory param
        "opds_prefix": f"{approot}{start}".strip('/'),
        "genre_prefix": URL["genre"].strip('/').replace('opds/', ''),
        "lang_authors": LANG["js_authors"],
        "lang_links": LANG["js_links"],
        "lang_genres": LANG["js_genres"],
    }
    tpl = "interface.js"
    return create_html_response(data, tpl, cache_period=int(CONFIG['CACHE_TIME_ST']))


@static.route("/favicon.ico")
def favicon():
    return current_app.send_static_file("favicon.ico")
