# -*- coding: utf-8 -*-
"""database update"""

import logging
import glob

from sqlalchemy.orm import sessionmaker

from .config import CONFIG
from .db_classes import dbconnect, GenresMeta, BookGenre


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


def open_booklist(booklist):
    """return file object of booklist (.zip.list or .zip.list.gz)"""
    if booklist.find('gz') >= len(booklist) - 3:  # pylint: disable=R1705
        return gzip.open(booklist)
    else:
        return open(booklist, encoding="utf-8")


def process_booklist(booklist, hide_deleted=False):
    """get data from booklist and fill it to db"""
    logging.debug("process booklist %s", booklist)


def process_booklists_db(stage='fillonly'):
    """get booklists and fill it to process_booklist"""
    logging.info("begin stage %s", stage)
    zipdir = CONFIG['ZIPS']

    i = 0
    for booklist in sorted(glob.glob(zipdir + '/*.zip.list') + glob.glob(zipdir + '/*.zip.list.gz')):
        logging.info("[%s] %s", str(i), booklist)
        process_booklist(booklist, CONFIG['HIDE_DELETED'])
        i = i + 1

    # try:
    #     db.commit()
    # except Exception as ex:  # pylint: disable=W0703
    #     db.conn.rollback()
    #     logging.error("db commit exception:")
    #     logging.error(ex)
    #     return False
    logging.info("end stage %s", stage)
