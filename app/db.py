# -*- coding: utf-8 -*-
"""database initialization"""

import logging

from .db_classes import Base, dbconnect
from .config import CONFIG
from .db_fill import fill_genres_meta


def dbtables():
    """prepare tables"""
    logging.info("[re]create tables in database")
    engine = dbconnect()
    # SQLAlchemy ORM не умеет в расширения постгреса
    with engine.connect() as connection:
        connection.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    Base.metadata.create_all(engine)
    fill_genres_meta()
    logging.info('end')


def dbclean():
    """cleanup database"""
    logging.info("cleanup database")
    engine = dbconnect()
    Base.metadata.drop_all(bind=engine)
    logging.info("end")


def get_genre_meta(meta_id):
    """return genre meta object"""
    engine = dbconnect()
    # FixMe: дописать
