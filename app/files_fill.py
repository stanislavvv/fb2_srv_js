# -*- coding: utf-8 -*-
"""create static data for authors/sequences/genres"""

import logging
import glob
import json
import base64

from pathlib import Path
from sqlalchemy.orm import sessionmaker

from .config import CONFIG
from .data import open_booklist, seqs_in_data, nonseq_from_data, refine_book
from .strings import id2path, id2pathonly
from .db_classes import (
    dbconnect,
    BookAuthor
)

# MAX_PASS_LENGTH = 4000
MAX_PASS_LENGTH = 20000
MAX_PASS_LENGTH_GEN = 5
PASS_SIZE_HINT = 10485760

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


def make_book_covers():
    """walk over .list's and extract book covers to struct"""

    logging.info("make book covers")

    pagesdir = CONFIG['PAGES']
    coversdir = pagesdir + '/covers'
    Path(coversdir).mkdir(parents=True, exist_ok=True)

    zipdir = CONFIG['ZIPS']
    hide_deleted = CONFIG['HIDE_DELETED']

    i = 0
    for booklist in sorted(glob.glob(zipdir + '/*.zip.list') + glob.glob(zipdir + '/*.zip.list.gz')):
        logging.info("[%s] %s", str(i), booklist)
        with open_booklist(booklist) as lst:
            count = 0
            lines = lst.readlines(PASS_SIZE_HINT)
            while len(lines) > 0:
                count = count + len(lines)
                # print("   %s" % count)
                logging.info("   %s", count)
                make_book_covers_data(lines, coversdir, hide_deleted)
                lines = lst.readlines(PASS_SIZE_HINT)
        i = i + 1
    logging.info("end")


def make_book_covers_data(lines, coversdir, hide_deleted=False):
    for line in lines:
        book = json.loads(line)
        if book is not None and book['book_id'] is not None:
            book_id = book['book_id']
            zip_file = book['zipfile']
            filename = book['filename']
            if "cover" in book and book["cover"] is not None:
                cover = book["cover"]
                # cover_ctype = cover["content-type"]
                cover_data = cover["data"] + '===='  # pad base64 data
                workdir = coversdir + '/' + id2pathonly(book_id)
                Path(workdir).mkdir(parents=True, exist_ok=True)
                try:
                    img_bytes = base64.b64decode(cover_data)
                    with open(workdir + '/' + book_id + '.jpg', 'wb') as img:
                        img.write(img_bytes)
                except Exception as ex:
                    logging.error('image error in %s/%s: %s', zip_file, filename, ex)
