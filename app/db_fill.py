# -*- coding: utf-8 -*-
"""database update"""

import logging
import glob
import json

from sqlalchemy.orm import sessionmaker

from .config import CONFIG
from .db_classes import dbconnect, GenresMeta
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
    # make_book_covers_db,
    open_booklist
)


# ToDo: test it on OrangePi with bigger values
# MAX_PASS_LENGTH = 4000
# MAX_PASS_LENGTH_GEN = 5

# PASS_SIZE_HINT = 10485760


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


def process_booklist(booklist, hide_deleted=False):
    """get data from booklist and fill it to db"""
    with open_booklist(booklist) as lst:
        count = 0
        lines = lst.readlines(int(CONFIG["PASS_SIZE_HINT"]))
        while len(lines) > 0:
            count = count + len(lines)
            # print("   %s" % count)
            logging.info("   %s", count)
            process_books_batch(lines, hide_deleted)
            lines = lst.readlines(int(CONFIG["PASS_SIZE_HINT"]))


def process_books_batch(lines, hide_deleted):
    """fill books data to db"""
    authors = {}
    seqs = {}
    genres = {}
    books = {}
    for line in lines:
        book = json.loads(line)
        if book is None:
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
