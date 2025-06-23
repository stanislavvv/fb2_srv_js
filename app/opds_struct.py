# -*- coding: utf-8 -*-
"""opds data structures and functions for static files data"""

import datetime
import os
import json
import logging
import urllib

from functools import cmp_to_key

from .data import (
    custom_alphabet_cmp,
    custom_alphabet_book_title_cmp,
    url_str,
    html_refine,
    get_genre_name,
    sizeof_fmt
)
from .validate import safe_path
from .strings import id2path, unicode_upper
from .config import CONFIG, URL, LANG


def get_dtiso():
    """return current time in iso"""
    return datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()


def pubinfo_anno(pubinfo):
    """create publication info for opds"""
    # pylint: disable=C0209
    ret = ""
    if pubinfo["isbn"] is not None and pubinfo["isbn"] != 'None':
        ret = ret + LANG["pubinfo_isbn"] % pubinfo["isbn"]
    if pubinfo["year"] is not None and pubinfo["year"] != 'None':
        ret = ret + LANG["pubinfo_isbn"] % pubinfo["year"]
    if pubinfo["publisher"] is not None and pubinfo["year"] != 'None':
        ret = ret + LANG["pubinfo_publisher"] % pubinfo["publisher"]
    return ret


def get_seq_link(approot: str, seqref: str, seq_id: str, seq_name: str):
    """create sequence link for opds"""
    ret = {
        "@href": approot + seqref + seq_id,
        "@rel": "related",
        "@title": LANG["seq_tpl"] % seq_name,
        "@type": "application/atom+xml"
    }
    return ret


def get_book_link(approot: str, zipfile: str, filename: str, ctype: str):
    """create download/read link for opds"""
    title = LANG["book_read"]
    book_ctype = "text/html"
    rel = "alternate"
    if zipfile.endswith('zip'):
        zipfile = zipfile[:-4]
    href = approot + URL["read"] + zipfile + "/" + url_str(filename)
    if ctype == 'dl':
        title = LANG["book_dl"]
        book_ctype = "application/fb2+zip"
        rel = "http://opds-spec.org/acquisition/open-access"
        href = approot + URL["dl"] + zipfile + "/" + url_str(filename) + ".zip"
    ret = {
        "@href": href,
        "@rel": rel,
        "@title": title,
        "@type": book_ctype
    }
    return ret


