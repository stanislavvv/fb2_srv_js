#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prepare fb2 books metadata in .zips for opds interface"""

import logging
import argparse
import sys

from app.config import read_config, CONFIG
from app.zips import renew_lists, new_lists
from app.db import dbtables, dbclean
from app.db_fill import process_booklists_db
from app.files_fill import (
    make_book_struct,
    make_authorsindex,
    make_sequencesindex,
    make_genresindex
)

CONFIG_FILE = "./config.ini"


def parse_arguments():
    """argument parser func"""
    parser = argparse.ArgumentParser(description="fb2 in zips processing")
    parser.add_argument('-c', '--config', type=str, default=CONFIG_FILE,
                        help=f'config filename (default: {CONFIG_FILE})')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    lists_parser = subparsers.add_parser('lists',
                                         help='[re]create all .zip.list')
    lists_parser.description = '[re]create all .zip.list'

    new_lists_parser = subparsers.add_parser('new_lists',
                                             help='[re]create .zip.list for only new/refreshed .zip')
    new_lists_parser.description = '[re]create .zip.list for only new/refreshed .zip'

    clean_db_parser = subparsers.add_parser('cleandb', help='Clean database tables and other if need')
    clean_db_parser.description = 'Clean database tables and other if need'

    make_db_parser = subparsers.add_parser('tables', help='Create database tables and other if need')
    make_db_parser.description = 'Create database tables and other if need'

    # fillall_db_parser = subparsers.add_parser('fillall', help='Fill all .zip.list to database, update if exists')
    # fillall_db_parser.description = 'Fill all .zip.list to database, update if exists'

    fillonly_db_parser = subparsers.add_parser('fillonly', help='Fill all .zip.list to database, update if exists')
    fillonly_db_parser.description = 'Fill all .zip.list to database, skip if exists'

    cover_parser = subparsers.add_parser('books', help='Make static data for books/covers')
    cover_parser.description = 'Make static data for book/covers'

    authindex_parser = subparsers.add_parser('authors', help='Make static json struct for authors')
    authindex_parser.description = 'Make static json struct for authors'

    seqindex_parser = subparsers.add_parser('sequences', help='Make static json struct for sequences')
    seqindex_parser.description = 'Make static json struct for sequences'

    genindex_parser = subparsers.add_parser('genres', help='Make static json struct for genres')
    genindex_parser.description = 'Make static json struct for genres'

    allindex_parser = subparsers.add_parser(
        'all',
        help='Run new_lists fillonly books authors sequences genres sequentially'
    )
    allindex_parser.description = 'Run new_lists fillonly books authors sequences genres sequentially'

    pargs = parser.parse_args()
    return pargs


if __name__ == "__main__":
    args = parse_arguments()

    read_config(args.config)

    if CONFIG['DEBUG'] == 'yes' or CONFIG['DEBUG'] is True:
        DBLOGLEVEL = logging.DEBUG  # DEBUG, INFO, WARN, ERR
    else:
        DBLOGLEVEL = logging.INFO  # INFO, WARN, ERR
    DBLOGFORMAT = '%(asctime)s -- %(message)s'
    logging.basicConfig(level=DBLOGLEVEL, format=DBLOGFORMAT)

    if args.command == 'lists':
        renew_lists()
    elif args.command == 'new_lists':
        new_lists()
    elif args.command == 'tables':
        dbtables()
    elif args.command == 'cleandb':
        dbclean()
    elif args.command == 'fillonly':
        process_booklists_db()
    elif args.command == 'authors':
        make_authorsindex()
    elif args.command == 'books':
        make_book_struct()
    elif args.command == 'sequences':
        make_sequencesindex()
    elif args.command == 'genres':
        make_genresindex()
    elif args.command == 'all':
        new_lists()
        dbtables()
        process_booklists_db()
        make_book_struct()
        make_authorsindex()
        make_sequencesindex()
        make_genresindex()
    else:
        print("-h or --help for help")
        sys.exit(1)
