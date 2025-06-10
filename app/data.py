# -*- coding: utf-8 -*-
"""in-vars data manipulations"""

import sys

from sqlalchemy.orm import sessionmaker

from .db_classes import (
    BookAuthor,
    BookSequence,
    BookGenre,
    Book,
    BookDescription,
    BookCover,
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
    books_tmp = {}
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


def make_book_covers_db(books):
    """return array of BookCover objects"""
    ret = []
    for book_id in books:
        if book_id is not None and books[book_id] is not None:
            book = books[book_id]
            if "cover" in book and book["cover"] is not None:
                cover = book["cover"]
                cover_ctype = cover["content-type"]
                cover_data = cover["data"]
                ret.append(
                    BookCover(
                        book_id=book_id,
                        cover_ctype=cover_ctype,
                        cover=cover_data
                    )
                )
    return ret
