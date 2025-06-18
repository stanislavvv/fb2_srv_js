# -*- coding: utf-8 -*-
"""string manipulations"""

import logging
import unicodedata as ud
import hashlib


def strip_quotes(s: str) -> str:
    """
    '"word word"' -> 'word word'
    '"word" word' -> '"word" word'
    '"word" "word"' -> '"word" "word"'
    """
    if s is None:
        return None
    s = s.strip()

    internal_quotes = False
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        inner_part = s[1:-1].strip()
        if '"' in inner_part:
            internal_quotes = True
    if internal_quotes:
        return s
    return s.strip('"')


def unicode_upper(string: str) -> str:
    """custom UPPER + normalize for sqlite and other"""
    ret = ud.normalize('NFKD', string)
    ret = ret.upper()
    ret = ret.replace('Ё', 'Е')
    ret = ret.replace('Й', 'И')
    ret = ret.replace('Ъ', 'Ь')
    return ret
    # upper_str = ud.normalize('NFKD', string).upper()
    # ret = ''.join(
    #     char for char in upper_str
    #     if ud.category(char) == 'Ll' or ud.category(char) == 'Lu'
    # )
    # return ret


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


def id2path(id: str):  # pylint: disable=W0622
    """1a2b3c.... to 1a/2b/1a2b3c..."""
    first = id[:2]
    second = id[2:4]
    return first + "/" + second + "/" + id


def id2pathonly(id: str):  # pylint: disable=W0622
    """1a2b3c.... to 1a/2b"""
    first = id[:2]
    second = id[2:4]
    return first + "/" + second


def string2filename(data: str) -> str:
    """remove fs-dangerous characters from data"""
    if not data:
        data = "-"
    data = data.replace('/', '⧸')
    data = data.replace('.', '_')
    return data


def make_id(name) -> str:
    """get name, strip quotes from begin/end, return md5"""
    name_str = "--- unknown ---"
    if name is not None and name != "":
        if isinstance(name, str):
            name_str = str(name).strip("'").strip('"')
        else:
            name_str = str(name, encoding='utf-8').strip("'").strip('"')
    norm_name = str_normalize(name_str)
    return hashlib.md5(norm_name.encode('utf-8').upper()).hexdigest()


def str_normalize(string: str) -> str:
    """will be normalize string for make_id and compare"""
    ret = unicode_upper(string.strip())
    return ret
