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
from .config import CONFIG, URL, LANG
from .strings import id2path
from .validate import (
    validate_prefix,
    validate_id
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
