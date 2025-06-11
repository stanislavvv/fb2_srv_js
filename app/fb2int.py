# -*- coding: utf-8 -*-
"""Get data from fb2 in zips"""

import os
# import zipfile
import sys
import io
import logging
import base64
import collections
import traceback  # DEBUG

from datetime import datetime
from bs4 import BeautifulSoup
from PIL import Image

import xmltodict

from .strings import strlist, strip_quotes, num2int, make_id
from .config import CONFIG

FB2_HEADER_LIMIT = 20000  # nearly 20kB for metadata text


def get_struct_by_key(key: str, struct):
    """ret substr by key"""
    if key in struct:
        return struct[key]
    if isinstance(struct, list):
        for k in struct:
            ret = get_struct_by_key(key, k)
            if ret is not None:
                return ret
    if isinstance(struct, dict):
        for _, val in struct.items():
            ret = get_struct_by_key(key, val)
            if ret is not None:
                return ret
    return None


def replace_book(filename: str, book, replace_data):
    """get book struct, if exists replacement, replace some fields from it"""
    # filename = book["filename"]
    if filename in replace_data:
        replace = replace_data[filename]
        for key, val in replace.items():
            book[key] = val
    return book


def get_genre(genr):
    """return array of genres from sometimes strange struct"""
    # pylint: disable=C0103,R0912
    ret = []
    if isinstance(genr, dict):
        for _, v in genr.items():
            if isinstance(v, str) and not v.isdigit() and v != "":
                ret.append(v)
            elif isinstance(v, dict):
                for _, v2 in v.items():
                    if not v2.isdigit() and v2 != "":
                        ret.append(v2)
            elif isinstance(v, list):
                for v2 in v:
                    if not v2.isdigit() and v2 != "":
                        ret.append(v2)
    elif isinstance(genr, list):
        for i in genr:
            if isinstance(i, str) and not i.isdigit() and i != "":
                ret.append(i)
            elif isinstance(i, dict):
                for _, v in i.items():
                    if not v.isdigit() and v != "":
                        ret.append(v)
            elif isinstance(i, list):
                for v in i:
                    if not v.isdigit() and v != "":
                        ret.append(v)
    else:
        ret.append(genr)
    return ret


def get_sequence(seq, zip_file: str, filename: str):
    """
    return struct: [{"name": "SomeName", "id": "id...", num: 3}, ...]
    for sequence(s) in data
    """
    # pylint: disable=R0912,C0209
    ret = []
    context = "get seq for file '%s/%s'" % (zip_file, filename)
    if isinstance(seq, str):
        seq_id = make_id(seq)
        ret.append({"name": seq, "id": seq_id})
    elif isinstance(seq, dict):
        name = None
        num = None
        if '@name' in seq:
            name = strip_quotes(seq['@name'].strip('|').replace('«', '"').replace('»', '"'))
            name = name.strip()
            seq_id = make_id(name)
            if name == "":
                name = None
        if '@number' in seq:
            num = seq['@number']
        if name is not None and num is not None:
            ret.append({"name": name, "id": seq_id, "num": num2int(num, context)})
        elif name is not None:
            ret.append({"name": name, "id": seq_id})
        elif num is not None:
            if num.find('« name=»') != -1:
                name = num.replace('« name=»', '')
                seq_id = make_id(name)
                ret.append({"name": name, "id": seq_id})
            else:
                ret.append({"num": num2int(num, context)})
    elif isinstance(seq, list):
        for single_seq in seq:
            name = None
            num = None
            if '@name' in single_seq:
                name = strip_quotes(
                    single_seq['@name'].strip('|').replace('«', '"').replace('»', '"')
                )
                name = name.strip()
                seq_id = make_id(name)
            if '@number' in single_seq:
                num = single_seq['@number']
            if name is not None and num is not None:
                ret.append({"name": name, "id": seq_id, "num": num2int(num, context)})
            elif name is not None:
                ret.append({"name": name, "id": seq_id})
            elif num is not None:
                if num.find('« name=»') != -1:
                    name = num.replace('« name=»', '')
                    seq_id = make_id(name)
                    ret.append({"name": name, "id": seq_id})
                else:
                    ret.append({"num": num2int(num, context)})
    else:
        ret.append(str(seq))
    return ret


