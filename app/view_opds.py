# -*- coding: utf-8 -*-
"""opds responses"""

import xmltodict
import logging

from flask import Blueprint, Response

from .opds_struct import (
    opds_main,
    opds_simple_list,
    opds_author_page,
    opds_book_list
)
from .opds_db import opds_books_db, opds_simple_list_db
from .config import CONFIG, URL, LANG
from .strings import id2path
from .data import get_meta_name, get_genre_name
from .validate import (
    validate_prefix,
    validate_id,
    validate_genre
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


@opds.route(URL["start"], methods=['GET'])
def opds_root():
    """root"""
    return create_opds_response(opds_main())


@opds.route(URL["authidx"], methods=['GET'])
def opds_auth_root():
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
    sub = validate_prefix(sub)
    params = {
        "index": URL["authidx"].replace("/opds/", "", 1) + sub,
        "tag": "tag:authors:" + sub,
        "subtag": "tag:authors:",
        "title": LANG["auth_root_subtitle"] + sub,
        "subtitle": LANG["auth_root_subtitle"],
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
    sub1 = validate_prefix(sub1)
    sub2 = validate_prefix(sub2)
    params = {
        "index": URL["authidx"].replace("/opds/", "", 1) + f"{sub1}/{sub2}",
        "tag": "tag:authors:" + sub2,
        "subtag": "tag:author:",
        "title": LANG["auth_root_subtitle"] + sub2,
        "subtitle": "",
        "simple_baseref": URL["authidx"] + sub1 + "/" + sub2,
        "strong_baseref": URL["author"],
        "self": URL["authidx"] + sub1 + "/" + sub2,
        "start": URL["start"],
        "up": URL["authidx"] + sub1
    }
    return create_opds_response(opds_simple_list(params))


@opds.route(URL["author"] + "<sub1>/<sub2>/<id>", methods=['GET'])
def opds_author_main(sub1, sub2, id):
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
        # "subtitle": "",
        "simple_baseref": URL["authidx"] + sub1 + "/" + sub2,
        "strong_baseref": URL["author"],
        "self": URL["author"] + id2path(id),
        "start": URL["start"],
        "up": URL["authidx"]
    }
    return create_opds_response(opds_author_page(params))


@opds.route(URL["author"] + "<sub1>/<sub2>/<id>/sequences", methods=['GET'])
def opds_author_seqs(sub1, sub2, id):
    sub1 = validate_id(sub1)
    sub2 = validate_id(sub2)
    id = validate_id(id)
    params = {
        "index": URL["author"].replace("/opds/", "", 1) + f"{sub1}/{sub2}/{id}/sequences",
        "id": id,
        "sub1": sub1,
        "sub2": sub2,
        "tag": "tag:author:" + id,
        "subtag": "tag:author:" + id,
        "title": "Автор ",
        "subtitle": "",
        "layout": "name_id_list",
        "simple_baseref": URL["authidx"] + sub1 + "/" + sub2,
        "strong_baseref": URL["author"] + f"{sub1}/{sub2}/{id}",
        "self": URL["author"] + id2path(id) + "/sequences",
        "start": URL["start"],
        "up": URL["author"] + id2path(id)
    }
    return create_opds_response(opds_simple_list(params))


@opds.route(URL["author"] + "<sub1>/<sub2>/<id>/<seq_id>", methods=['GET'])
def opds_author_seq(sub1, sub2, id, seq_id):
    sub1 = validate_id(sub1)
    sub2 = validate_id(sub2)
    id = validate_id(id)
    seq_id = validate_id(seq_id)
    params = {
        "index": URL["author"].replace("/opds/", "", 1) + f"{sub1}/{sub2}/{id}/",
        "id": id,
        "sub1": sub1,
        "sub2": sub2,
        "tag": "tag:author:" + id,
        "subtag": "tag:author:" + id,
        "seq_id": seq_id,
        "title": LANG["books_author_seq"],
        # "subtitle": "",
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
        # "subtitle": "",
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
        # "subtitle": "",
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
        # "subtitle": "",
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
    sub = validate_prefix(sub)
    params = {
        "index": URL["seqidx"].replace("/opds/", "", 1) + sub,
        "tag": "tag:sequences:" + sub,
        "subtag": "tag:sequences:",
        "title": LANG["seq_root_subtitle"] + sub,
        "subtitle": LANG["seq_root_subtitle"],
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
    sub1 = validate_prefix(sub1)
    sub2 = validate_prefix(sub2)
    params = {
        "index": URL["seqidx"].replace("/opds/", "", 1) + f"{sub1}/{sub2}",
        "tag": "tag:sequences:" + sub2,
        "subtag": "tag:sequence:",
        "title": LANG["seq_root_subtitle"] + sub2,
        "subtitle": "",
        "simple_baseref": URL["seqidx"] + sub1 + "/" + sub2,
        "strong_baseref": URL["seq"],
        "self": URL["seqidx"] + sub1 + "/" + sub2,
        "start": URL["start"],
        "up": URL["seqidx"] + sub1
    }
    return create_opds_response(opds_simple_list(params))


@opds.route(URL["seq"] + "<sub1>/<sub2>/<id>", methods=['GET'])
def opds_sequence(sub1, sub2, id):
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
    params = {
        "index": URL["genidx"].replace("/opds/", "", 1),
        "tag": "tag:root:genres",
        "subtag": "tag:genres:",
        "title": LANG["genres_meta"],
        "subtitle": "",
        "layout": "key_value",
        "simple_baseref": URL["genidx"],
        "strong_baseref": URL["genre"],
        "self": URL["genidx"],
        "start": URL["start"],
        "up": URL["start"]
    }
    return create_opds_response(opds_simple_list(params))


@opds.route(URL["genidx"] + "<meta_id>", methods=['GET'])
def opds_genres_list(meta_id):
    meta_id = validate_id(meta_id)
    meta_name = get_meta_name(meta_id)
    params = {
        "index": URL["genidx"].replace("/opds/", "", 1) + meta_id,
        "tag": "tag:root:genres",
        "subtag": "tag:genres:",
        "title": LANG["genres_root_subtitle"] + meta_name,
        "subtitle": "",
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
    params = {
        "tag": "tag:time:" + str(page),
        "subtag": "tag:time:" + str(page),
        "title": LANG["title_time"],
        "layout": "paginated",
        "page": page,
        "simple_baseref": URL["time"],
        "strong_baseref": URL["time"],
        "authref": URL["author"],
        "seqref": URL["seq"],
        "self": URL["time"],
        "start": URL["start"],
        "up": URL["start"]
    }
    return create_opds_response(opds_books_db(params))


@opds.route(URL["rndbook"], methods=['GET'])
def opds_rnd_books():
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
    return create_opds_response(opds_books_db(params))


@opds.route(URL["rndgen"] + "<gen_id>", methods=['GET'])
def opds_rnd_books_genre(gen_id):
    gen_id = validate_genre(gen_id)
    params = {
        "tag": "tag:search:books:random",
        "title": LANG["rnd_books"],
        "layout": "rnd_books_genre",
        "gen_id": gen_id,
        # "simple_baseref": URL["rndbook"],
        # "strong_baseref": URL["rndbook"],
        "authref": URL["author"],
        "seqref": URL["seq"],
        "self": URL["rndbook"],
        "start": URL["start"],
        "up": URL["start"]
    }
    return create_opds_response(opds_books_db(params))


@opds.route(URL["rndseq"], methods=['GET'])
def opds_rnd_seqs():
    params = {
        "tag": "tag:search:sequences:random:",
        "subtag": "tag:search:sequence:random:",
        "title": LANG["rnd_seqs"],
        "subtitle": "",
        "layout": "rnd_seqs",
        "baseref": URL["seq"],
        "self": URL["rndseq"],
        "start": URL["start"],
        "up": URL["start"]
    }
    return create_opds_response(opds_simple_list_db(params))
