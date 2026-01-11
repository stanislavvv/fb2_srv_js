# -*- coding: utf-8 -*-
"""database initialization and some utilities"""

import logging

from sqlalchemy import text, select

from .db_classes import Base, dbconnect, BookAuthor, BookDescription, BookSequence, BookGenre, GenresMeta, VectorsData
from .config import CONFIG
from .db_fill import fill_genres_meta


def dbtables():
    """prepare tables"""
    logging.info("[re]create tables in database")
    engine = dbconnect()
    # SQLAlchemy ORM не особо умеет в расширения постгреса
    with engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA pg_catalog;"))
        if CONFIG["VECTOR_SEARCH"] in (True, 'yes', 'YES', 'Yes'):
            connection.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))
            logging.debug('vector extention enable')
        connection.commit()

    # for non-vectorized instances -- do not create table
    vectors = Base.metadata.tables['vectors']
    if CONFIG["VECTOR_SEARCH"] not in (True, 'yes', 'YES', 'Yes'):
        Base.metadata.remove(vectors)

    Base.metadata.create_all(engine)
    fill_genres_meta()
    logging.info('end')


def dbclean():
    """cleanup database"""
    logging.info("cleanup database")
    engine = dbconnect()
    Base.metadata.drop_all(bind=engine)
    logging.info("end")


def get_genres_meta(session):
    """return genres metas dict -- meta_id: meta_name"""

    ret = {}
    m_data = session.query(GenresMeta).all()
    for m in m_data:
        meta_id = m.meta_id
        name = m.name
        # descr = m.description
        ret[meta_id] = name
    return ret


def get_genres(session):
    """return dict for gen_id: {"meta_id": meta_id, "name": genre_name}"""

    ret = {}
    g_data = session.query(BookGenre).all()
    for gen in g_data:
        gen_id = gen.id
        meta_id = gen.meta_id
        gen_name = gen.name
        ret[gen_id] = {
            "meta_id": meta_id,
            "name": gen_name
        }

    return ret


def get_books_descr(session, bookids):
    """return dict for: book_id: {BookDescription named fields dict}"""
    ret = {}
    data = session.query(BookDescription).filter(BookDescription.book_id.in_(bookids)).all()
    for b in data:
        book_id = b.book_id
        ret[book_id] = {
            "book_id": b.book_id,
            "book_title": b.book_title,
            "pub_isbn": b.pub_isbn,
            "pub_year": b.pub_year,
            "publisher": b.publisher,
            "publisher_id": b.publisher_id,
            "annotation": b.annotation
        }
    return ret


def get_authors(session, authids):
    """return dict for: author_id: {BookAuthor named fields dict}"""
    ret = {}
    data = session.query(BookAuthor).filter(BookAuthor.id.in_(authids)).all()
    for a in data:
        auth_id = a.id
        ret[auth_id] = {
            "id": a.id,
            "name": a.name
        }
    return ret


def get_seqs(session, seqids):
    """return dict for: author_id: {BookSequence named fields dict}"""
    ret = {}
    data = session.query(BookSequence).filter(BookSequence.id.in_(seqids)).all()
    for a in data:
        seq_id = a.id
        ret[seq_id] = {
            "id": a.id,
            "name": a.name
        }
    return ret


def get_ids_nearest(session, vector, type, limit):
    """return array of ids"""
    ret = []
    data = session.scalars(
        select(VectorsData)
        .where(VectorsData.is_bad == False)
        .order_by(VectorsData.embedding.l2_distance(vector))
        .limit(limit)
    )
    for i in data:
        ret.append(i.id)
    return ret