def get_author_struct(author):
    """return [{"name": "Name", "id": "id"}, ...] for author(s)"""
    # pylint: disable=R0912
    ret = [{"name": '--- unknown ---', "id": make_id('--- unknown ---')}]  # default
    aret = []
    if isinstance(author, list):
        for i in author:
            a_tmp = []
            if i is not None:
                if 'last-name' in i and i['last-name'] is not None:
                    a_tmp.append(strlist(i['last-name']))
                if 'first-name' in i and i['first-name'] is not None:
                    a_tmp.append(strlist(i['first-name']))
                if 'middle-name' in i and i['middle-name'] is not None:
                    a_tmp.append(strlist(i['middle-name']))
                if 'nickname' in i and i['nickname'] is not None:
                    if len(a_tmp) > 0:
                        a_tmp.append('(' + strlist(i['nickname']) + ')')
                    else:
                        a_tmp.append(strlist(i['nickname']))
                a_tmp2 = " ".join(a_tmp)
                a_tmp2 = strip_quotes(a_tmp2).strip('|')
                a_tmp2 = a_tmp2.strip()
                if len(a_tmp2) > 0:
                    aret.append({"name": a_tmp2, "id": make_id(a_tmp2.ljust(4))})
        if len(aret) > 0:
            ret = aret
    else:
        a_tmp = []
        if author is not None:
            if 'last-name' in author and author['last-name'] is not None:
                a_tmp.append(strlist(author['last-name']))
            if 'first-name' in author and author['first-name'] is not None:
                a_tmp.append(strlist(author['first-name']))
            if 'middle-name' in author and author['middle-name'] is not None:
                a_tmp.append(strlist(author['middle-name']))
            if 'nickname' in author and author['nickname'] is not None:
                if len(a_tmp) > 0:
                    a_tmp.append('(' + strlist(author['nickname']) + ')')
                else:
                    a_tmp.append(strlist(author['nickname']))
        aret = " ".join(a_tmp)
        aret = strip_quotes(aret).strip('|')
        aret = aret.strip()
        if len(aret) > 0:
            ret = [{"name": aret, "id": make_id(aret.ljust(4))}]
    return ret


def get_title(title) -> str:
    """get stripped title from struct"""
    if isinstance(title, str):
        return title.replace('«', '"').replace('»', '"')
    if isinstance(title, dict):
        if '#text' in title:
            return str(title["#text"]).replace('«', '"').replace('»', '"')
        if 'p' in title:
            return str(title['p']).replace('«', '"').replace('»', '"')
    return str(title).replace('«', '"').replace('»', '"')


# FixMe: must return array of strings, but it will be HUGE incompartibility
def get_lang(lng) -> str:
    """return lang id(s) string"""
    ret = ""
    rets = {}
    if isinstance(lng, list):
        for i in lng:
            rets[i] = 1
        ret = "|".join(rets)
    else:
        ret = str(lng)
    return ret


def array2string(arr):
    """array of any to string"""
    ret = []
    if arr is None:
        return None  # ashes to ashes dust to dust
    for elem in arr:
        if elem is not None:
            ret.append(str(elem))
    return "".join(ret)


def get_pub_info(pubinfo):
    """get publishing vars from pubinfo"""
    isbn = None
    year = None
    publisher = None
    if pubinfo is not None:
        if isinstance(pubinfo, dict):
            isbn = array2string(pubinfo.get("isbn"))
            if not isinstance(isbn, str):
                isbn = None
            year = array2string(pubinfo.get("year"))
            if isinstance(year, int):
                year = str(year)
            if not isinstance(year, str):
                year = None
            publisher = pubinfo.get("publisher")
            if isinstance(publisher, dict):
                publisher = publisher["#text"]
            if isinstance(publisher, list):
                publisher = array2string(publisher)
        elif isinstance(pubinfo, list):
            for pub in pubinfo:
                tmpisbn, tmpyear, tmppub = get_pub_info(pub)
                if tmpisbn is not None:
                    isbn = tmpisbn
                if tmpyear is not None:
                    year = tmpyear
                if tmppub is not None:
                    publisher = tmppub
    return isbn, year, publisher


