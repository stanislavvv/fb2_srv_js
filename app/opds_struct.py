# -*- coding: utf-8 -*-
"""opds data structures and functions"""

import datetime
import os
import json
import logging
import urllib

from functools import cmp_to_key

from .data import custom_alphabet_cmp
from .validate import safe_path
from .strings import id2path
from .config import CONFIG, URL


def get_dtiso():
    """return current time in iso"""
    return datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()


def opds_header(params):
    """return opds header struct, ready for entries append"""
    approot = CONFIG["APPLICATION_ROOT"]

    title = params["title"]
    ts = params["ts"]
    startlink = params["start"]
    selflink = params["self"]
    tag = params["tag"]

    feed = {
        "@xmlns": "http://www.w3.org/2005/Atom",
        "@xmlns:dc": "http://purl.org/dc/terms/",
        "@xmlns:os": "http://a9.com/-/spec/opensearch/1.1/",
        "@xmlns:opds": "http://opds-spec.org/2010/catalog",
        "id": tag,
        "title": title,
        "updated": ts,
        "icon": approot + CONFIG["APP_ICO"],
        "link": [
          {
            "@href": approot + URL["search"] + "?searchTerm={searchTerms}",
            "@rel": "search",
            "@type": "application/atom+xml"
          },
          {
            "@href": approot + startlink,
            "@rel": "start",
            "@type": "application/atom+xml;profile=opds-catalog"
          },
          {
            "@href": approot + selflink,
            "@rel": "self",
            "@type": "application/atom+xml;profile=opds-catalog"
          }
        ],
        "entry": []
    }

    if "up" in params:
        up_link = params["up"]
        feed["link"].append(
            {
                "@href": approot + up_link,
                "@rel": "up",
                "@type": "application/atom+xml;profile=opds-catalog"
            }
        )
    if "next" in params:
        next_link = params["next"]
        feed["link"].append(
            {
                "@href": approot + next_link,
                "@rel": "next",
                "@type": "application/atom+xml;profile=opds-catalog"
            }
        )
    if "prev" in params:
        prev_link = params["prev"]
        feed["link"].append(
            {
                "@href": approot + prev_link,
                "@rel": "prev",
                "@type": "application/atom+xml;profile=opds-catalog"
            }
        )
    return {"feed": feed}


def opds_main(params={}):
    """library main entry page"""
    approot = CONFIG["APPLICATION_ROOT"]
    ts = get_dtiso()

    params["ts"] = ts
    params["tag"] = "tag:root"
    params["title"] = CONFIG["TITLE"]
    params["start"] = URL["start"]
    params["self"] = URL["start"]

    ret = opds_header(params)
    ret["feed"]["entry"] = [
          {
            "updated": ts,
            "id": "tag:root:time",
            "title": "По дате поступления",
            "content": {
              "@type": "text",
              "#text": "По дате поступления"
            },
            "link": {
              "@href": approot + URL["time"],
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          },
          {
            "updated": ts,
            "id": "tag:root:authors",
            "title": "По авторам",
            "content": {
              "@type": "text",
              "#text": "По авторам"
            },
            "link": {
              "@href": approot + URL["authidx"],
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          },
          {
            "updated": ts,
            "id": "tag:root:sequences",
            "title": "По сериям",
            "content": {
              "@type": "text",
              "#text": "По сериям"
            },
            "link": {
              "@href": approot + URL["seqidx"],
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          },
          {
            "updated": ts,
            "id": "tag:root:genre",
            "title": "По жанрам",
            "content": {
              "@type": "text",
              "#text": "По жанрам"
            },
            "link": {
              "@href": approot + URL["genidx"],
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          },
          {
            "updated": ts,
            "id": "tag:root:random:books",
            "title": "Случайные книги",
            "content": {
              "@type": "text",
              "#text": "Случайные книги"
            },
            "link": {
              "@href": approot + URL["rndbook"],
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          },
          {
            "updated": ts,
            "id": "tag:root:random:sequences",
            "title": "Случайные серии",
            "content": {
              "@type": "text",
              "#text": "Случайные серии"
            },
            "link": {
              "@href": approot + URL["rndseq"],
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          },
          {
            "updated": ts,
            "id": "tag:root:random:genres",
            "title": "Случайные книги в жанре",
            "content": {
              "@type": "text",
              "#text": "Случайные книги в жанре"
            },
            "link": {
              "@href": approot + URL["rndgenidx"],
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          }
        ]
    return ret


def opds_simple_list(params):
    """asimple urls list
        params["index"] -- for example: 'authorsindex/', 'authorsindex/A', 'authorindex/ABC'
    """
    approot = CONFIG["APPLICATION_ROOT"]
    ts = get_dtiso()
    params["ts"] = ts

    pagesdir = CONFIG["PAGES"]
    index_info = params['index']
    simple_baseref = params['simple_baseref']  # simple lists
    strong_baseref = params['strong_baseref']  # authors lists or books lists
    subtag = params["subtag"]  # common part of tags in links
    subtitle = params["subtitle"]  # for text part of links

    print(params)

    simple_links = False  # links not to simple lists
    if os.path.isfile(pagesdir + "/" + safe_path(index_info + "/index.json")):
        indexfile = pagesdir + "/" + safe_path(index_info + "/index.json")
        simple_links = True
    elif os.path.isfile(pagesdir + "/" + safe_path(index_info + ".json")):
        indexfile = pagesdir + "/" + safe_path(index_info + ".json")
    else:
        return None

    index = {}
    try:
        with open(indexfile) as idx:
            index = json.load(idx)
    except Exception as ex:
        logging.error(f"error in index: {index_info}, exception: {ex}")
        return None

    data = []
    if simple_links:
        data = sorted(index.keys(), key=cmp_to_key(custom_alphabet_cmp))
    else:
        for k, v in sorted(index.items(), key=lambda item: item[1]):  # pylint: disable=W0612
            data.append(k)

    ret = opds_header(params)

    for k in data:
        if simple_links:
            title = k
            baseref = simple_baseref
        else:
            title = index[k]
            baseref = strong_baseref
        ret["feed"]["entry"].append(
            {
                "updated": ts,
                "id": subtag + urllib.parse.quote(k),
                "title": title,
                "content": {
                    "@type": "text",
                    "#text": subtitle + "'" + title + "'"
                },
                "link": {
                    "@href": approot + baseref + urllib.parse.quote(id2path(k)),
                    "@type": "application/atom+xml;profile=opds-catalog"
                }
            }
        )
    return ret
