# -*- coding: utf-8 -*-
"""database update"""

import logging
import glob
import json

from sqlalchemy.orm import sessionmaker

from .config import CONFIG
from .db_classes import dbconnect, dbsession, GenresMeta, BookDescription, VectorType, VectorsData
from .data import (
    genres_to_meta_init,
    fill_authors_book,
    fill_sequences_book,
    fill_genres_book,
    fill_books,
    make_authors_db,
    make_seqs_db,
    make_genres_db,
    make_books_db,
    make_book_descr_db,
    open_booklist,
    make_anno_vectors,
    get_count
)


def dbwrite(data):
    """write prepared data to db"""
    engine = dbconnect()
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add_all(data)
    session.commit()


def fill_genres_meta():  # pylint: disable=C0103
    """fill genres meta data"""
    engine = dbconnect()
    Session = sessionmaker(bind=engine)
    session = Session()

    meta = []
    with open('genres_meta.list', 'r', encoding='utf-8') as data:
        while True:
            line = data.readline()
            if not line:
                break
            (meta_id, name) = line.strip('\n').split('|')
            instance = session.query(GenresMeta).filter_by(meta_id=meta_id).first()
            if not instance:
                meta.append(GenresMeta(meta_id=int(meta_id), name=name))
    session.add_all(meta)
    session.commit()


def process_booklists_db(stage='fillonly'):
    """get booklists and fill it to process_booklist"""
    logging.info("begin stage %s", stage)
    zipdir = CONFIG['ZIPS']

    genres_to_meta_init()  # fill internal var by predefined data

    i = 0
    for booklist in sorted(glob.glob(zipdir + '/*.zip.list') + glob.glob(zipdir + '/*.zip.list.gz')):
        logging.info("[%s] %s", str(i), booklist)
        process_booklist(booklist, CONFIG['HIDE_DELETED'])
        i = i + 1
    logging.info("end stage %s", stage)


def process_booklist(booklist, hide_deleted="no"):
    """get data from booklist and fill it to db"""
    with open_booklist(booklist) as lst:
        count = 0
        lines = lst.readlines(int(CONFIG["PASS_SIZE_HINT"]))
        while len(lines) > 0:
            count = count + len(lines)
            # print("   %s" % count)
            logging.debug("   %s", count)
            process_books_batch(lines, hide_deleted)
            lines = lst.readlines(int(CONFIG["PASS_SIZE_HINT"]))


def process_books_batch(lines, hide_deleted):
    """fill books data to db"""
    authors = {}
    seqs = {}
    genres = {}
    books = {}
    deleted_cnt = 0
    for line in lines:
        book = json.loads(line)
        if book is None:
            continue
        if hide_deleted == "yes" and "deleted" in book and book["deleted"] == 1:
            deleted_cnt = deleted_cnt + 1
            continue
        authors = fill_authors_book(authors, book)
        seqs = fill_sequences_book(seqs, book)
        genres = fill_genres_book(genres, book)
        books = fill_books(books, book)
    dbwrite(make_books_db(books))
    dbwrite(make_book_descr_db(books))
    dbwrite(make_genres_db(genres))
    dbwrite(make_seqs_db(seqs))
    dbwrite(make_authors_db(authors))
    if hide_deleted == "yes":
        logging.debug(f"      deleted {deleted_cnt}")


def get_book_ids(session, limit=CONFIG["MAX_PASS_LENGTH"], offset=0):
    """return array of book_id"""
    ret = []
    data = session.query(BookDescription).offset(offset).limit(limit)
    for a in data:
        ret.append(a.book_id)
    return ret


def check_ids_vectors(session, book_ids, type):
    """return array of book_ids that are not processed"""
    existing_ids = session.query(VectorsData.id).filter(
        VectorsData.id.in_(book_ids),
        VectorsData.type == type
    ).all()

    existing_ids_set = {row[0] for row in existing_ids}
    return [id for id in book_ids if id not in existing_ids_set]


def make_vectors():
    """use pre-filled db data for make vectors"""
    if CONFIG["VECTOR_SEARCH"] not in (True, 'yes', 'YES', 'Yes'):
        logging.error("Vector search is not enabled")
        return
    limit = int(CONFIG["MAX_PASS_LENGTH"])
    offset = 0
    session = dbsession()
    book_cnt = get_count(session, BookDescription)
    logging.info("Making annotations vectors, total: %s, batch limit: %s", str(book_cnt), str(limit))
    book_ids = get_book_ids(session, limit, offset)
    while len(book_ids) > 0:
        ids = check_ids_vectors(session, book_ids, VectorType.BOOK_ANNO)
        dbwrite(make_anno_vectors(session, ids))

        logging.debug("  offset: %s, processed: %s", offset, len(ids))
        offset = offset + limit
        book_ids = get_book_ids(session, limit, offset)
    logging.info("end")