def get_image(name: str, binary, last=True, context=None):  # pylint: disable=R0912,R0914
    """
    return {"content-type": "image/jpeg", "data": "<image data in jpeg>"}
    content-type must be correspond for image data format
    """
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.CRITICAL)
    ret = None
    c_type = "image/jpeg"  # default
    if name is not None:
        if isinstance(binary, dict) and '@id' in binary and binary['@id'] == name:
            if '@content-type' in binary:
                c_type = binary['@content-type']
            if '#text' in binary:
                data = binary['#text']
                ret = {
                    "content-type": c_type,
                    "data": data
                }
        elif isinstance(binary, list):
            for item in binary:
                tmp = get_image(name, item, False, context)
                if tmp is not None:
                    ret = tmp
                    break
        elif isinstance(binary, collections.OrderedDict):
            for val in binary.values():
                tmp = get_image(name, val, False, context)
                if tmp is not None:
                    ret = tmp
                    break
    if ret is not None and last is True:
        try:
            # basewidth = 300
            basewidth = int(CONFIG['PIC_WIDTH'])
            buf = io.BytesIO(base64.b64decode(ret["data"] + '=='))  # additinally pad db64
            img = Image.open(buf).convert('RGB')
            wpercent = basewidth/float(img.size[0])
            if wpercent < 1:
                hsize = int((float(img.size[1])*float(wpercent)))
                img = img.resize((basewidth, hsize), Image.LANCZOS)
            buffout = io.BytesIO()
            img.save(buffout, format="JPEG", quality="web_medium")
            data = base64.encodebytes(buffout.getvalue())
            ret["content-type"] = "image/jpeg"
            ret["data"] = data.decode("utf-8")
        except Exception as ex:  # pylint: disable=W0703
            if context is not None:
                logging.error("Image error in: %s", context)
            logging.error(ex)
            logging.debug(traceback.format_exc())
    return ret


def get_fb2data(fb2_fd, zip_file, filename):
    """return FictionBook section from opened file fb2_fd"""
    sys.setrecursionlimit(10000)  # for some strange fb2 with nested <p>
    b_soap = BeautifulSoup(bytes(fb2_fd.read()), 'xml')
    doc = b_soap.prettify()
    xmldata = xmltodict.parse(doc)
    if 'FictionBook' not in xmldata:  # parse with namespace
        xmldata = xmltodict.parse(
            doc,
            process_namespaces=True,
            namespaces={'http://www.gribuser.ru/xml/fictionbook/2.0': None}
        )
    if 'FictionBook' not in xmldata:  # not fb2
        logging.error("not fb2: %s/%s ", zip_file, filename)
        return None, None
    fb2data = get_struct_by_key('FictionBook', xmldata)  # xmldata['FictionBook']
    return fb2data


