# -*- coding: utf-8 -*-
"""in-vars data manipulations"""

import gzip

from sqlalchemy.orm import sessionmaker

from .config import CONFIG
from .strings import make_id
from .db_classes import (
    BookAuthor,
    BookSequence,
    BookGenre,
    Book,
    BookDescription,
    dbconnect
)

genres = {}


def genres_to_meta_init():
    """load genres info from file"""
    with open('genres.list') as lst:
        while True:
            line = lst.readline()
            if not line:
                break
            genre_line = line.strip('\n').split('|')
            if len(genre_line) > 1:
                genres[genre_line[1]] = {"descr": genre_line[2], "meta_id": genre_line[0]}


def get_exist_authors(author_ids):
    """return authors ids, which exists in database"""
    ret = []
    engine = dbconnect()
    Session = sessionmaker(bind=engine)
    session = Session()
    data = session.query(BookAuthor).filter(BookAuthor.id.in_(author_ids)).all()
    for auth in data:
        auth_id = auth.id
        if auth_id in author_ids:
            ret.append(auth_id)
    session.close()
    return ret


def get_exist_seqs(seq_ids):
    """return sequences ids, which exists in database"""
    ret = []
    engine = dbconnect()
    Session = sessionmaker(bind=engine)
    session = Session()
    data = session.query(BookSequence).filter(BookSequence.id.in_(seq_ids)).all()
    for seq in data:
        seq_id = seq.id
        if seq_id in seq_ids:
            ret.append(seq_id)
    session.close()
    return ret


def fill_authors_book(authors, book):
    """return array of BookAuthor objects for given book"""
    authors_tmp = {}
    auth_ids_tmp = []
    if book is None or "authors" not in book or book["authors"] is None or len(book["authors"]) < 1:
        return authors
    for author in book["authors"]:
        authors_tmp[author["id"]] = author["name"]
        auth_ids_tmp.append(author["id"])
    new_author_ids = get_exist_authors(auth_ids_tmp)
    for auth_id in auth_ids_tmp:
        if auth_id not in new_author_ids:
            authors[auth_id] = authors_tmp[auth_id]
    return authors


def make_authors_db(authors):
    ret = []
    for auth in authors:
        if auth is not None and authors[auth] is not None:
            ret.append(
                BookAuthor(
                    id=auth,
                    name=authors[auth]
                )
            )
    return ret


def fill_sequences_book(seqs, book):
    """return array of BookSequence objects for given book"""
    seqs_tmp = {}
    seq_ids_tmp = []
    if book is None or "sequences" not in book or book["sequences"] is None or len(book["sequences"]) < 1:
        return seqs
    for seq in book["sequences"]:
        if "id" in seq and seq["id"] is not None and "name" in seq and seq["name"] is not None:
            seqs_tmp[seq["id"]] = seq["name"]
            seq_ids_tmp.append(seq["id"])
    new_seq_ids = get_exist_seqs(seq_ids_tmp)
    for seq_id in seq_ids_tmp:
        if seq_id not in new_seq_ids:
            seqs[seq_id] = seqs_tmp[seq_id]
    return seqs


def make_seqs_db(seqs):
    ret = []
    for seq in seqs:
        if seq is not None and seqs[seq] is not None:
            ret.append(
                BookSequence(
                    id=seq,
                    name=seqs[seq]
                )
            )
    return ret


def get_exist_genres(genre_ids):
    """return genres ids, which exists in database"""
    ret = []
    engine = dbconnect()
    Session = sessionmaker(bind=engine)
    session = Session()
    data = session.query(BookGenre).filter(BookGenre.id.in_(genre_ids)).all()
    for genre in data:
        genre_id = genre.id
        if genre_id in genre_ids:
            ret.append(genre_id)
    session.close()
    return ret


def fill_genres_book(genres, book):
    """return array of BookGenre objects for given book"""
    genres_tmp = {}
    genre_ids_tmp = []
    if book is None or "genres" not in book or book["genres"] is None or len(book["genres"]) < 1:
        return genres
    for genre in book["genres"]:
        genres_tmp[genre] = 1
        genre_ids_tmp.append(genre)
    new_genre_ids = get_exist_genres(genre_ids_tmp)
    for genre_id in genre_ids_tmp:
        if genre_id not in new_genre_ids:
            genres[genre_id] = genres_tmp[genre_id]
    return genres


