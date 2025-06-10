#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prepare fb2 books metadata in .zips for opds interface"""

import logging
import argparse
import sys

from app.config import read_config
from app.zips import renew_lists, new_lists
from app.db import dbtables, dbclean
from app.db_fill import process_booklists_db

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

    make_db_parser = subparsers.add_parser('tables', help='Create database tables and other if need')
    make_db_parser.description = 'Create database tables and other if need'

    clean_db_parser = subparsers.add_parser('cleandb', help='Clean database tables and other if need')
    clean_db_parser.description = 'Clean database tables and other if need'

    fillall_db_parser = subparsers.add_parser('fillall', help='Fill all .zip.list to database, update if exists')
    fillall_db_parser.description = 'Fill all .zip.list to database, update if exists'

    fillonly_db_parser = subparsers.add_parser('fillonly', help='Fill all .zip.list to database, update if exists')
    fillonly_db_parser.description = 'Fill all .zip.list to database, skip if exists'

    pargs = parser.parse_args()
    return pargs


if __name__ == "__main__":
    args = parse_arguments()

    read_config(args.config)

    DBLOGLEVEL = logging.DEBUG  # DEBUG, INFO, WARN, ERR
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
    elif args.command in ('fillonly', 'fillall'):
        process_booklists_db(stage=args.command)
    else:
        print("-h or --help for help")
        sys.exit(1)
