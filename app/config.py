# -*- coding: utf-8 -*-
"""Config file loading"""

# pylint: disable=C0103,W0718

import os
import sys
import configparser

# translate var names from config to internal/flask
VARS = {
    "debug": "DEBUG",  # yes|no -- enable some debug logs
    "app_root": "APPLICATION_ROOT",  # url path like '/books'
    "hide_deleted": "HIDE_DELETED",  # yes|no -- will skip deleted when indexing
    "page_size": "PAGE_SIZE",  # web page size
    "pages_path": "PAGES",  # filesystem full path to static data
    "pg_base": "PG_BASE",  # postgres db name
    "pg_host": "PG_HOST",  # postgres host
    "pg_pass": "PG_PASS",  # postgres password
    "pg_user": "PG_USER",  # postgres username
    "listen_port": "LISTEN_PORT",  # ex: "8000"
    "listen_host": "LISTEN_HOST",  # ex: "0.0.0.0"
    "pic_width": "PIC_WIDTH",  # max width for cover previews (see 'datachew.sh cover' command)
    "search_result_limit": "MAX_SEARCH_RES",  # max search page size
    "web_title": "TITLE",  # web interface title
    "inpx_file": "INPX",  # archive with .inp files, create empty .zip if not exists
    "zips_path": "ZIPS",  # filesystem full path to .zip's with .fb2 content
    "max_pass_lenth": "MAX_PASS_LENGTH",  # memory limit param, default see below
    "mas_genre_pass_length": "MAX_PASS_LENGTH_GEN",  # memory limit param, default see below
    "books_pass_size_hint": "PASS_SIZE_HINT",  # memory limit param, default see below
    "default_cover_image": "DEFAULT_COVER",  # path to default cover
    "static_file_cache_seconds": "CACHE_TIME_ST"  # static file cache time, seconds
}

CONFIG = {  # default values
    "LISTEN_HOST": "0.0.0.0",
    "LISTEN_PORT": "8000",
    "AUTHOR_PLACEHOLDER": "Автор Неизвестен",
    "MAX_PASS_LENGTH": "4000",  # default for orange pi
    "MAX_PASS_LENGTH_GEN": "5",  # default for orange pi
    "PASS_SIZE_HINT": "1048576",  # default for orange pi
    "DEFAULT_COVER": "/covers/default-cover.jpg",
    "CACHE_TIME_ST": "2592000",  # 60 * 60 * 24 * 30 == 30 days
}


def read_config(conf: str):
    """Read config from file"""
    try:
        app_env = os.environ.get('APP_ENV')
        if app_env is None:
            app_env = 'development'
        cn = configparser.ConfigParser()
        cn.read(conf)
        common = cn['common']
        for k in common.keys():
            if k in VARS:
                CONFIG[VARS[k]] = common[k]
        current = cn[app_env]
        for k in current.keys():
            if k in VARS:
                CONFIG[VARS[k]] = current[k]
    except Exception as ex:
        sys.stderr.write("Exception by: ", str(ex))
        sys.exit(1)
