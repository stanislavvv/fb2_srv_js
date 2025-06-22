# -*- coding: utf-8 -*-
"""opds functions for data in database"""

import logging

from sqlalchemy.sql.expression import func

from .db_classes import Book, dbsession
from .db import (
    get_books_descr,
    get_authors,
    get_seqs
)
from .opds_struct import (
    get_dtiso,
    opds_header,
    make_book_entry
)
from .strings import unicode_upper
from .config import CONFIG


def opds_books_db(params):
    """get books from db"""
    ts = get_dtiso()
    params["ts"] = ts
    # approot = CONFIG["APPLICATION_ROOT"]

    authref = params["authref"]
    seqref = params["seqref"]

    layout = params["layout"]
    if "page" in params:
        page = params["page"]
    else:
        page = 0
    pagelimit = int(CONFIG["PAGE_SIZE"])

    ret = opds_header(params)
    try:
        session = dbsession()
        if layout == "rnd_books":
            books_data = session.query(Book).order_by(func.random()).limit(pagelimit).all()
        elif layout == "rnd_books_genre":
            gen_id = params["gen_id"]
            books_data = session.query(
                Book
            ).filter(
                Book.genres.any(gen_id)
            ).order_by(func.random()).limit(pagelimit).all()
        else:
            books_data = session.query(Book).order_by(Book.date.desc()).limit(pagelimit).offset(pagelimit * page).all()
        book_ids = []
        books = {}
        authorids = []
        seqids = []
        for b in books_data:
            book_id = b.book_id
            book_ids.append(book_id)
            book = {
                "zipfile": b.zipfile,
                "filename": b.filename,
                "genres": b.genres,
                "authors": b.authors,  # fixme
                "sequences": b.sequences,
                "book_id": b.book_id,
                "book_title": b.book_id,  # fixme
                "lang": b.lang,
                "date_time": str(b.date) + "_00:00",  # fixme to datetime as 2010-03-27_00:00
                "size": str(b.size),
                "annotation": b.book_id,
                "pubinfo": None,
                "deleted": b.deleted
            }
            books[book_id] = book
            for a in b.authors:
                authorids.append(a)
            for s in b.sequences:
                seqids.append(s)
        descr = get_books_descr(session, book_ids)
        authors = get_authors(session, authorids)
        sequences = get_seqs(session, seqids)
        for book_id in books:
            book = books[book_id]
            if book_id in descr:
                d = descr[book_id]
                book["book_title"] = d["book_title"]
                pubinfo = {
                    "isbn": d["pub_isbn"],
                    "year": d["pub_year"],
                    "publisher": d["publisher"],
                    "publisher_id": d["publisher_id"]
                }
                book["pub_info"] = pubinfo
                book["annotation"] = d["annotation"]
            auth_ids = book["authors"]
            book_authors = []
            for a in auth_ids:
                if a in authors:
                    book_authors.append(authors[a])
            book["authors"] = book_authors
            seq_ids = book["sequences"]
            book_seqs = []
            for s in seq_ids:
                if s in sequences:
                    book_seqs.append(sequences[s])
            book["sequences"] = book_seqs
            books[book_id] = book
        session.close()
    except Exception as ex:
        logging.error(f"Database error:{ex}")
        session.close()
        return None

    data = []
    for book_id in books:
        data.append(books[book_id])
    data = sorted(data, key=lambda s: unicode_upper(s["date_time"]))
    for book in data:
        ret["feed"]["entry"].append(make_book_entry(book, ts, authref, seqref))
    return ret
