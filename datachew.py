#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging


from app.config import read_config, CONFIG
from app.zips import renew_lists, new_lists

CONFIG_FILE="./config.ini"


if __name__ == "__main__":
    # ToDo: args parsing
    read_config(CONFIG_FILE)

    DBLOGLEVEL = logging.DEBUG  # DEBUG, INFO, WARN, ERR
    DBLOGFORMAT = '%(asctime)s -- %(message)s'
    logging.basicConfig(level=DBLOGLEVEL, format=DBLOGFORMAT)
    new_lists()

