# -*- coding: utf-8 -*-
"""opds responses"""

import os
import xmltodict
import logging
import urllib

from flask import Blueprint, Response, request

from .opds_struct import (
    opds_main,
    opds_simple_list,
    opds_author_page,
    opds_book_list,
    opds_search_main
)
from .opds_db import opds_books_db, opds_simple_list_db
from .config import CONFIG, URL, LANG
from .strings import id2path
from .data import get_meta_name, get_genre_name, is_auth
from .validate import (
    validate_prefix,
    validate_id,
    validate_genre,
    validate_search
)

opds = Blueprint("opds", __name__)


def create_opds_response(data, cache_time=CONFIG["CACHE_TIME"]):
    """data to xml to flask response"""
    if data is None:
        return Response("Page not found", status=404)
    try:
        xml = xmltodict.unparse(data, pretty=True)
        resp = Response(xml, mimetype='text/xml')
        resp.headers['Cache-Control'] = f"max-age={cache_time}, must-revalidate"
        return resp
    except Exception as e:
        # Log the exception for debugging purposes
        logging.error(f"Error creating OPDS response: {e}")
        # Return an error response (you might want a more specific error page)
        return Response("Internal Server Error", status=500, mimetype='text/plain')


@opds.before_request
def require_auth():
    """Require HTTP Basic auth on every request handled by this blueprint."""
    # Check if passwd file exists before requiring auth
    passwd_file = os.path.join(CONFIG["ZIPS"], "passwd")
    if not os.path.exists(passwd_file):
        return  # Skip authentication if passwd file doesn't exist

    auth = request.authorization
    if not auth or not is_auth(auth.username, auth.password):
        return Response(
            'Authentication required',
            401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'}
        )


@opds.route(URL["start"], methods=['GET'])
def opds_root():
    """opds root"""
    return create_opds_response(opds_main())


@opds.route(URL["authidx"], methods=['GET'])
def opds_auth_root():
    """authors root"""
    params = {
        "index": URL["authidx"].replace("/opds/", "", 1),
        "tag": "tag:root:authors",
        "subtag": "tag:authors:",
        "title": LANG["authors"],
        "subtitle": LANG["auth_root_subtitle"],
        "simple_baseref": URL["authidx"],
        "strong_baseref": URL["author"],
        "self": URL["authidx"],
        "start": URL["start"],
        "up": URL["start"]
    }
    return create_opds_response(opds_simple_list(params))


@opds.route(URL["authidx"] + "<sub>", methods=['GET'])
def opds_auth_sub(sub):
    """first letter view for authors"""
    sub = validate_prefix(sub)
    params = {
        "index": URL["authidx"].replace("/opds/", "", 1) + sub,
        "tag": "tag:authors:" + sub,
        "subtag": "tag:authors:",
        "title": LANG["auth_root_subtitle"] + sub,
        "subtitle": LANG["authors_num"],
        "use_nums": True,
        "layout": "subs",
        "simple_baseref": URL["authidx"] + sub + "/",
        "strong_baseref": URL["author"],
        "self": URL["authidx"] + sub,
        "start": URL["start"],
        "up": URL["authidx"]
    }
    return create_opds_response(opds_simple_list(params))


@opds.route(URL["authidx"] + "<sub1>/<sub2>", methods=['GET'])
def opds_auth_sub2(sub1, sub2):
    """<first letter>/<first three letters> view for authors"""
    sub1 = validate_prefix(sub1)
    sub2 = validate_prefix(sub2)
    params = {
        "index": URL["authidx"].replace("/opds/", "", 1) + f"{sub1}/{sub2}",
        "tag": "tag:authors:" + sub2,
        "subtag": "tag:author:",
        "title": LANG["auth_root_subtitle"] + sub2,
        "subtitle": "'%s'",
        "simple_baseref": URL["authidx"] + sub1 + "/" + sub2,
        "strong_baseref": URL["author"],
        "self": URL["authidx"] + sub1 + "/" + sub2,
        "start": URL["start"],
        "up": URL["authidx"] + sub1
    }
    return create_opds_response(opds_simple_list(params))


