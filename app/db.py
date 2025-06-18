# -*- coding: utf-8 -*-
"""database initialization"""

import logging

from sqlalchemy import text

from .db_classes import Base, dbconnect, BookGenre, GenresMeta
# from .config import CONFIG
from .db_fill import fill_genres_meta


def dbtables():
    """prepare tables"""
    logging.info("[re]create tables in database")
    engine = dbconnect()
    # SQLAlchemy ORM не умеет в расширения постгреса
    with engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA pg_catalog;"))
        connection.commit()
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
        descr = m.description
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
