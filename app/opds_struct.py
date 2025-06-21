# -*- coding: utf-8 -*-
"""opds data structures and functions"""

import datetime

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

    feed = {
        "@xmlns": "http://www.w3.org/2005/Atom",
        "@xmlns:dc": "http://purl.org/dc/terms/",
        "@xmlns:os": "http://a9.com/-/spec/opensearch/1.1/",
        "@xmlns:opds": "http://opds-spec.org/2010/catalog",
        "id": "tag:root",
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
