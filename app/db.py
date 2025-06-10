# -*- coding: utf-8 -*-
"""working with database"""

from sqlalchemy import *
from sqlalchemy.dialects.postgresql import ARRAY, TEXT
from sqlalchemy.ext.declarative import declarative_base

from .config import CONFIG

Base = declarative_base()

class Book(Base):
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

class Description(Base):
    __tablename__ = 'book_descr'
    book_id = Column(String(32), ForeignKey("books.book_id"), primary_key=True)
    book_title = Column(String)
    pub_isbn = Column(String)
    pub_year = Column(String)
    publisher = Column(String)
    publisher_id = Column(String(32), index=True, nullable=False)
    annotation = Column(TEXT)
    __table_args__ = (
        Index('books_descr_title', 'book_title', postgresql_using="gin", postgresql_ops={"book_title": "gin_trgm_ops"},),
        Index('books_descr_anno', 'annotation', postgresql_using="gin", postgresql_ops={"annotation": "gin_trgm_ops"},),
    )

class Cover(Base):
    __tablename__ = 'books_covers'
    book_id = Column(String(32), ForeignKey("books.book_id"), primary_key=True)
    cover_ctype = Column(String)
    cover = Column(TEXT)

class Author(Base):
    __tablename__ = 'authors'
    id = Column(String(32), nullable=False, primary_key=True)
    name = Column(String, nullable=False)
    info = Column(TEXT, default='')
    __table_args__ = (
        Index('authors_names', 'name', postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"},),
    )

class Sequence(Base):
    __tablename__ = 'sequences'
    id = Column(String(32), nullable=False, primary_key=True)
    name = Column(String, nullable=False)
    info = Column(TEXT, default='')
    __table_args__ = (
        Index('seq_names', 'name', postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"},),
    )

class GenresMeta(Base):
    __tablename__ = 'genres_meta'
    meta_id = Column(String(32), nullable=False, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(TEXT, default='')

class Genre(Base):
    __tablename__ = 'genres'
    id = Column(String(32), nullable=False, primary_key=True)
    meta_id = Column(String(32), ForeignKey('genres_meta.meta_id'))
    name = Column(String, nullable=False)
    description = Column(TEXT, default='')


def dbconnect():
    dbpath = f"postgresql+psycopg2://{CONFIG['PG_USER']}:{CONFIG['PG_PASS']}@{CONFIG['PG_HOST']}:5432/{CONFIG['PG_BASE']}"
    engine = create_engine(dbpath)
    return engine

def dbtables():
    engine = dbconnect()
    # SQLAlchemy ORM не умеет в расширения постгреса
    with engine.connect() as connection: 
        connection.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    Base.metadata.create_all(engine)
    return

def dbclean():
    engine = dbconnect()
    Base.metadata.drop_all(bind=engine)

