# -*- coding: utf-8 -*-
"""in-vars data manipulations"""

import gzip
import base64
import logging
import urllib

from sqlalchemy.orm import sessionmaker
from bs4 import BeautifulSoup
import openai

from .config import CONFIG, VECTOR_SIZE
from .strings import make_id
from .db_classes import (
    BookAuthor,
    BookSequence,
    BookGenre,
    Book,
    BookDescription,
    VectorsData,
    VectorType,
    dbconnect
)

alphabet_1 = [  # first letters in main authors/sequences page
    'А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З', 'И', 'Й',
    'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф',
    'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь', 'Э', 'Ю', 'Я'
]

alphabet_2 = [  # second letters in main authors/sequences page
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
    'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
    'U', 'V', 'W', 'X', 'Y', 'Z'
]

genres = {}
genres_meta = {}


def cmp_in_arr(arr, char1, char2):
    """compare characters by array"""
    if char1 in arr and char2 in arr:
        idx1 = arr.index(char1)
        idx2 = arr.index(char2)
        if idx1 == idx2:  # pylint: disable=R1705
            return 0
        elif idx1 < idx2:
            return -1
        else:
            return 1
    else:
        return None


def custom_char_cmp(char1: str, char2: str):  # pylint: disable=R0911
    """custom compare chars"""
    if char1 == char2:
        return 0

    if char1 in alphabet_1 and char2 not in alphabet_1:
        return -1
    if char1 in alphabet_2 and char2 not in alphabet_2 and char2 not in alphabet_1:
        return -1
    if char2 in alphabet_1 and char1 not in alphabet_1:
        return 1
    if char2 in alphabet_2 and char1 not in alphabet_2 and char1 not in alphabet_1:
        return 1

    # sort by array order
    if char1 in alphabet_1 and char2 in alphabet_1:
        return cmp_in_arr(alphabet_1, char1, char2)
    if char1 in alphabet_2 and char1 in alphabet_2:
        return cmp_in_arr(alphabet_2, char1, char2)

    if char1 < char2:  # pylint: disable=R1705
        return -1
    else:
        return +1


def custom_alphabet_cmp(str1: str, str2: str):  # pylint: disable=R0911
    """custom compare strings"""
    # pylint: disable=R1705
    s1len = len(str1)
    s2len = len(str2)
    i = 0

    # zero-length strings case
    if s1len == i:
        if i == s2len:
            return 0
        else:
            return -1
    elif i == s2len:
        return 1

    while custom_char_cmp(str1[i], str2[i]) == 0:
        i = i + 1
        if i == s1len:
            if i == s2len:
                return 0
            else:
                return -1
        elif i == s2len:
            return 1
    return custom_char_cmp(str1[i], str2[i])


def custom_alphabet_book_title_cmp(str1, str2):  # pylint: disable=R0911
    """custom compare book_title fields"""
    book_title1 = str1["book_title"]
    book_title2 = str2["book_title"]
    return custom_alphabet_cmp(book_title1, book_title2)


def custom_alphabet_name_cmp(str1, str2):  # pylint: disable=R0911
    """custom compare name fields"""
    name1 = str1["name"]
    name2 = str2["name"]
    return custom_alphabet_cmp(name1, name2)


def genres_to_meta_init():
    """load genres info from file"""
    with open('genres.list', encoding="utf-8") as lst:
        while True:
            line = lst.readline()
            if not line:
                break
            genre_line = line.strip('\n').split('|')
            if len(genre_line) > 1:
                genres[genre_line[1]] = {"descr": genre_line[2], "meta_id": genre_line[0]}


def get_genre_name(gen_id):
    """return genre name by id"""
    if gen_id in genres:
        return genres[gen_id]["descr"]
    return gen_id


def meta_init():
    """load genres meta info from file"""
    with open('genres_meta.list', encoding="utf-8") as lst:
        while True:
            line = lst.readline()
            if not line:
                break
            genre_line = line.strip('\n').split('|')
            if len(genre_line) > 1:
                genres_meta[genre_line[0]] = genre_line[1]


def get_meta_name(meta_id):
    """return genres meta name by id"""
    if meta_id in genres_meta:
        return genres_meta[meta_id]
    return meta_id


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
    """make authors data for writing"""
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
        if "id" in seq and seq["id"] is not None and "name" in seq and seq["name"] is not None:
            seqs_tmp[seq["id"]] = seq["name"]
            seq_ids_tmp.append(seq["id"])
    new_seq_ids = get_exist_seqs(seq_ids_tmp)
    for seq_id in seq_ids_tmp:
        if seq_id not in new_seq_ids:
            seqs[seq_id] = seqs_tmp[seq_id]
    return seqs


def make_seqs_db(seqs):
    """make sequences data for writing"""
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
    """make genres data for writing"""
    ret = []
    for genre in genre_ids:
        if genre is not None and genre_ids[genre] is not None:
            if genre in genres:  # ToDo: remove checking after wrong genre replacement
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
                    if "id" in seq and seq["id"] is not None:
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


def open_booklist(booklist):
    """return file object of booklist (.zip.list or .zip.list.gz)"""
    if booklist.find('gz') >= len(booklist) - 3:  # pylint: disable=R1705
        return gzip.open(booklist)
    else:
        return open(booklist, encoding="utf-8")


def seqs_in_data(data):
    """return [{"name": "...", "id": "...", "cnt": 1}, ...]"""
    ret = []
    seq_idx = {}
    for book in data:
        if book["sequences"] is not None:
            for seq in book["sequences"]:
                seq_id = seq.get("id")
                if seq_id is not None:
                    seq_name = seq["name"]
                    if seq_id in seq_idx:
                        s = seq_idx[seq_id]
                        count = s["cnt"]
                        count = count + 1
                        s["cnt"] = count
                        seq_idx[seq_id] = s
                    else:
                        s = {"name": seq_name, "id": seq_id, "cnt": 1}
                        seq_idx[seq_id] = s
    for seq in seq_idx:
        ret.append(seq_idx[seq])
    return ret