def make_genres_db(genre_ids):
    ret = []
    for genre in genre_ids:
        if genre is not None and genre_ids[genre] is not None:
            if genre in genres:  # ToDo: remove checking after wrong genre replacement
                gdata = genres[genre]
                ret.append(
                    BookGenre(
                        id=genre,
                        name=gdata["descr"],
                        meta_id=gdata["meta_id"]
                    )
                )
    return ret


def get_exists_book(book_ids):
    """return book ids, which exists in database"""
    ret = []
    engine = dbconnect()
    Session = sessionmaker(bind=engine)
    session = Session()
    data = session.query(Book).filter(Book.book_id.in_(book_ids)).all()
    for book in data:
        book_id = book.book_id
        if book_id in book_ids:
            ret.append(book_id)
    session.close()
    return ret


def fill_books(books, book):
    """append new-only book to books"""
    new_book_ids = get_exists_book([book["book_id"]])
    if new_book_ids is None or len(new_book_ids) < 1:
        books[book["book_id"]] = book
    return books


def make_books_db(books):
    """return array of Books objects"""
    ret = []
    for book_id in books:
        if book_id is not None and books[book_id] is not None:
            book = books[book_id]
            author_ids = []
            if "authors" in book and book["authors"] is not None:
                for auth in book["authors"]:
                    author_ids.append(auth["id"])
            seq_ids = []
            if "sequences" in book and book["sequences"] is not None:
                for seq in book["sequences"]:
                    if "id" in seq and seq["id"] is not None:
                        seq_ids.append(seq["id"])
            ret.append(
                Book(
                    zipfile=book["zipfile"],
                    filename=book["filename"],
                    genres=book["genres"],
                    authors=author_ids,
                    sequences=seq_ids,
                    book_id=book["book_id"],
                    lang=book["lang"],
                    date=book["date_time"],
                    size=book["size"],
                    deleted=book["deleted"]
                )
            )
    return ret


def make_book_descr_db(books):
    """return array of BookDescription objects"""
    ret = []
    for book_id in books:
        if book_id is not None and books[book_id] is not None:
            book = books[book_id]
            pubinfo = book["pub_info"]
            ret.append(
                BookDescription(
                    book_id=book_id,
                    book_title=book["book_title"],
                    pub_isbn=pubinfo["isbn"],
                    pub_year=pubinfo["year"],
                    publisher=pubinfo["publisher"],
                    publisher_id=pubinfo["publisher_id"],
                    annotation=book["annotation"]
                )
            )
    return ret


def open_booklist(booklist):
    """return file object of booklist (.zip.list or .zip.list.gz)"""
    if booklist.find('gz') >= len(booklist) - 3:  # pylint: disable=R1705
        return gzip.open(booklist)
    else:
        return open(booklist, encoding="utf-8")


def seqs_in_data(data):
    """return [{"name": "...", "id": "...", "cnt": 1}, ...]"""
    ret = []
    seq_idx = {}
    for book in data:
        if book["sequences"] is not None:
            for seq in book["sequences"]:
                seq_id = seq.get("id")
                if seq_id is not None:
                    seq_name = seq["name"]
                    if seq_id in seq_idx:
                        s = seq_idx[seq_id]
                        count = s["cnt"]
                        count = count + 1
                        s["cnt"] = count
                        seq_idx[seq_id] = s
                    else:
                        s = {"name": seq_name, "id": seq_id, "cnt": 1}
                        seq_idx[seq_id] = s
    for seq in seq_idx:
        ret.append(seq_idx[seq])
    return ret


def nonseq_from_data(data):
    """return books_id[] without sequences"""
    ret = []
    for book in data:
        if book["sequences"] is None:
            book_id = book["book_id"]
            ret.append(book_id)
    return ret


def refine_book(book):
    """strip images and refine some other data from books info"""
    if "genres" not in book or book["genres"] in (None, "", []):
        book["genres"] = ["other"]
    # book["genres"] = db.genres_replace(book, book["genres"])
    # book["lang"] = db.lang_replace(book, book["lang"])
    if "cover" in book:
        del book["cover"]
    if "authors" not in book:
        author = [
            {
                "name": CONFIG['AUTHOR_PLACEHOLDER'],
                "id": make_id(CONFIG['AUTHOR_PLACEHOLDER'])
            }
        ]
        book["authors"] = author
    return book
