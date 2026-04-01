# -*- coding: utf-8 -*-
"""string manipulations"""

import logging
import unicodedata as ud
import hashlib
import string as str_lib

# Mapping for character replacements (umlauts, special characters)
REPLACEMENT_MAP = {
    # Cyrillic
    'Ё': 'Е', 'Й': 'И', 'Ъ': 'Ь',
    # German umlauts (uppercase)
    'Ä': 'AE', 'Ö': 'OE', 'Ü': 'UE', 'ß': 'SS',
    # Other common replacements (uppercase)
    'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Å': 'A',
    'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
    'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I',
    'Ñ': 'N',
    'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O',
    'Ù': 'U', 'Ú': 'U', 'Û': 'U',
    'Ý': 'Y',
    'Ç': 'C',
    'Þ': 'TH',
    'Đ': 'D',
    'Ł': 'L',
    'Ń': 'N',
    'Ǿ': 'O',
    'Ŕ': 'R',
    'Ś': 'S',
    'Ź': 'Z',
    'Ż': 'Z',
}


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
    # Apply replacements from map
    for old, new in REPLACEMENT_MAP.items():
        ret = ret.replace(old, new)
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
        return -1  # invalid num indicator, valid numbers >=0


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


def make_id(name, name_as_is: bool = False) -> str:
    """get name, strip quotes from begin/end, return md5"""
    name_str = "--- unknown ---"
    if name is not None and name != "":
        if isinstance(name, str):
            name_str = str(name).strip("'").strip('"')
        else:
            name_str = str(name, encoding='utf-8').strip("'").strip('"')
    norm_name = name_str if name_as_is else str_normalize(name_str)
    return hashlib.md5(norm_name.encode('utf-8')).hexdigest()


def str_normalize(string: str) -> str:
    """normalize string for make_id and compare"""
    if not string:
        return ""

    # Strip leading/trailing whitespace
    ret = string.strip()

    # Replace multiple spaces with single space
    while '  ' in ret:
        ret = ret.replace('  ', ' ')

    # Convert to upper case with unicode normalization
    ret = unicode_upper(ret)

    # Remove all punctuation except:
    # - ? and ! (only at the end, 1-4 chars)
    # - parentheses (significant characters)

    # First, collect trailing ? and ! (1-4 chars) from the end
    trailing_punct = ""
    i = len(ret) - 1
    while i >= 0 and len(trailing_punct) < 4 and ret[i] in '?!':
        trailing_punct = ret[i] + trailing_punct
        i -= 1

    # Remove all punctuation except parentheses from the string
    punctuation_to_remove = set(str_lib.punctuation) - {'(', ')'}

    result = []
    for char in ret:
        if char in punctuation_to_remove:
            continue
        result.append(char)

    ret = ''.join(result)

    # Strip multiple spaces again after punctuation removal
    while '  ' in ret:
        ret = ret.replace('  ', ' ')

    # Strip again after removing punctuation
    ret = ret.strip()

    # Add back trailing punctuation if any
    if trailing_punct:
        ret = ret + trailing_punct

    return ret
