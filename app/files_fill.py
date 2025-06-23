# -*- coding: utf-8 -*-
"""create static data for authors/sequences/genres"""

import logging
import glob
import json
# import base64
import shutil

from functools import cmp_to_key
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func

from .config import CONFIG
from .data import (
    open_booklist,
    seqs_in_data,
    nonseq_from_data,
    refine_book,
    custom_alphabet_book_title_cmp,
    decode_b64
)
from .strings import (
    id2path,
    id2pathonly,
    string2filename
)
from .db_classes import (
    dbconnect,
    BookAuthor,
    BookSequence,
    BookGenre
)
from .db import (
    get_genres,
    get_genres_meta
)

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
    logging.info("Creating per-authors indexes (total: %d)...", auth_cnt)
    processed = -1
    while processed != 0:
        processed = make_auth_data(session)
        logging.debug(" - processed authors: %d/%d, in pass: %d", len(auth_processed), auth_cnt, processed)

    logging.debug("Creating author's tree indexes")
    make_auth_subindexes(session)
    logging.debug("end")
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
                            elif len(auth_data) < int(CONFIG["MAX_PASS_LENGTH"]):
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
        with open(workfile, 'w', encoding="utf-8") as idx:
            json.dump(allbooks, idx, indent=2, ensure_ascii=False)

        seqs = seqs_in_data(auth_data[auth_id]["books"])
        workfile = workdir + "/sequences.json"
        with open(workfile, 'w', encoding="utf-8") as idx:
            json.dump(seqs, idx, indent=2, ensure_ascii=False)

        nonseqs = nonseq_from_data(auth_data[auth_id]["books"])
        workfile = workdir + "/sequenceless.json"
        with open(workfile, 'w', encoding="utf-8") as idx:
            json.dump(nonseqs, idx, indent=2, ensure_ascii=False)

        main = data
        del main["books"]
        workfile = workdir + "/index.json"
        with open(workfile, 'w', encoding="utf-8") as idx:
            json.dump(main, idx, indent=2, ensure_ascii=False)
        auth_processed[auth_id] = 1
    return len(auth_data.keys())


