# -*- coding: utf-8 -*-
"""database definitions"""

# from sqlalchemy import *
from sqlalchemy import (
    Column,
    String,
    Date,
    Integer,
    Boolean,
    Index,
    ForeignKey,
    create_engine
)
from sqlalchemy.dialects.postgresql import ARRAY, TEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import CONFIG

Base = declarative_base()

# pylint: disable=R0903


class Book(Base):
    """book data"""
    __tablename__ = 'books'
    zipfile = Column(String, index=True, nullable=False)
    filename = Column(String, index=True, nullable=False)
    genres = Column(ARRAY(String), nullable=False)
    authors = Column(ARRAY(String), nullable=False)
    sequences = Column(ARRAY(String), nullable=False)
    book_id = Column(String(32), nullable=False, primary_key=True)
    lang = Column(String)
    date = Column(Date)
    size = Column(Integer)
    deleted = Column(Boolean)


class BookDescription(Base):
    """book description and publish info"""
    __tablename__ = 'book_descr'
    book_id = Column(String(32), ForeignKey("books.book_id"), primary_key=True)
    book_title = Column(String)
    pub_isbn = Column(String)
    pub_year = Column(String)
    publisher = Column(String)
    publisher_id = Column(String(32), index=True, nullable=False)
    annotation = Column(TEXT)
    __table_args__ = (
        Index(
            'books_descr_title',
            'book_title',
            postgresql_using="gin",
            postgresql_ops={"book_title": "gin_trgm_ops"},
        ),
        Index(
            'books_descr_anno',
            'annotation',
            postgresql_using="gin",
            postgresql_ops={"annotation": "gin_trgm_ops"},
        ),
    )


# class BookCover(Base):
#     """book cover image"""
#     __tablename__ = 'books_covers'
#     book_id = Column(String(32), ForeignKey("books.book_id"), primary_key=True)
#     cover_ctype = Column(String)
#     cover = Column(TEXT)


class BookAuthor(Base):
    """books author"""
    __tablename__ = 'authors'
    id = Column(String(32), nullable=False, primary_key=True)
    name = Column(String, nullable=False)
    info = Column(TEXT, default='')
    __table_args__ = (
        Index('authors_names', 'name', postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"},),
    )


class BookSequence(Base):
    """sequence/series of books"""
    __tablename__ = 'sequences'
    id = Column(String(32), nullable=False, primary_key=True)
    name = Column(String, nullable=False)
    info = Column(TEXT, default='')
    __table_args__ = (
        Index('seq_names', 'name', postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"},),
    )


class GenresMeta(Base):
    """meta genre/genres group"""
    __tablename__ = 'genres_meta'
    meta_id = Column(String(32), nullable=False, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(TEXT, default='')


class BookGenre(Base):
    """genre"""
    __tablename__ = 'genres'
    id = Column(String(32), nullable=False, primary_key=True)
    meta_id = Column(String(32), ForeignKey('genres_meta.meta_id'))
    name = Column(String, nullable=False)
    description = Column(TEXT, default='')


def dbconnect():
    """connect to db and return engine"""
    dbpath = "postgresql+psycopg2://%s:%s@%s:5432/%s" % (
        CONFIG['PG_USER'],
        CONFIG['PG_PASS'],
        CONFIG['PG_HOST'],
        CONFIG['PG_BASE']
    )
    engine = create_engine(dbpath)
    return engine


def dbsession():
    """connect to db and return session"""
    engine = dbconnect()
    Session = sessionmaker(bind=engine)
    session = Session()
    return session
