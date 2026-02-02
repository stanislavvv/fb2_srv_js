# -*- coding: utf-8 -*-
"""static files view"""

import os
import io
import time
import zipfile
import re
import lxml.etree as et

from bs4 import BeautifulSoup
from io import BytesIO  # noqa
from flask import (
    Blueprint,
    Response,
    current_app,
    send_file,
    url_for,
    redirect,
    request,
    render_template
)

from .validate import (
    safe_path,
    validate_id,
    validate_zip,
    validate_fb2
)
from .config import CONFIG, URL, LANG, XSL_READ
from .data import is_auth

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
        current_app.logger.error("Error in file: %s/%s: %s", zip_file, filename, ex)
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
        current_app.logger.error("Error in file: %s/%s: %s", zip_file, filename, ex)
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


def add_xsl_line(fb2data, xsl_line):
    # Проверяем кодировку из XML декларации или используем 'utf-8' по умолчанию
    match = re.search(r'^<\?xml.*encoding=["\']([^"\']+)["\']', fb2data.decode('utf-8', errors='ignore'))
    encoding = match.group(1) if match else 'utf-8'

    # Преобразуем fb2data в строку
    xml_string = fb2data.decode(encoding)

    # Находим конец XML декларации
    xml_declaration_end = xml_string.find('>') + 1

    # Вставляем xsl_line после XML декларации
    modified_xml_string = (xml_string[:xml_declaration_end] + '\n' +
                           xsl_line.strip() +
                           xml_string[xml_declaration_end:])

    return modified_xml_string.encode(encoding)


def require_auth(f):
    """Require HTTP Basic auth decorator"""
    def decorated_function(*args, **kwargs):
        # есть ли файл с паролями
        passwd_path = os.path.join(CONFIG["ZIPS"], "passwd")
        if not os.path.exists(passwd_path):
            # Если файла нет, пропускаем авторизацию
            return f(*args, **kwargs)
        auth = request.authorization
        if not auth or not is_auth(auth.username, auth.password):
            # 401 response forces the browser to show the login dialog
            return Response(
                'Authentication required',
                401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}
            )
        return f(*args, **kwargs)
    return decorated_function


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
    coverfile = safe_path("%s%s/%s/%s.jpg" % (
        URL["cover"],
        sub1,
        sub2,
        book_id
    ))

    fullpath = os.path.join(pagesdir, coverfile)

    if os.path.isfile(fullpath):
        return send_file(fullpath, mimetype='image/jpeg', max_age=max_age)
    coverfile = safe_path(CONFIG['DEFAULT_COVER'])
    fullpath = os.path.join(pagesdir, coverfile)
    return send_file(fullpath, mimetype='image/jpeg', max_age=max_age)


@require_auth
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


@require_auth
@static.route(URL["plain"] + "<zip_file>/<filename>")
def fb2_plain(zip_file=None, filename=None):
    """send plain fb2 on download request"""
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
        cachectl = "maxage=%d, must-revalidate" % int(CONFIG['CACHE_TIME_ST'])
        xsl_line = XSL_READ % URL["xsl_read"]

        fb2prepared = add_xsl_line(fb2data, xsl_line)

        # resp = Response(fb2data, content_type='application/x-fb2+xml')
        resp = Response(fb2prepared, content_type='text/xhtml')
        resp.headers['Cache-Control'] = cachectl
        return resp
    return Response("Book not found", status=404)


@require_auth
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
        "lang_lang": LANG["js_lang"],
    }
    tpl = "interface.js"
    return create_html_response(data, tpl, cache_period=int(CONFIG['CACHE_TIME_ST']))


@static.route("/favicon.ico")
def favicon():
    return current_app.send_static_file("favicon.ico")


@static.route("/fb2.xsl")
def fb2_xsl():
    return current_app.send_static_file("fb2.xsl")