def nonseq_from_data(data):
    """return books_id[] without sequences"""
    ret = []
    for book in data:
        if book["sequences"] is None:
            book_id = book["book_id"]
            ret.append(book_id)
    return ret


def refine_book(book):
    """strip images and refine some other data from books info"""
    if "genres" not in book or book["genres"] in (None, "", []):
        book["genres"] = ["other"]
    # ToDo: reimplement this:
    # book["genres"] = db.genres_replace(book, book["genres"])
    # book["lang"] = db.lang_replace(book, book["lang"])
    if "cover" in book:
        del book["cover"]
    if "authors" not in book:
        author = [
            {
                "name": CONFIG['AUTHOR_PLACEHOLDER'],
                "id": make_id(CONFIG['AUTHOR_PLACEHOLDER'])
            }
        ]
        book["authors"] = author
    return book


def decode_b64(data):
    """decode base64 data with light corruption"""
    try:
        return base64.b64decode(data)
    except Exception as e:
        logging.debug("bare image error: %s", e)
        # can't decode as is - pad and try again
        padding_len = len(data) % 4
        if padding_len != 0:
            data_padded = data + '=' * (4 - padding_len)
        else:
            data_padded = data
        try:
            return base64.b64decode(data_padded)
        except Exception as e:
            logging.debug("padded image error: %s", e)
            # can't decode even padded - try take partial decode
            for i in range(1, 5):
                try:
                    return base64.b64decode(data[:len(data) - i])
                except Exception as e:
                    logging.debug("truncated image pass %d error: %s", i, e)
                    pass
            return base64.b64decode(data[:len(data) - 6])


def url_str(string: str):
    """urlencode string (quote + replace some characters to %NN)"""
    transl = {
        '"': '%22',
        "'": '%27',
        # '.': '%2E',
        # '/': '%2F'
    }
    ret = ''
    if string is not None:
        for char in string:
            if char in transl:  # pylint: disable=R1715
                # pylint take here wrong warning
                char = transl[char]
            ret = ret + char
    return urllib.parse.quote(ret, encoding='utf-8')


def html_refine(txt: str):
    """refine html by beautiful soap"""
    html = BeautifulSoup(txt, 'html.parser')
    ret = html.prettify()
    return ret


# 123456 -> 123k, 1234567 -> 1.23M
def sizeof_fmt(num: int, suffix="B"):
    """format size to human-readable format"""
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def is_auth(user, password):
    """
    check user:pass in zips_path/passwd
    """
    import os
    passwd_path = os.path.join(CONFIG["ZIPS"], "passwd")
    try:
        with open(passwd_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line:  # пропускаем пустые строки
                    continue
                if line.lstrip().startswith("#"):  # туда же комменты
                    continue
                try:
                    u, p = line.split(":", 1)
                except ValueError:
                    continue  # невалидная строка
                if u == user and p == password:
                    return True
        return False
    except FileNotFoundError:
        # при отсутствии файла -- режим без авторизации
        return True


def get_vector(text: str):
    """get text and return vector"""
    ret = None
    if text is None or len(text.strip()) < 1:
        return ret
    client = openai.OpenAI(base_url=CONFIG["OPENAI_URL"], api_key=CONFIG["OPENAI_KEY"])
    response = client.embeddings.create(
        model=CONFIG["OPENAI_MODEL"],
        input=text,
        dimensions=VECTOR_SIZE
    )
    ret = response.data[0].embedding
    return ret


def get_books_textinfo(session, bookids):
    """return dict for: book_id: {BookDescription named fields dict}"""
    ret = {}
    descr_data = session.query(BookDescription).filter(BookDescription.book_id.in_(bookids)).all()
    other_data = session.query(Book).filter(Book.book_id.in_(bookids)).all()
    for b in descr_data:
        book_id = b.book_id
        ret[book_id] = {
            "book_id": b.book_id,
            "book_title": b.book_title,
            "annotation": b.annotation
        }
    for b in other_data:
        book_id = b.book_id
        book_genres = []
        for g in b.genres:
            gen_name = get_genre_name(g)
            book_genres.append(gen_name)
        book_data = ret[book_id]
        book_data["genres"] = ", ".join(book_genres)
        ret[book_id] = book_data
    return ret


def get_count(session, obj):
    """return count of obj in database"""
    return session.query(obj).count()


def make_anno_vectors(session, book_ids):
    """return data for dbwrite for vector table with type == book annotation"""
    ret = []
    descr = get_books_textinfo(session, book_ids)
    # disable debug logs for openai internals
    logging.getLogger("openai").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("httpcore").setLevel(logging.ERROR)

    vect_cnt = 0
    for book_id in descr:
        try:
            txt = []
            for s in [descr[book_id]["book_title"], descr[book_id]["genres"], descr[book_id]["annotation"]]:
                if s is not None and len(s) >= 1:
                    txt.append(s)
            vector = None
            if len(txt) > 0:
                text = "\n".join(txt)
                vector = get_vector(text)
            is_bad = False
            if vector is None:
                is_bad = True
            else:
                vect_cnt = vect_cnt + 1
            ret.append(
                VectorsData(
                    id=book_id,
                    type=VectorType.BOOK_ANNO,
                    is_bad=is_bad,
                    embedding=vector
                )
            )
        except Exception as ex:
            logging.error("ERR: Make descr vectors at book_id %s: %s", book_id, ex)
    return ret, vect_cnt
