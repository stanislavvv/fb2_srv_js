# -*- coding: utf-8 -*-
"""opds responses"""

import xmltodict
import logging

from flask import Blueprint, Response

from .opds_struct import opds_main
from .config import CONFIG, URL

opds = Blueprint("opds", __name__)


def create_opds_response(data, cache_time=CONFIG["CACHE_TIME"]):
    """data to xml to flask response"""
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
