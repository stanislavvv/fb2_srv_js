# -*- coding: utf-8 -*-
"""get data from .ipx file in .zip"""

import zipfile
import os
import logging

# pylint: disable=relative-beyond-top-level
from .strings import strip_quotes, num2int


def array_strip_empty(arr):
    """cleanup empty strings from array of strings"""
    ret = []
    for elem in arr:
        if elem is not None:
            if isinstance(elem, str):
                if elem != "":
                    ret.append(elem)
            else:
                ret.append(elem)
    return ret


def authors2fields(authors):
    """authors names from strings[] to struct[]"""
    ret = []
    for auth in authors:
        auth_arr = strip_quotes(auth).split(',')
        if len(auth_arr) >= 4:
            ret.append(
                {
                    "last-name": auth_arr[0],
                    "first-name": auth_arr[1],
                    "middle-name": auth_arr[2],
                    "nick-name": auth_arr[3]
                }
            )
        elif len(auth_arr) == 3:
            ret.append(
                {
                    "last-name": auth_arr[0],
                    "first-name": auth_arr[1],
                    "middle-name": auth_arr[2]
                }
            )
        elif len(auth_arr) == 2:
            ret.append(
                {
                    "last-name": auth_arr[0],
                    "first-name": auth_arr[1]
                }
            )
        else:
            ret.append(
                {
                    "last-name": auth_arr[0]
                }
            )
    return ret


def get_line_fields(line: str):
    """get file data from .inpx line

    Fields in record:
    0. AUTHOR
    1. GENRE
    2. TITLE
    3. SERIES
    4. SERNO
    5. FILE
    6. SIZE
    7. LIBID
    8. DEL        # 0|1
    9. EXT        # .fb2
    10. DATE
    11. LANG      # ru
    12. LIBRATE
    13. KEYWORDS
    """
    ret = {}
    line_arr = line.strip("\r").split("\004")
    if len(line_arr) >= 11:  # pylint: disable=R1705
        ret["author"] = authors2fields(
            array_strip_empty(line_arr[0].split(":"))
        )
        ret["genre"] = array_strip_empty(line_arr[1].split(":"))
        ret["book-title"] = line_arr[2]
        context = "get inpx data for '" + str(line_arr[5]) + ".fb2'"
        if len(line_arr[3]) > 2:
            if line_arr[4] is not None and line_arr[4] != '' and num2int(line_arr[4], context) >= 0:
                ret["sequence"] = {"@name": line_arr[3], "@number": line_arr[4]}
            else:
                ret["sequence"] = {"@name": line_arr[3]}
        try:
            ret["deleted"] = int(line_arr[8])
        except ValueError as ex:
            logging.warning(
                "WARN: can't get deleted status for '%s.%s', set it to 0",
                line_arr[5], line_arr[9]
            )
            logging.warning(
                "WARN: raw deleted status for '%s.%s': >%s<",
                line_arr[5], line_arr[9], str(line_arr[8])
            )
            logging.debug("Exception: %s", ex)
            ret["deleted"] = 0
        ret["date_time"] = line_arr[10] + "_00:00"
        ret["lang"] = line_arr[11]
        return line_arr[5] + "." + line_arr[9], ret
    else:
        return None, None


def get_inpx_meta(inpx_data, zip_file):
    """retrieve data from entire .inpx file"""
    ret = {}
    inp_file = os.path.basename(zip_file).replace(".zip", ".inp")

    try:
        # pylint: disable=R1732
        inpx_zip = zipfile.ZipFile(inpx_data)
        f_inpx = inpx_zip.open(inp_file, "r")
        data = f_inpx.read().decode('utf-8')
        lines = data.split("\n")
        for line in lines:
            fb2, meta = get_line_fields(line)
            ret.update({fb2: meta})
            line = f_inpx.readline().decode('utf-8').strip("\r").strip("\n")
        f_inpx.close()
    except Exception as ex:  # pylint: disable=W0703
        logging.exception(
            "Error in getting metadata: %s for file: %s",
            str(ex),
            os.path.basename(zip_file)
        )
    return ret