@opds.route(URL["author"] + "<sub1>/<sub2>/<id>", methods=['GET'])
def opds_author_main(sub1, sub2, id):
    """author's main page"""
    sub1 = validate_id(sub1)
    sub2 = validate_id(sub2)
    id = validate_id(id)
    params = {
        "index": URL["author"].replace("/opds/", "", 1) + f"{sub1}/{sub2}/{id}",
        "id": id,
        "sub1": sub1,
        "sub2": sub2,
        "tag": "tag:author:" + id,
        "subtag": "tag:author:" + id,
        "title": LANG["author_tpl"],
        "simple_baseref": URL["authidx"] + sub1 + "/" + sub2,
        "strong_baseref": URL["author"],
        "self": URL["author"] + id2path(id),
        "start": URL["start"],
        "up": URL["authidx"]
    }
    return create_opds_response(opds_author_page(params))


@opds.route(URL["author"] + "<sub1>/<sub2>/<id>/sequences", methods=['GET'])
def opds_author_seqs(sub1, sub2, id):
    """author's sequences list"""
    sub1 = validate_id(sub1)
    sub2 = validate_id(sub2)
    id = validate_id(id)
    params = {
        "index": URL["author"].replace("/opds/", "", 1) + f"{sub1}/{sub2}/{id}/sequences",
        "nameindex": URL["author"].replace("/opds/", "", 1) + f"{sub1}/{sub2}/{id}",
        "id": id,
        "sub1": sub1,
        "sub2": sub2,
        "tag": "tag:author:" + id + ":sequences",
        "subtag": "tag:author:" + id,
        "title": LANG["seqs_author"],
        "subtitle": LANG["books_num"],
        "layout": "name_id_list",
        "use_nums": True,
        "simple_baseref": URL["authidx"] + sub1 + "/" + sub2,
        "strong_baseref": URL["author"] + f"{sub1}/{sub2}/{id}/",
        "self": URL["author"] + id2path(id) + "/sequences",
        "start": URL["start"],
        "up": URL["author"] + id2path(id)
    }
    return create_opds_response(opds_simple_list(params))


@opds.route(URL["author"] + "<sub1>/<sub2>/<id>/<seq_id>", methods=['GET'])
def opds_author_seq(sub1, sub2, id, seq_id):
    """author's books in sequence"""
    sub1 = validate_id(sub1)
    sub2 = validate_id(sub2)
    id = validate_id(id)
    seq_id = validate_id(seq_id)
    params = {
        "index": URL["author"].replace("/opds/", "", 1) + f"{sub1}/{sub2}/{id}/",
        "id": id,
        "sub1": sub1,
        "sub2": sub2,
        "tag": "tag:author:" + id + ":" + seq_id,
        "subtag": "tag:author:" + id,
        "seq_id": seq_id,
        "title": LANG["books_author_seq"],
        "layout": "author_seq",
        "baseref": URL["author"],
        "authref": URL["author"],
        "seqref": URL["seq"],
        "self": URL["author"] + id2path(id) + "/" + seq_id,
        "start": URL["start"],
        "up": URL["author"] + id2path(id) + "/sequences"
    }
    return create_opds_response(opds_book_list(params))


@opds.route(URL["author"] + "<sub1>/<sub2>/<id>/sequenceless", methods=['GET'])
def opds_author_nonseq(sub1, sub2, id):
    """author's books not in any sequence"""
    sub1 = validate_id(sub1)
    sub2 = validate_id(sub2)
    id = validate_id(id)
    params = {
        "index": URL["author"].replace("/opds/", "", 1) + f"{sub1}/{sub2}/{id}/",
        "id": id,
        "sub1": sub1,
        "sub2": sub2,
        "tag": "tag:author:" + id,
        "subtag": "tag:author:" + id,
        "title": LANG["books_author_nonseq"],
        "layout": "author_nonseq",
        "baseref": URL["author"],
        "authref": URL["author"],
        "seqref": URL["seq"],
        "self": URL["author"] + id2path(id) + "/sequenceless",
        "start": URL["start"],
        "up": URL["author"] + id2path(id)
    }
    return create_opds_response(opds_book_list(params))