def make_auth_subindexes(session):
    """make per-letter/three-letter indexes"""
    pagesdir = CONFIG['PAGES']
    workdir = pagesdir + '/authorsindex/'

    Path(workdir).mkdir(parents=True, exist_ok=True)

    first_letters = session.query(
        func.upper(func.left(BookAuthor.name, 1)).distinct().label('first_letter')
    ).all()
    idx = {}
    for letter in first_letters:
        idx[letter[0]] = 1
    with open(workdir + "index.json", "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2, ensure_ascii=False)

    for letter in idx.keys():
        three_l = session.query(
            func.upper(func.left(BookAuthor.name, 3))
            .label('first_three')
        ).filter(
            # BookAuthor.name.ilike(f'{letter}%')
            func.upper(func.left(BookAuthor.name, 1)) == letter
        ).group_by('first_three').all()
        logging.debug("- %s", letter)
        t_idx = {}
        t_real = {}
        for t in three_l:
            t_real[t[0]] = 1
            t_pad = string2filename("%-3s" % t[0].upper())
            t_idx[t_pad] = 1
        Path(workdir + string2filename(letter)).mkdir(parents=True, exist_ok=True)
        with open(workdir + string2filename(letter) + "/index.json", "w", encoding="utf-8") as f:
            json.dump(t_idx, f, indent=2, ensure_ascii=False)
        t_idx = {}
        for t in t_real.keys():
            if len(t) < 3:
                pattern = t
                authors = session.query(BookAuthor).filter(
                    func.upper(BookAuthor.name) == func.upper(pattern)
                ).all()
            else:
                pattern = t + '%'
                authors = session.query(BookAuthor).filter(
                    BookAuthor.name.ilike(pattern)
                ).all()
            t_pad = string2filename("%-3s" % t)
            if t_pad not in t_idx:
                t_idx[t_pad] = {}
            for a in authors:
                t_idx[t_pad][a.id] = a.name
        for idx in t_idx.keys():
            with open(workdir + string2filename(letter) + f"/{idx}.json", "w", encoding="utf-8") as f:
                json.dump(t_idx[idx], f, indent=2, ensure_ascii=False)


def make_book_covers():
    """walk over .list's and extract book covers to struct"""

    logging.info("make book covers")

    pagesdir = CONFIG['PAGES']
    coversdir = pagesdir + '/covers'
    Path(coversdir).mkdir(parents=True, exist_ok=True)

    zipdir = CONFIG['ZIPS']
    hide_deleted = CONFIG['HIDE_DELETED']

    passhint = int(CONFIG['PASS_SIZE_HINT'])

    i = 0
    for booklist in sorted(glob.glob(zipdir + '/*.zip.list') + glob.glob(zipdir + '/*.zip.list.gz')):
        logging.info("[%s] %s", str(i), booklist)
        with open_booklist(booklist) as lst:
            count = 0
            lines = lst.readlines(passhint)
            while len(lines) > 0:
                count = count + len(lines)
                # print("   %s" % count)
                logging.info("   %s", count)
                make_book_covers_data(lines, coversdir, hide_deleted)
                lines = lst.readlines(passhint)
        i = i + 1
    shutil.copy(CONFIG['DEFAULT_COVER_SRC'], pagesdir + CONFIG['DEFAULT_COVER'])
    logging.info("end")


def make_book_covers_data(lines, coversdir, hide_deleted=False):
    """write covers previews from jsonl lines data"""
    for line in lines:
        book = json.loads(line)
        if book is not None and book['book_id'] is not None:
            book_id = book['book_id']
            zip_file = book['zipfile']
            filename = book['filename']
            if "cover" in book and book["cover"] is not None:
                cover = book["cover"]
                # cover_ctype = cover["content-type"]
                cover_data = cover["data"] + '==='  # pad base64 data
                workdir = coversdir + '/' + id2pathonly(book_id)
                Path(workdir).mkdir(parents=True, exist_ok=True)
                try:
                    img_bytes = decode_b64(cover_data)
                    with open(workdir + '/' + book_id + '.jpg', 'wb') as img:
                        img.write(img_bytes)
                except Exception as ex:
                    logging.error('image error in %s/%s: %s', zip_file, filename, ex)


def make_sequencesindex():
    """make pages/sequencesindex content"""
    make_pages_dir()
    engine = dbconnect()
    Session = sessionmaker(bind=engine)
    session = Session()
    seq_cnt = session.query(BookSequence).count()
    logging.info("Creating per-sequences indexes (total: %d)...", seq_cnt)
    processed = -1
    while processed != 0:
        processed = make_seq_data(session)
        logging.debug(" - processed sequences: %d/%d, in pass: %d", len(seq_processed), seq_cnt, processed)

    logging.debug("Creating sequences tree indexes")
    make_seq_subindexes(session)
    logging.debug("end")
    session.close()


def make_seq_data(session):
    """make book sequences index"""

    hide_deleted = CONFIG['HIDE_DELETED']
    zipdir = CONFIG['ZIPS']
    pagesdir = CONFIG['PAGES']

    seq_data = {}
    for booklist in sorted(glob.glob(zipdir + '/*.zip.list') + glob.glob(zipdir + '/*.zip.list.gz')):
        with open_booklist(booklist) as lst:
            for b in lst:
                book = json.loads(b)
                if book is None:
                    continue
                if hide_deleted and "deleted" in book and book["deleted"] != 0:
                    continue
                book = refine_book(book)
                if book["sequences"] is not None:
                    book = refine_book(book)
                    for seq in book["sequences"]:
                        seq_id = seq.get("id")
                        seq_name = seq.get("name")
                        if seq_id is not None and seq_id not in seq_processed:
                            if seq_id in seq_data:
                                s = seq_data[seq_id]["books"]
                                s.append(book)
                                seq_data[seq_id]["books"] = s
                            elif len(seq_data) < int(CONFIG["MAX_PASS_LENGTH"]):
                                s = {"name": seq_name, "id": seq_id}
                                b = []
                                b.append(book)
                                s["books"] = b
                                seq_data[seq_id] = s
    for seq_id in seq_data:
        data = seq_data[seq_id]

        workdir = pagesdir + "/sequence/" + id2pathonly(seq_id)
        Path(workdir).mkdir(parents=True, exist_ok=True)

        workfile = workdir + f"/{seq_id}.json"
        with open(workfile, 'w', encoding="utf-8") as idx:
            json.dump(data, idx, indent=2, ensure_ascii=False)
        seq_processed[seq_id] = 1

    return len(seq_data.keys())


def make_seq_subindexes(session):
    """make per-letter/three-letter indexes for sequences"""
    pagesdir = CONFIG['PAGES']
    workdir = pagesdir + '/sequencesindex/'

    Path(workdir).mkdir(parents=True, exist_ok=True)

    first_letters = session.query(
        func.upper(func.left(BookSequence.name, 1)).distinct().label('first_letter')
    ).all()
    idx = {}
    for letter in first_letters:
        idx[letter[0]] = 1
    with open(workdir + "index.json", "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2, ensure_ascii=False)

    for letter in idx.keys():
        if len(letter) < 1:
            continue
        three_l = session.query(
            func.upper(func.left(BookSequence.name, 3))
            .label('first_three')
        ).filter(
            func.upper(func.left(BookSequence.name, 1)) == letter
        ).group_by('first_three').all()
        logging.debug("- %s", letter)
        t_idx = {}
        t_real = {}
        for t in three_l:
            t_real[t[0]] = 1
            t_pad = string2filename("%-3s" % t[0].upper())
            t_idx[t_pad] = 1
        Path(workdir + string2filename(letter)).mkdir(parents=True, exist_ok=True)
        with open(workdir + string2filename(letter) + "/index.json", "w", encoding="utf-8") as f:
            json.dump(t_idx, f, indent=2, ensure_ascii=False)
        t_idx = {}
        for t in t_real.keys():
            if len(t) < 3:
                pattern = t
                seqors = session.query(BookSequence).filter(
                    func.upper(BookSequence.name) == func.upper(pattern)
                ).all()
            else:
                pattern = t + '%'
                seqors = session.query(BookSequence).filter(
                    BookSequence.name.ilike(pattern)
                ).all()
            t_pad = string2filename("%-3s" % t)
            if t_pad not in t_idx:
                t_idx[t_pad] = {}
            for a in seqors:
                t_idx[t_pad][a.id] = a.name
        for idx in t_idx.keys():
            with open(workdir + string2filename(letter) + f"/{idx}.json", "w", encoding="utf-8") as f:
                json.dump(t_idx[idx], f, indent=2, ensure_ascii=False)


def make_genresindex():
    """make pages/genresindex content"""
    make_pages_dir()
    engine = dbconnect()
    Session = sessionmaker(bind=engine)
    session = Session()
    seq_cnt = session.query(BookGenre).count()
    logging.info("Creating per-genre indexes (total: %d)...", seq_cnt)
    processed = -1
    while processed != 0:
        processed = make_genres_data(session)
        logging.debug(" - processed genres: %d/%d, in pass: %d", len(gen_processed), seq_cnt, processed)

    logging.debug("Creating genres tree indexes")
    make_genres_subindexes(session)
    logging.debug("end")
    session.close()


def make_genres_data(session):
    """make book genres index"""

    hide_deleted = CONFIG['HIDE_DELETED']
    zipdir = CONFIG['ZIPS']
    pagesdir = CONFIG['PAGES']

    genres = get_genres(session)

    gen_data = {}
    gen_names = {}
    for booklist in sorted(glob.glob(zipdir + '/*.zip.list') + glob.glob(zipdir + '/*.zip.list.gz')):
        with open_booklist(booklist) as lst:
            for b in lst:
                book = json.loads(b)
                if book is None:
                    continue
                if hide_deleted and "deleted" in book and book["deleted"] != 0:
                    continue
                book = refine_book(book)
                if book["genres"] is not None:
                    book = refine_book(book)
                    for gen in book["genres"]:
                        gen_id = gen
                        gen_name = gen
                        if gen in genres:
                            gen_name = genres[gen]["name"]
                        gen_names[gen_id] = gen_name
                        if gen_id not in gen_processed:
                            if gen_id in gen_data:
                                s = gen_data[gen_id]
                                s.append(book)
                                gen_data[gen_id] = s
                            elif len(gen_data) < int(CONFIG["MAX_PASS_LENGTH_GEN"]):
                                s = []
                                s.append(book)
                                gen_data[gen_id] = s

    workdir = pagesdir + "/genre/"
    Path(workdir).mkdir(parents=True, exist_ok=True)
    for gen in gen_data:
        workdir = pagesdir + "/genre/" + string2filename(gen)
        Path(workdir).mkdir(parents=True, exist_ok=True)

        data = []
        for book in gen_data[gen]:
            data.append(book["book_id"])

        workfile = pagesdir + "/genre/" + string2filename(gen) + "/all.json"
        with open(workfile, 'w', encoding="utf-8") as idx:
            json.dump(data, idx, indent=2, ensure_ascii=False)

        i = 0
        data = sorted(gen_data[gen], key=cmp_to_key(custom_alphabet_book_title_cmp))
        while len(data) > 0:
            wdata = data[:50]
            data = data[50:]
            workfile = pagesdir + "/genre/" + string2filename(gen) + "/" + str(i) + ".json"
            with open(workfile, 'w', encoding="utf-8") as idx:
                json.dump(wdata, idx, indent=2, ensure_ascii=False)
            i = i + 1
        gen_processed[gen] = 1
    return len(gen_data.keys())


def make_genres_subindexes(session):
    """make meta/genres indexes"""
    pagesdir = CONFIG['PAGES']
    workdir = pagesdir + '/genresindex/'

    Path(workdir).mkdir(parents=True, exist_ok=True)

    meta_data = get_genres_meta(session)
    with open(workdir + "index.json", "w", encoding="utf-8") as f:
        json.dump(meta_data, f, indent=2, ensure_ascii=False)

    genres = get_genres(session)

    data = {}
    for gen_id in genres:
        gen_name = genres[gen_id]["name"]
        meta_id = genres[gen_id]["meta_id"]
        if meta_id not in data:
            data[meta_id] = {}
        data[meta_id][gen_id] = gen_name
    for meta_id in data:
        meta = data[meta_id]
        with open(workdir + string2filename(meta_id) + ".json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
