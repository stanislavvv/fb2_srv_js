# -*- coding: utf-8 -*-
"""external inputs validation"""

import re

id_check = re.compile('([0-9a-f]+)')
zip_check = re.compile('([0-9a-zA-Z_.-]+.zip)')
fb2_check = re.compile('([ 0-9a-zA-ZА-Яа-я_,.:!-]+.fb2)')  # may be incomplete


def validate_prefix(string: str):
    """very simple prefix validation in .../sequenceindes and .../authorsindex"""
    ret = string
    if len(ret) > 10:
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