@opds.route(URL["author"] + "<sub1>/<sub2>/<id>/alphabet", methods=['GET'])
def opds_author_alphabet(sub1, sub2, id):
    """author's all books sort by book_title"""
    sub1 = validate_id(sub1)
    sub2 = validate_id(sub2)
    id = validate_id(id)
    params = {
        "index": URL["author"].replace("/opds/", "", 1) + f"{sub1}/{sub2}/{id}/",
        "id": id,
        "sub1": sub1,
        "sub2": sub2,
        "tag": "tag:author:" + id,
        "subtag": "tag:author:" + id,
        "title": LANG["books_author_alphabet"],
        "layout": "author_alpha",
        "baseref": URL["author"],
        "authref": URL["author"],
        "seqref": URL["seq"],
        "self": URL["author"] + id2path(id) + "/alphabet",
        "start": URL["start"],
        "up": URL["author"] + id2path(id)
    }
    return create_opds_response(opds_book_list(params))


@opds.route(URL["author"] + "<sub1>/<sub2>/<id>/time", methods=['GET'])
def opds_author_time(sub1, sub2, id):
    """author's all books sort by date"""
    sub1 = validate_id(sub1)
    sub2 = validate_id(sub2)
    id = validate_id(id)
    params = {
        "index": URL["author"].replace("/opds/", "", 1) + f"{sub1}/{sub2}/{id}/",
        "id": id,
        "sub1": sub1,
        "sub2": sub2,
        "tag": "tag:author:" + id,
        "subtag": "tag:author:" + id,
        "title": LANG["books_author_time"],
        "layout": "author_time",
        "baseref": URL["author"],
        "authref": URL["author"],
        "seqref": URL["seq"],
        "self": URL["author"] + id2path(id) + "/time",
        "start": URL["start"],
        "up": URL["author"] + id2path(id)
    }
    return create_opds_response(opds_book_list(params))


@opds.route(URL["seqidx"], methods=['GET'])
def opds_seq_root():
    """sequences root"""
    params = {
        "index": URL["seqidx"].replace("/opds/", "", 1),
        "tag": "tag:root:sequences",
        "subtag": "tag:sequences:",
        "title": LANG["sequences"],
        "subtitle": LANG["seq_root_subtitle"],
        "simple_baseref": URL["seqidx"],
        "strong_baseref": URL["seq"],
        "self": URL["seqidx"],
        "start": URL["start"],
        "up": URL["start"]
    }
    return create_opds_response(opds_simple_list(params))


@opds.route(URL["seqidx"] + "<sub>", methods=['GET'])
def opds_seq_sub(sub):
    """sequences first letter view"""
    sub = validate_prefix(sub)
    params = {
        "index": URL["seqidx"].replace("/opds/", "", 1) + sub,
        "tag": "tag:sequences:" + sub,
        "subtag": "tag:sequences:",
        "title": LANG["seq_root_subtitle"] + sub,
        "subtitle": LANG["seqs_num"],
        "use_nums": True,
        "layout": "subs",
        "simple_baseref": URL["seqidx"] + sub + "/",
        "strong_baseref": URL["seq"],
        "self": URL["seqidx"] + sub,
        "start": URL["start"],
        "up": URL["seqidx"]
    }
    return create_opds_response(opds_simple_list(params))


@opds.route(URL["seqidx"] + "<sub1>/<sub2>", methods=['GET'])
def opds_seq_sub2(sub1, sub2):
    """sequences <first letter>/<first three letters> view"""
    sub1 = validate_prefix(sub1)
    sub2 = validate_prefix(sub2)
    params = {
        "index": URL["seqidx"].replace("/opds/", "", 1) + f"{sub1}/{sub2}",
        "tag": "tag:sequences:" + sub2,
        "subtag": "tag:sequence:",
        "title": LANG["seq_root_subtitle"] + sub2,
        "subtitle": "'%s'",
        "simple_baseref": URL["seqidx"] + sub1 + "/" + sub2,
        "strong_baseref": URL["seq"],
        "self": URL["seqidx"] + sub1 + "/" + sub2,
        "start": URL["start"],
        "up": URL["seqidx"] + sub1
    }
    return create_opds_response(opds_simple_list(params))


