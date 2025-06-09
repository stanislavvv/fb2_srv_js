# -*- coding: utf-8 -*-
"""string manipulations"""

import logging
import unicodedata as ud


def strip_quotes(string: str) -> str:
    """
    '"word word"' -> 'word word'
    '"word" word' -> '`word` word'
    """
    if string is None:
        return None
    if string.startswith('"') and string.endswith('"'):
        string = string[1:-1]
    return string.replace('"', '`')


def unicode_upper(string: str) -> str:
    """custom UPPER + normalize for sqlite and other"""
    ret = ud.normalize('NFKD', string)
    ret = ret.upper()
    ret = ret.replace('Ё', 'Е')
    ret = ret.replace('Й', 'И')
    ret = ret.replace('Ъ', 'Ь')
    return ret


def strlist(string) -> str:
    """return string or first element of list"""
    if isinstance(string, str):
        return strnull(string)
    if isinstance(string, list):
        if string:
            return strnull(string[0])
        return strnull("")  # empty list
    return strnull(str(string))


def strnull(string) -> str:
    """return empty string if None, else return content"""
    if string is None:
        return ""
    return str(string)


def num2int(num: str, context: str) -> int:
    """number in string or something to integer"""
    try:
        ret = int(num)
        return ret
    # pylint: disable=W0703
    except Exception as ex:  # not exception, but error in data
        logging.error("Error: %s", str(ex))
        logging.error("Context: %s", context)
        return -1
