# -*- coding: utf-8 -*-

import os
import configparser

# translate var names from config to internal
VARS = {
  "debug": "DEBUG",
  "app_root": "APPLICATION_ROOT",
  "hide_deleted": "HIDE_DELETED",
  "page_size": "PAGE_SIZE",
  "pages_path": "PAGES",
  "pg_base": "PG_BASE",
  "pg_host": "PG_HOST",
  "pg_pass": "PG_PASS",
  "pg_user": "PG_USER",
  "listen_port": "LISTEN_PORT",
  "listen_host": "LISTEN_HOST",
  "pic_width": "PIC_WIDTH",
  "search_result_limit": "MAX_SEARCH_RES",
  "web_title": "TITLE",
  "inpx_file": "INPX",
  "zips_path": "ZIPS"
}

CONFIG = {  # default values
  "LISTEN_HOST": "0.0.0.0",
  "LISTEN_PORT": "8000"
}

def read_config(conf: str):
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
    print("Exception by:", str(ex))
    exit(1)