@opds.route(URL["seq"] + "<sub1>/<sub2>/<id>", methods=['GET'])
def opds_sequence(sub1, sub2, id):
    """books in sequences"""
    sub1 = validate_id(sub1)
    sub2 = validate_id(sub2)
    id = validate_id(id)
    params = {
        "index": URL["seq"].replace("/opds/", "", 1) + f"{sub1}/{sub2}/{id}",
        "id": id,
        "sub1": sub1,
        "sub2": sub2,
        "tag": "tag:seq:" + id,
        "subtag": "tag:sequence:" + id,
        "title": LANG["seq_tpl"],
        "layout": "sequence",
        "simple_baseref": URL["seqidx"] + sub1 + "/" + sub2,
        "strong_baseref": URL["seq"],
        "authref": URL["author"],
        "seqref": URL["seq"],
        "self": URL["seq"] + id2path(id),
        "start": URL["start"],
        "up": URL["seqidx"]
    }
    return create_opds_response(opds_book_list(params))


@opds.route(URL["genidx"], methods=['GET'])
def opds_genres_root():
    """genres root (genres groups list)"""
    params = {
        "index": URL["genidx"].replace("/opds/", "", 1),
        "tag": "tag:root:genres",
        "subtag": "tag:genresindex:",
        "title": LANG["genres_meta"],
        "subtitle": "%s",
        "layout": "key_value",
        "simple_baseref": URL["genidx"],
        "strong_baseref": URL["genidx"],
        "self": URL["genidx"],
        "start": URL["start"],
        "up": URL["start"]
    }
    return create_opds_response(opds_simple_list(params))


@opds.route(URL["genidx"] + "<meta_id>", methods=['GET'])
def opds_genres_list(meta_id):
    """genres list in group"""
    meta_id = validate_id(meta_id)
    meta_name = get_meta_name(meta_id)
    params = {
        "index": URL["genidx"].replace("/opds/", "", 1) + meta_id,
        "tag": "tag:root:genres",
        "subtag": "tag:genres:",
        "title": LANG["genres_root_subtitle"] + meta_name,
        "subtitle": "%s",
        "layout": "key_value",
        "simple_baseref": URL["genidx"],
        "strong_baseref": URL["genre"],
        "self": URL["genidx"],
        "start": URL["start"],
        "up": URL["start"]
    }
    return create_opds_response(opds_simple_list(params))


@opds.route(URL["genre"] + "<gen_id>", methods=['GET'])
@opds.route(URL["genre"] + "<gen_id>/<int:page>", methods=['GET'])
def opds_genre_books(gen_id, page=0):
    """paginated book list in genre"""
    id = validate_genre(gen_id)
    gen_name = get_genre_name(id)
    params = {
        "index": URL["genre"].replace("/opds/", "", 1) + id,
        "id": gen_id,
        "tag": "tag:genre:" + id,
        "subtag": "tag:genre:" + id,
        "title": LANG["genre_tpl"] % gen_name,
        "layout": "paginated",
        "page": page,
        "simple_baseref": URL["genidx"],
        "strong_baseref": URL["genre"],
        "authref": URL["author"],
        "seqref": URL["seq"],
        "self": URL["genre"] + id,
        "start": URL["start"],
        "up": URL["genidx"]
    }
    return create_opds_response(opds_book_list(params))


@opds.route(URL["time"], methods=['GET'])
@opds.route(URL["time"] + "/<int:page>", methods=['GET'])
def opds_time_books(page=0):
    """all books in library sort by date"""
    params = {
        "tag": "tag:time:" + str(page),
        "subtag": "tag:time:" + str(page),
        "title": LANG["title_time"],
        "layout": "time",
        "page": page,
        "simple_baseref": URL["time"],
        "strong_baseref": URL["time"],
        "authref": URL["author"],
        "seqref": URL["seq"],
        "next": URL["time"] + f"/{page+1}",
        "self": URL["time"],
        "start": URL["start"],
        "up": URL["start"]
    }
    return create_opds_response(opds_books_db(params))