def fb2parse(z_file, filename, replace_data, inpx_data):  # pylint: disable=R0912,R0914,R0915
    """get filename in opened zip (assume filename format as fb2), return book struct"""

    file_info = z_file.getinfo(filename)
    zip_file = str(os.path.basename(z_file.filename))
    fb2dt = datetime(*file_info.date_time)
    date_time = fb2dt.strftime("%F_%H:%M")
    size = file_info.file_size

    if size < 500:  # too small for real book
        return None, None

    fb2 = z_file.open(filename)
    b_soap = BeautifulSoup(bytes(fb2.read(FB2_HEADER_LIMIT)), 'xml')
    # some data, taken from xml directly, so get_fb2data() can't be used
    bs_descr = b_soap.FictionBook.description
    tinfo = bs_descr.find("title-info")
    bs_anno = str(tinfo.annotation)
    bs_anno = bs_anno.replace("<annotation>", "").replace("</annotation>", "")

    # as in get_fb2data()
    doc = b_soap.prettify()
    data = xmltodict.parse(doc)
    if 'FictionBook' not in data:  # parse with namespace
        data = xmltodict.parse(
            doc,
            process_namespaces=True,
            namespaces={'http://www.gribuser.ru/xml/fictionbook/2.0': None}
        )
    if 'FictionBook' not in data:  # not fb2
        logging.error("not fb2: %s/%s ", zip_file, filename)
        return None, None
    fb2data = get_struct_by_key('FictionBook', data)  # data['FictionBook']
    descr = get_struct_by_key('description', fb2data)  # fb2data['description']
    info = get_struct_by_key('title-info', descr)  # descr['title-info']

    cover = None
    if "coverpage" in info and info["coverpage"] is not None:
        coverpage = info["coverpage"]
        if "image" in coverpage and coverpage["image"] is not None:
            fb2_full = z_file.open(filename)
            fb2data_full = get_fb2data(fb2_full, zip_file, filename)
            covermeta = coverpage["image"]
            covername = None
            if "@l:href" in covermeta:
                covername = covermeta["@l:href"].lstrip('#')
            elif "@xlink:href" in covermeta:
                covername = covermeta["@xlink:href"].lstrip('#')
            else:
                logging.debug(  # debug strange cover info
                    "strange coverpage data in '%s/%s': %s",
                    zip_file,
                    filename,
                    coverpage
                )
            if "binary" in fb2data_full:
                binary = fb2data_full["binary"]  # mostly images here
                cover = get_image(
                    covername,
                    binary,
                    context="%s/%s" % (zip_file, filename)
                )  # get corresponding image
    pubinfo = None
    try:
        pubinfo = get_struct_by_key('publish-info', descr)  # descr['publish-info']
    except Exception as ex:  # pylint: disable=W0703
        # get_struct_by_key must return None without stacktrace
        if len(str(ex)) > 0:  # flake8...
            logging.debug("No publish info in %s/%s", zip_file, filename)
    if isinstance(pubinfo, list):
        pubinfo = pubinfo[0]
    if isinstance(info, list):
        # see f.fb2-513034-516388.zip/513892.fb2
        info = info[0]
    if inpx_data is not None and filename in inpx_data:
        info = replace_book(filename, info, inpx_data)
    if replace_data is not None and filename in replace_data:
        info = replace_book(filename, info, replace_data)

    if "deleted" in info:
        if info["deleted"] != 0:
            logging.debug("%s/%s in deleted status", zip_file, filename)
    else:
        info["deleted"] = 0

    if "date_time" in info and info["date_time"] is not None:
        date_time = str(info["date_time"])
    if 'genre' in info and info['genre'] is not None:
        genre = get_genre(info['genre'])
    else:
        genre = ""
    author = [{"name": '--- unknown ---', "id": make_id('--- unknown ---')}]
    if 'author' in info and info['author'] is not None:
        author = get_author_struct(info['author'])
    sequence = None
    if 'sequence' in info and info['sequence'] is not None:
        sequence = get_sequence(info['sequence'], zip_file, filename)
    book_title = ''
    if 'book-title' in info and info['book-title'] is not None:
        book_title = get_title(info['book-title'])
    lang = ''
    if 'lang' in info and info['lang'] is not None:
        lang = get_lang(info['lang'])
    annotext = ''
    if 'annotation' in info and info['annotation'] is not None:
        annotext = bs_anno

    isbn, pub_year, publisher = get_pub_info(pubinfo)
    pub_info = {
        "isbn": isbn,
        "year": pub_year,
        "publisher": publisher,
        "publisher_id": make_id(publisher)
    }
    book_path = str(os.path.basename(z_file.filename)) + "/" + filename
    book_id = make_id(book_path)
    out = {
        "zipfile": zip_file,
        "filename": filename,
        "genres": genre,
        "authors": author,
        "sequences": sequence,
        "book_title": str(book_title),
        "cover": cover,
        "book_id": book_id,
        "lang": str(lang),
        "date_time": date_time,
        "size": str(size),
        "annotation": str(annotext.replace('\n', " ").replace('|', " ")),
        "pub_info": pub_info,
        "deleted": info["deleted"]
    }
    return book_id, out
