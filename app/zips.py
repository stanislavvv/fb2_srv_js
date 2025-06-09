# -*- coding: utf-8 -*-
""".zip file processing"""

import logging
import zipfile
import glob
import os
import sys
import json

from .config import CONFIG
from .inpx import get_inpx_meta
from .fb2int import fb2parse


def get_replace_list(zip_file: str):
    """return None or struct from .zip.replace"""
    ret = None
    replace_list = zip_file + ".replace"
    if os.path.isfile(replace_list):
        try:
            with open(replace_list, encoding="utf-8") as rlist:
                ret = json.load(rlist)
        except Exception as ex:  # pylint: disable=W0703
            # used error() because error in file data, not in program
            logging.error("Can't load json from '%s': %s", replace_list, str(ex))
    return ret


def list_zip(zip_file):
    """return list of files in zip_file"""
    ret = []
    z_file = zipfile.ZipFile(zip_file)  # pylint: disable=R1732
    for filename in z_file.namelist():
        if not os.path.isdir(filename):
            ret.append(filename)
    return ret


def create_booklist(inpx_data, zip_file) -> None:  # pylint: disable=C0103
    """(re)create .list from .zip"""

    booklist = zip_file + ".list"
    booklistgz = zip_file + ".list.gz"
    if os.path.exists(booklistgz):
        os.remove(booklistgz)  # fix simultaneous .list and .list.gz
    try:
        with open(booklist, 'w', encoding='utf-8') as blist:
            files = list_zip(zip_file)
            z_file = zipfile.ZipFile(zip_file)  # pylint: disable=R1732
            inpx_meta = get_inpx_meta(inpx_data, zip_file)
            replace_data = get_replace_list(zip_file)

            for filename in files:
                logging.debug("%s/%s            ", zip_file, filename)
                _, book = fb2parse(z_file, filename, replace_data, inpx_meta)
                if book is None:
                    continue
                blist.write(json.dumps(book, ensure_ascii=False))  # jsonl in blist
                blist.write("\n")
    except Exception as ex:  # pylint: disable=W0703
        logging.error("error processing zip_file: %s", ex)
        logging.info("removing %s", booklist)
        os.remove(booklist)
        sys.exit(1)
    except KeyboardInterrupt as ex:  # Ctrl-C
        logging.error("error processing zip_file: %s", ex)
        logging.info("removing %s", booklist)
        os.remove(booklist)
        sys.exit(1)


def update_booklist(inpx_data, zip_file) -> bool:  # pylint: disable=C0103
    """(re)create .list for new or updated .zip"""

    booklist = zip_file + ".list"
    booklistgz = zip_file + ".list.gz"
    replacelist = zip_file + ".replace"
    if os.path.exists(booklist):
        ziptime = os.path.getmtime(zip_file)
        listtime = os.path.getmtime(booklist)
        replacetime = 0
        if os.path.exists(replacelist):
            replacetime = os.path.getmtime(replacelist)
        if ziptime < listtime and replacetime < listtime:
            return False
    elif os.path.exists(booklistgz):
        ziptime = os.path.getmtime(zip_file)
        listtime = os.path.getmtime(booklistgz)
        replacetime = 0
        if os.path.exists(replacelist):
            replacetime = os.path.getmtime(replacelist)
        if ziptime < listtime and replacetime < listtime:
            return False
        os.remove(booklistgz)  # remove outdated .list.gz, because it is not .list
    create_booklist(inpx_data, zip_file)
    return True


def renew_lists():
    """recreate all .list's from .zip's"""
    zipdir = CONFIG['ZIPS']
    inpx_data = zipdir + "/" + CONFIG['INPX']
    i = 0
    for zip_file in sorted(glob.glob(zipdir + '/*.zip')):
        i += 1
        logging.info("[%s] %s", (str(i)), zip_file)
        create_booklist(inpx_data, zip_file)
    logging.info("[end]")


def new_lists():
    """create .list's for new or updated .zip's"""
    zipdir = CONFIG['ZIPS']
    inpx_data = zipdir + "/" + CONFIG['INPX']
    i = 0
    for zip_file in sorted(glob.glob(zipdir + '/*.zip')):
        i += 1
        logging.info("[%s] %s", (str(i)), zip_file)
        update_booklist(inpx_data, zip_file)
    logging.info("[end]")