@opds.route(URL["rndbook"], methods=['GET'])
def opds_rnd_books():
    """random books list"""
    params = {
        "tag": "tag:search:books:random",
        "title": LANG["rnd_books"],
        "layout": "rnd_books",
        # "simple_baseref": URL["rndbook"],
        # "strong_baseref": URL["rndbook"],
        "authref": URL["author"],
        "seqref": URL["seq"],
        "self": URL["rndbook"],
        "start": URL["start"],
        "up": URL["start"]
    }
    return create_opds_response(opds_books_db(params), cache_time=CONFIG["CACHE_TIME_RND"])


@opds.route(URL["rndgenidx"], methods=['GET'])
def opds_rnd_genres_root():
    """genres root (genres groups list) for random books"""
    params = {
        "index": URL["genidx"].replace("/opds/", "", 1),
        "tag": "tag:rnd:genres",
        "subtag": "tag:rnd:genres:",
        "title": LANG["genres_meta"],
        "subtitle": "%s",
        "layout": "key_value",
        "simple_baseref": URL["rndgenidx"],
        "strong_baseref": URL["rndgenidx"],
        "self": URL["rndgenidx"],
        "start": URL["start"],
        "up": URL["start"]
    }
    return create_opds_response(opds_simple_list(params), cache_time=CONFIG["CACHE_TIME_RND"])


@opds.route(URL["rndgenidx"] + "<meta_id>", methods=['GET'])
def opds_rnd_genres_list(meta_id):
    """genres list in group for random books"""
    meta_id = validate_id(meta_id)
    meta_name = get_meta_name(meta_id)
    params = {
        "index": URL["genidx"].replace("/opds/", "", 1) + meta_id,
        "tag": "tag:rnd:genres:" + meta_id,
        "subtag": "tag:rnd:genre:",
        "title": LANG["genres_root_subtitle"] + str(meta_name),
        "subtitle": "%s",
        "layout": "key_value",
        "simple_baseref": URL["rndgenidx"],
        "strong_baseref": URL["rndgen"],
        "self": URL["rndgenidx"] + meta_id,
        "start": URL["start"],
        "up": URL["rndgenidx"]
    }
    return create_opds_response(opds_simple_list(params), cache_time=CONFIG["CACHE_TIME_RND"])


@opds.route(URL["rndgen"] + "<gen_id>", methods=['GET'])
def opds_rnd_books_genre(gen_id):
    """random books list in genre"""
    gen_id = validate_genre(gen_id)
    gen_name = get_genre_name(gen_id)
    params = {
        "tag": "tag:rnd:genre:" + gen_id,
        "title": LANG["rnd_genre_books"] % gen_name,
        "layout": "rnd_books_genre",
        "gen_id": gen_id,
        "authref": URL["author"],
        "seqref": URL["seq"],
        "self": URL["rndgen"] + gen_id,
        "start": URL["start"],
        "up": URL["rndgenidx"]
    }
    return create_opds_response(opds_books_db(params), cache_time=CONFIG["CACHE_TIME_RND"])


@opds.route(URL["rndseq"], methods=['GET'])
def opds_rnd_seqs():
    """random sequences list"""
    params = {
        "tag": "tag:search:sequences:random:",
        "subtag": "tag:search:sequence:random:",
        "title": LANG["rnd_seqs"],
        "subtitle": "'%s'",
        "layout": "rnd_seqs",
        "baseref": URL["seq"],
        "self": URL["rndseq"],
        "start": URL["start"],
        "up": URL["start"]
    }
    return create_opds_response(opds_simple_list_db(params), cache_time=CONFIG["CACHE_TIME_RND"])


@opds.route(URL["search"], methods=['GET'])
def opds_search():
    """search root page"""
    s_term = request.args.get('searchTerm')
    s_term = validate_search(s_term)
    params = {
        "search_term": s_term,
        "self": URL["search"] + f"?searchTerm={s_term}",
        "start": URL["start"],
        "up": URL["start"],
        "tag": "tag:search:",
        "title": LANG["search_main"] % s_term
    }
    return create_opds_response(opds_search_main(params))


