# -*- coding: utf-8 -*-
"""create static data for authors/sequences/genres"""

import logging
import glob
import json

from pathlib import Path
from sqlalchemy.orm import sessionmaker

from .config import CONFIG
from .data import open_booklist, seqs_in_data, nonseq_from_data, refine_book
from .strings import id2path
from .db_classes import (
    dbconnect,
    BookAuthor
)

# MAX_PASS_LENGTH = 4000
MAX_PASS_LENGTH = 20000
MAX_PASS_LENGTH_GEN = 5

auth_processed = {}
seq_processed = {}
gen_processed = {}


def make_pages_dir():
    """make root dir for static data"""
    pagesdir = CONFIG['PAGES']
    Path(pagesdir).mkdir(parents=True, exist_ok=True)


def make_authorsindex():
    """make pages/authorsindex content"""
    make_pages_dir()
    engine = dbconnect()
    Session = sessionmaker(bind=engine)
    session = Session()
    auth_cnt = session.query(BookAuthor).count()
    logging.info("Creating authors indexes (total: %d)...", auth_cnt)
    processed = -1
    while processed != 0:
        processed = make_auth_data(session)
        logging.debug(" - processed authors: %d/%d, in pass: %d", len(auth_processed), auth_cnt, processed)
    # make_auth_subindexes(db, pagesdir)
    session.close()


def make_auth_data(session):
    """pass over authors and make pages/authorsindex"""

    hide_deleted = CONFIG['HIDE_DELETED']
    zipdir = CONFIG['ZIPS']
    pagesdir = CONFIG['PAGES']

    auth_data = {}
    for booklist in sorted(glob.glob(zipdir + '/*.zip.list') + glob.glob(zipdir + '/*.zip.list.gz')):
        with open_booklist(booklist) as lst:
            for b in lst:
                book = json.loads(b)
                if book is None:
                    continue
                if hide_deleted and "deleted" in book and book["deleted"] != 0:
                    continue
                book = refine_book(book)
                if book["authors"] is not None:
                    book = refine_book(book)
                    for auth in book["authors"]:
                        auth_id = auth.get("id")
                        auth_name = auth.get("name")
                        if auth_id not in auth_processed:
                            if auth_id in auth_data:
                                s = auth_data[auth_id]["books"]
                                s.append(book)
                                auth_data[auth_id]["books"] = s
                            elif len(auth_data) < MAX_PASS_LENGTH:
                                s = {"name": auth_name, "id": auth_id}
                                b = []
                                b.append(book)
                                s["books"] = b
                                auth_data[auth_id] = s
    for auth_id in auth_data:
        data = auth_data[auth_id]

        workdir = pagesdir + "/author/" + id2path(auth_id)
        Path(workdir).mkdir(parents=True, exist_ok=True)

        allbooks = data["books"]
        workfile = workdir + "/all.json"
        with open(workfile, 'w') as idx:
            json.dump(allbooks, idx, indent=2, ensure_ascii=False)

        seqs = seqs_in_data(auth_data[auth_id]["books"])
        workfile = workdir + "/sequences.json"
        with open(workfile, 'w') as idx:
            json.dump(seqs, idx, indent=2, ensure_ascii=False)

        nonseqs = nonseq_from_data(auth_data[auth_id]["books"])
        workfile = workdir + "/sequenceless.json"
        with open(workfile, 'w') as idx:
            json.dump(nonseqs, idx, indent=2, ensure_ascii=False)

        main = data
        del main["books"]
        workfile = workdir + "/index.json"
        with open(workfile, 'w') as idx:
            json.dump(main, idx, indent=2, ensure_ascii=False)
        auth_processed[auth_id] = 1
    return len(auth_data.keys())
