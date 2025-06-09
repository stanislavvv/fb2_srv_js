#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test app runner, not for production"""

from app import create_app
from app.config import CONFIG

if __name__ == "__main__":
    app = create_app()
    print(app.url_map)
    app.run(host=CONFIG['LISTEN_HOST'], port=CONFIG['LISTEN_PORT'])
