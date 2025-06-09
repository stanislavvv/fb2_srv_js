#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prepare fb2 books metadata in .zips for opds interface"""

import logging
import argparse


from app.config import read_config
from app.zips import renew_lists, new_lists

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
