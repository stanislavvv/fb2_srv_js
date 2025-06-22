# -*- coding: utf-8 -*-
"""external inputs validation"""

import os
import re

id_check = re.compile('([0-9a-f]+)')
zip_check = re.compile('([0-9a-zA-Z_.-]+.zip)')
fb2_check = re.compile('([ 0-9a-zA-ZА-Яа-я_,.:!-]+.fb2)')  # may be incomplete
genre_check = re.compile('([0-9a-z_]+)')


def safe_path(fspath):
    """create safe relative path from input"""
    if fspath is None:
        return None
    return os.path.relpath(os.path.normpath(os.path.join("/", fspath)), "/")


def validate_prefix(string: str):
    """very simple prefix validation in .../sequenceindes and .../authorsindex"""
    if string is None:
        return None
    ret = safe_path(string)
    if len(ret) > 10 or len(ret) < 1:
        return None
    return ret


def validate_id(string: str):
    """author/book/sequence id validation"""
    ret = string
    if id_check.match(string):
        return ret
    return None


def validate_zip(string: str):
    """zip filename validation"""
    ret = string
    if zip_check.match(string):
        return ret
    return None


def validate_fb2(string: str):
    """fb2 filename validation"""
    ret = string
    if fb2_check.match(string):
        return ret
    return None


def validate_genre(string: str):
    """genre id validation"""
    ret = string
    if genre_check.match(string):
        return ret
    return None