@opds.route(URL["srchauth"], methods=['GET'])
def opds_search_author():
    """search in author names"""
    s_term = request.args.get('searchTerm')
    s_term = validate_search(s_term)
    s_term_q = urllib.parse.quote(s_term)
    params = {
        "search_term": s_term,
        "self": URL["srchauth"] + f"?searchTerm={s_term_q}",
        "start": URL["start"],
        "up": URL["search"] + f"?searchTerm={s_term_q}",
        "tag": "tag:search:authors:",
        "subtag": "tag:author:",
        "baseref": URL["author"],
        "layout": "search_author",
        "title": LANG["search_author"] % s_term,
        "subtitle": "'%s'"
    }
    return create_opds_response(opds_simple_list_db(params))


@opds.route(URL["srchseq"], methods=['GET'])
def opds_search_seq():
    """search in sequence names"""
    s_term = request.args.get('searchTerm')
    s_term = validate_search(s_term)
    s_term_q = urllib.parse.quote(s_term)
    params = {
        "search_term": s_term,
        "self": URL["srchseq"] + f"?searchTerm={s_term_q}",
        "start": URL["start"],
        "up": URL["search"] + f"?searchTerm={s_term_q}",
        "tag": "tag:search:sequences:",
        "subtag": "tag:sequence:",
        "baseref": URL["seq"],
        "layout": "search_seq",
        "title": LANG["search_seq"] % s_term,
        "subtitle": "'%s'"
    }
    return create_opds_response(opds_simple_list_db(params))


@opds.route(URL["srchbook"], methods=['GET'])
def opds_search_books(page=0):
    """search in book titles"""
    s_term = request.args.get('searchTerm')
    s_term = validate_search(s_term)
    s_term_q = urllib.parse.quote(s_term)
    params = {
        "search_term": s_term,
        "tag": "tag:search:books:",
        "subtag": "tag:book:",
        "title": LANG["search_book"] % s_term,
        "layout": "search_book",
        "page": page,
        "authref": URL["author"],
        "seqref": URL["seq"],
        "self": URL["srchbook"] + f"?searchTerm={s_term_q}",
        "start": URL["start"],
        "up": URL["search"] + f"?searchTerm={s_term_q}"
    }
    return create_opds_response(opds_books_db(params))


@opds.route(URL["srchbookanno"], methods=['GET'])
def opds_search_booksanno(page=0):
    """search in book annotations"""
    s_term = request.args.get('searchTerm')
    s_term = validate_search(s_term)
    s_term_q = urllib.parse.quote(s_term)
    params = {
        "search_term": s_term,
        "tag": "tag:search:books:",
        "subtag": "tag:book:",
        "title": LANG["search_anno"] % s_term,
        "layout": "search_anno",
        "page": page,
        "authref": URL["author"],
        "seqref": URL["seq"],
        "self": URL["srchbookanno"] + f"?searchTerm={s_term_q}",
        "start": URL["start"],
        "up": URL["search"] + f"?searchTerm={s_term_q}"
    }
    return create_opds_response(opds_books_db(params))


@opds.route(URL["srchbookannovector"], methods=['GET'])
def opds_search_booksannovector(page=0):
    """search in book annotations by vector"""
    s_term = request.args.get('searchTerm')
    s_term = validate_search(s_term)
    s_term_q = urllib.parse.quote(s_term)
    params = {
        "search_term": s_term,
        "tag": "tag:search:booksvector:",
        "subtag": "tag:book:",
        "title": LANG["search_anno_vector"] % s_term,
        "layout": "search_anno_vector",
        "page": page,
        "authref": URL["author"],
        "seqref": URL["seq"],
        "self": URL["srchbookannovector"] + f"?searchTerm={s_term_q}",
        "start": URL["start"],
        "up": URL["search"] + f"?searchTerm={s_term_q}"
    }
    return create_opds_response(opds_books_db(params))
