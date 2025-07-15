# -*- coding: utf-8 -*-
"""Config file loading and some internal constants"""

# pylint: disable=C0103,W0718

import os
import sys
import configparser
import lxml.etree as et

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
    "default_cover_source": "DEFAULT_COVER_SRC",  # master-copy of default cover
    "default_cache_seconds": "CACHE_TIME",  # default cache time
    "static_file_cache_seconds": "CACHE_TIME_ST",  # static file cache time, seconds
    "random_cache_seconds": "CACHE_TIME_RND",
    "xslt_file": "FB2_XSLT",  # xslt file for fb2 to html conversion
    "app_ico": "APP_ICO",  # application .ico
}

CONFIG = {  # default values
    "LISTEN_HOST": "0.0.0.0",
    "LISTEN_PORT": "8000",
    "APPLICATION_ROOT": "",
    "AUTHOR_PLACEHOLDER": "Автор Неизвестен",
    "MAX_PASS_LENGTH": "4000",  # default for orange pi
    "MAX_PASS_LENGTH_GEN": "5",  # default for orange pi
    "PASS_SIZE_HINT": "10485760",  # default for orange pi
    "DEFAULT_COVER": "/covers/default.jpg",
    "DEFAULT_COVER_SRC": "./app/static/default-cover.jpg",
    "CACHE_TIME": "604800",  # 60 * 60 * 24 * 7 == 7 days
    "CACHE_TIME_ST": "2592000",  # 60 * 60 * 24 * 30 == 30 days
    "CACHE_TIME_RND": "300",  # 5 min
    "FB2_XSLT": "fb2_to_html.xsl",
    # internal configs
    "REDIR_FROM_ERR": 'root',
    "APP_ICO": "/favicon.ico",  # ToDo: draw it
    "TITLE": "Home OPDS directory",
}

# internal configuration for opds interface
URL = {
    "start": "/opds/",
    "author": "/opds/author/",
    "authidx": "/opds/authorsindex/",
    "seq": "/opds/sequence/",
    "seqidx": "/opds/sequencesindex/",
    "genre": "/opds/genre/",
    "genidx": "/opds/genresindex/",
    "search": "/opds/search",  # main search page, no last '/' in search
    "srchauth": "/opds/search/authors",
    "srchseq": "/opds/search/sequences",
    "srchbook": "/opds/search/books",
    "srchbookanno": "/opds/search/booksanno",
    "rndbook": "/opds/random-books/",
    "rndseq": "/opds/random-sequences/",
    "rndgen": "/opds/rnd/genre/",
    "rndgenidx": "/opds/rnd/genresindex/",
    "time": "/opds/time",  # all books by time (from new to old)
    "read": "/read/",  # read book
    "dl": "/fb2/",  # download book
    "cover": "/covers/",  # books cover images
}

# interface strings
LANG = {
    "title_time": "По дате поступления",
    "title_authors": "По авторам",
    "title_sequences": "По сериям",
    "title_genres": "По жанрам",
    "title_rnd_books": "Случайные книги",
    "title_rnd_seqs": "Случайные серии",
    "title_rnd_genre": "Случайные книги в жанре",

    "book_dl": "Скачать",
    "book_read": "Читать онлайн",
    "books_num": "%s книг(и)",
    "books_author_alphabet": "Книги автора '%s' по алфавиту",
    "books_author_time": "Книги автора '%s' по времени поступления",
    "books_author_nonseq": "Книги автора '%s' вне серий",
    "books_author_seq": "Серия '%s', автор '%s'",
    "books_alphabet": "По алфавиту",
    "books_time": "По дате добавления",
    "books_nonseq": "Вне серий",
    "books_seq": "По сериям",
    "bookinfo": """
        <p class=\"book\"> %s </p>\n<br/>формат: fb2<br/>
        размер: %s<br/>
    """,
    "bookinfo_seq": """
        <p class=\"book\"> %s </p>\n<br/>формат: fb2<br/>
        размер: %s<br/>Серия: %s, номер: %s<br/>
    """,

    "authors": "Авторы",
    "auth_root_subtitle": "Авторы на ",
    "author": "Автор %s",
    "author_tpl": "Автор '%s'",
    "authors_num": "%s авт.",

    "sequences": "Серии",
    "seq_root_subtitle": "Серии на ",
    "sequence": "Серия ",
    "seq_tpl": "Серия '%s'",
    "seqs_num": "%s сер.",
    "seqs_author": "Серии автора '%s'",

    "pubinfo_isbn": "<p>ISBN: %s</p>",
    "pubinfo_year": "<p>Год публикации: %s</p>",
    "pubinfo_publisher": "<p>Издательство: %s</p>",

    "genres_meta": "Группы жанров",
    "genres": "Жанры",
    "genre": "Жанр ",
    "genres_root_subtitle": "Жанры в группе ",
    "genre_tpl": "Жанр '%s'",

    "search_main": "Поиск по '%s'",
    "schmain_author": "Поиск в именах авторов",
    "schmain_seq": "Поиск в сериях",
    "schmain_book": "Поиск в названиях книг",
    "schmain_anno": "Поиск в аннотациях книг",
    "search_author": "Поиск среди авторов по '%s'",
    "search_seq": "Поиск среди серий по '%s'",
    "search_book": "Поиск по заголовкам книг по '%s'",
    "search_anno": "Поиск по описаниям книг по '%s'",

    "rnd_books": "Случайные книги",
    "rnd_seqs": "Случайные серии",
    "rnd_genre_books": "Случайные книги в жанре '%s'",

    "all_books_by_time": "Все книги по дате поступления"
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


def init_xslt(xsltfile):
    """init xslt data from file"""
    xslt = et.parse(xsltfile)
    transform = et.XSLT(xslt)
    CONFIG['TRANSFORM'] = transform