def make_book_entry(book, ts, authref, seqref, seq_id=None):
    """create book entry for xml
    params:
        book -- book structure (see "Json book object" in SPEC_lists.md)
        ts -- timestamp in get_dtiso() format (compartibility)
        authref -- URL["author"] from config.py or another url for author's id2path(id) struct
        seqref -- URL["seq"] from config.py or another
        seq_id -- if exists -- entry for this sequence book list
    """
    approot = CONFIG['APPLICATION_ROOT']
    book_title = book["book_title"]
    book_id = book["book_id"]
    lang = book["lang"]
    annotation = html_refine(book["annotation"])
    size = int(book["size"])
    date_time = book["date_time"]
    zipfile = book["zipfile"]
    filename = book["filename"]
    genres = book["genres"]
    pubinfo = ""
    if "pub_info" in book and book["pub_info"] is not None:
        pubinfo = pubinfo_anno(book["pub_info"])
    authors = []
    links = []
    category = []
    seq_name = ""
    seq_num = ""
    for author in book["authors"]:
        authors.append(
            {
                "uri": approot + authref + id2path(author["id"]),
                "name": author["name"]
            }
        )
        links.append(
            {
                "@href": approot + authref + id2path(author["id"]),
                "@rel": "related",
                "@title": author["name"],
                "@type": "application/atom+xml"
            }
        )
    for gen in genres:
        category.append(
            {
                "@label": get_genre_name(gen),
                "@term": gen
            }
        )
    if book["sequences"] is not None and book["sequences"] != '-':
        for seq in book["sequences"]:
            s_id = seq.get("id")
            if s_id is not None:
                links.append(get_seq_link(approot, seqref, id2path(s_id), seq["name"]))
                if seq_id is not None and seq_id == s_id:
                    seq_name = seq["name"]
                    seq_num = seq.get("num")
                    if seq_num is None:
                        seq_num = "0"
    links.append(get_book_link(approot, zipfile, filename, 'dl'))
    links.append(get_book_link(approot, zipfile, filename, 'read'))

    # book cover
    for rel in (
        "http://opds-spec.org/image",
        "x-stanza-cover-image",
        "http://opds-spec.org/thumbnail",
        "x-stanza-cover-image-thumbnail"
    ):
        links.append({
            "@href": approot + URL["cover"] + id2path(book_id) + ".jpg",
            "@rel": rel,
            "@type": "image/jpeg"
        })

    if seq_id is not None and seq_id != '':
        annotext = LANG["bookinfo_seq"] % (annotation, sizeof_fmt(size), seq_name, seq_num)
    else:
        annotext = LANG["bookinfo"] % (annotation, sizeof_fmt(size))
    annotext = annotext + pubinfo
    ret = {
        "updated": date_time,
        "id": "tag:book:" + book_id,
        "title": book_title,
        "author": authors,
        "link": links,
        "category": category,
        "dc:language": lang,
        "dc:format": "fb2",
        "content": {
            "@type": "text/html",
            "#text": annotext
        }
    }
    return ret


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
            "title": LANG["title_time"],
            "content": {
              "@type": "text",
              "#text": LANG["title_time"]
            },
            "link": {
              "@href": approot + URL["time"],
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          },
          {
            "updated": ts,
            "id": "tag:root:authors",
            "title": LANG["title_authors"],
            "content": {
              "@type": "text",
              "#text": LANG["title_authors"]
            },
            "link": {
              "@href": approot + URL["authidx"],
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          },
          {
            "updated": ts,
            "id": "tag:root:sequences",
            "title": LANG["title_sequences"],
            "content": {
              "@type": "text",
              "#text": LANG["title_sequences"]
            },
            "link": {
              "@href": approot + URL["seqidx"],
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          },
          {
            "updated": ts,
            "id": "tag:root:genre",
            "title": LANG["title_genres"],
            "content": {
              "@type": "text",
              "#text": LANG["title_genres"]
            },
            "link": {
              "@href": approot + URL["genidx"],
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          },
          {
            "updated": ts,
            "id": "tag:root:random:books",
            "title": LANG["title_rnd_books"],
            "content": {
              "@type": "text",
              "#text": LANG["title_rnd_books"]
            },
            "link": {
              "@href": approot + URL["rndbook"],
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          },
          {
            "updated": ts,
            "id": "tag:root:random:sequences",
            "title": LANG["title_rnd_seqs"],
            "content": {
              "@type": "text",
              "#text": LANG["title_rnd_seqs"]
            },
            "link": {
              "@href": approot + URL["rndseq"],
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          },
          {
            "updated": ts,
            "id": "tag:root:random:genres",
            "title": LANG["title_rnd_genre"],
            "content": {
              "@type": "text",
              "#text": LANG["title_rnd_genre"]
            },
            "link": {
              "@href": approot + URL["rndgenidx"],
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          }
        ]
    return ret


def opds_simple_list(params):
    """simple urls list
        params["index"] -- for example: 'authorsindex/', 'authorsindex/A', 'authorindex/ABC'
    """
    approot = CONFIG["APPLICATION_ROOT"]
    pagesdir = CONFIG["PAGES"]
    ts = get_dtiso()
    params["ts"] = ts

    index_info = params['index']
    simple_baseref = params['simple_baseref']  # simple lists
    strong_baseref = params['strong_baseref']  # authors lists or books lists
    subtag = params["subtag"]  # common part of tags in links
    subtitle = params["subtitle"]  # for text part of links

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
        with open(indexfile, encoding="utf-8") as idx:
            index = json.load(idx)
    except Exception as ex:
        logging.error(f"error in index: {index_info}, exception: {ex}")
        return None

    data = []
    if "layout" in params:
        if params["layout"] == "name_id_list":  # array of {name: ..., id, ...}
            idx_data = {}
            for i in index:
                name = i["name"]
                i_id = i["id"]
                idx_data[i_id] = name
            for k, v in sorted(idx_data.items(), key=lambda item: item[1]):  # pylint: disable=W0612
                data.append(k)
        if params["layout"] == "key_value":
            idx_data = {}
            for k, v in sorted(index.items(), key=lambda item: item[1]):  # pylint: disable=W0612
                idx_data[k] = v
                data.append(k)
    elif simple_links:  # id: name dict
        data = sorted(index.keys(), key=cmp_to_key(custom_alphabet_cmp))
    else:  # key_value by default in not simple_links
        for k, v in sorted(index.items(), key=lambda item: item[1]):  # pylint: disable=W0612
            data.append(k)

    ret = opds_header(params)

    for k in data:
        if "layout" in params:
            if params["layout"] in ("name_id_list", "key_value"):
                title = idx_data[k]
                baseref = strong_baseref
                href = approot + baseref + urllib.parse.quote(k)
        elif simple_links:
            title = k
            baseref = simple_baseref
            href = approot + baseref + urllib.parse.quote(k)
        else:
            title = index[k]
            baseref = strong_baseref
            href = approot + baseref + urllib.parse.quote(id2path(k))
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
                    "@href": href,
                    "@type": "application/atom+xml;profile=opds-catalog"
                }
            }
        )
    return ret


def opds_author_page(params):
    """main page of author"""
    ts = get_dtiso()
    params["ts"] = ts
    approot = CONFIG["APPLICATION_ROOT"]
    pagesdir = CONFIG["PAGES"]

    sub1 = params["sub1"]
    sub2 = params["sub2"]
    auth_id = params["id"]
    index = params["index"]
    subtag = params["subtag"]

    indexfile = pagesdir + "/" + f"{index}/index.json"
    if not os.path.isfile(indexfile):
        return None
    try:
        with open(indexfile, encoding="utf-8") as idx:
            auth_data = json.load(idx)
    except Exception as ex:
        logging.error(f"Error on author {sub1}/{sub2}/{id}, exception: {ex}")
        return None
    auth_name = auth_data["name"]
    params["title"] = params["title"] % auth_name

    ret = opds_header(params)
    ret["feed"]["entry"] = [
        {
            "updated": ts,
            "id": "tag:author:bio:" + auth_id,
            "title": "Об авторе",
            "link": [
                {
                    "@href": approot + URL["author"] + id2path(auth_id) + "/sequences",
                    "@rel": "http://www.feedbooks.com/opds/facet",
                    "@title": LANG["books_seq"],
                    "@type": "application/atom+xml;profile=opds-catalog"
                },
                {
                    "@href": approot + URL["author"] + id2path(auth_id) + "/sequenceless",
                    "@rel": "http://www.feedbooks.com/opds/facet",
                    "@title": LANG["books_nonseq"],
                    "@type": "application/atom+xml;profile=opds-catalog"
                }
            ],
            "content": {
                "@type": "text/html",
                "#text": "<p><span style=\"font-weight:bold\">" + auth_name + "</span></p>"
            }
        },
        {
            "updated": ts,
            "id": subtag + ":sequences",
            "title": LANG["books_seq"],
            "link": {
                "@href": approot + URL["author"] + id2path(auth_id) + "/sequences",
                "@type": "application/atom+xml;profile=opds-catalog"
            }
        },
        {
            "updated": ts,
            "id": subtag + ":sequenceless",
            "title": LANG["books_nonseq"],
            "link": {
                "@href": approot + URL["author"] + id2path(auth_id) + "/sequenceless",
                "@type": "application/atom+xml;profile=opds-catalog"
            }
        },
        {
            "updated": ts,
            "id": subtag + ":alphabet",
            "title": LANG["books_alphabet"],
            "link": {
                "@href": approot + URL["author"] + id2path(auth_id) + "/alphabet",
                "@type": "application/atom+xml;profile=opds-catalog"
            }
        },
        {
            "updated": ts,
            "id": subtag + ":time",
            "title": LANG["books_time"],
            "link": {
                "@href": approot + URL["author"] + id2path(auth_id) + "/time",
                "@type": "application/atom+xml;profile=opds-catalog"
            }
        }
    ]
    return ret


def opds_book_list(params):
    """return list of books, only for data in json"""
    ts = get_dtiso()
    params["ts"] = ts
    # approot = CONFIG["APPLICATION_ROOT"]
    pagesdir = CONFIG["PAGES"]

    index = params["index"]
    title = params["title"]
    # subtitle = params["subtitle"]
    authref = params["authref"]
    seqref = params["seqref"]

    layout = params["layout"]
    if layout == "paginated":
        page = params["page"]

    if layout in ("author_seq", "author_alpha", "author_time", "author_nonseq"):
        auth_name = ""
        try:
            with open(pagesdir + "/" + index + "index.json", encoding="utf-8") as nm:
                auth_name = json.load(nm)["name"]
        except Exception as ex:
            logging.error(f"Can't read author data for {index}/index.json, exception: {ex}")
        booksidx = index + "/all.json"
    if layout == "author_seq":
        seq_name = ""
        try:
            seq_id = params["seq_id"]
            with open(pagesdir + "/" + index + "sequences.json", encoding="utf-8") as seqs:
                seq_data = json.load(seqs)
            for s in seq_data:
                if s["id"] == seq_id:
                    seq_name = s["name"]
                    break
        except Exception as ex:
            logging.error(f"Can't read sequences data for {index}/sequences.json, exception: {ex}")
            return None
        params["title"] = title % (seq_name, auth_name)
    elif layout in ("author_alpha", "author_nonseq", "author_time"):
        booksidx = index + "/all.json"
        params["title"] = title % auth_name
    elif layout == "sequence":
        booksidx = index + ".json"
    elif layout == "paginated":
        booksidx = index + f"/{page}.json"
        params["next"] = params["self"] + "/" + str(page + 1)
        if page == 1:
            params["prev"] = params["self"]
        elif page > 1:
            params["prev"] = params["self"] + "/" + str(page - 1)
        print(booksidx)

    try:
        with open(pagesdir + "/" + booksidx, encoding="utf-8") as b:
            data = json.load(b)
    except Exception as ex:
        logging.error(f"Can't read books list from {booksidx}, exception: {ex}")
        return None

    if layout == "sequence":
        params["title"] = title % data["name"]

    ret = opds_header(params)
    if layout == "author_seq":
        data = sorted(data, key=cmp_to_key(custom_alphabet_book_title_cmp))  # presort unnumbered books
        data_seq = []

        for book in data:
            if book["sequences"] is not None and seq_name is not None:
                for s in book["sequences"]:
                    seq_num = 0
                    if s.get("id") == seq_id:
                        snum = s.get("num")
                        if snum is not None:
                            seq_num = int(snum)
                        book["seq_num"] = seq_num
                        data_seq.append(book)
        data = sorted(data_seq, key=lambda s: s["seq_num"] or -1)
    elif layout == "author_nonseq":
        data_nonseq = []
        for book in data:
            if book["sequences"] is None:
                data_nonseq.append(book)
        data = sorted(data_nonseq, key=cmp_to_key(custom_alphabet_book_title_cmp))
    elif layout == "author_time":
        data = sorted(data, key=lambda s: unicode_upper(s["date_time"]))
    elif layout == "sequence":
        seq_id = data["id"]
        data = sorted(data["books"], key=cmp_to_key(custom_alphabet_book_title_cmp))

    for book in data:
        if layout in ("sequence", "author_seq"):
            ret["feed"]["entry"].append(make_book_entry(book, ts, authref, seqref, seq_id=seq_id))
        else:
            ret["feed"]["entry"].append(make_book_entry(book, ts, authref, seqref))
    return ret


def opds_search_main(params):
    """near-static output for main search page"""
    s_term = params["search_term"]
    approot = CONFIG["APPLICATION_ROOT"]
    ts = get_dtiso()

    params["ts"] = ts
    # params["tag"] = "tag:root"
    tag = params["tag"]
    # params["title"] = CONFIG["TITLE"]
    params["start"] = URL["start"]
    params["self"] = URL["start"]

    ret = opds_header(params)
    if s_term is None:
        ret["feed"]["id"] = tag
    else:
        ret["feed"]["id"] = tag + urllib.parse.quote_plus(s_term)
        ret["feed"]["entry"].append(
          {
            "updated": ts,
            "id": "tag:search:authors:",
            "title": LANG["schmain_author"],
            "content": {
              "@type": "text",
              "#text": LANG["schmain_author"]
            },
            "link": {
              "@href": approot + URL["srchauth"] + "?searchTerm=%s" % url_str(s_term),
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          }
        )
        ret["feed"]["entry"].append(
          {
            "updated": ts,
            "id": "tag:search:sequences:",
            "title": LANG["schmain_seq"],
            "content": {
              "@type": "text",
              "#text": LANG["schmain_seq"]
            },
            "link": {
              "@href": approot + URL["srchseq"] + "?searchTerm=%s" % url_str(s_term),
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          }
        )
        ret["feed"]["entry"].append(
          {
            "updated": ts,
            "id": "tag:search:booktitles:",
            "title": LANG["schmain_book"],
            "content": {
              "@type": "text",
              "#text": LANG["schmain_book"]
            },
            "link": {
              "@href": approot + URL["srchbook"] + "?searchTerm=%s" % url_str(s_term),
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          }
        )
        ret["feed"]["entry"].append(
          {
            "updated": ts,
            "id": "tag:search:bookanno:",
            "title": LANG["schmain_anno"],
            "content": {
              "@type": "text",
              "#text": LANG["schmain_anno"]
            },
            "link": {
              "@href": approot + URL["srchbookanno"] + "?searchTerm=%s" % url_str(s_term),
              "@type": "application/atom+xml;profile=opds-catalog"
            }
          }
        )
    return ret
