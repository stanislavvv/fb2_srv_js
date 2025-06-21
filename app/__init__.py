# -*- coding: utf-8 -*-
"""app module"""

from flask import Flask
from .config import read_config, init_xslt, CONFIG

from .view_static import static

CONFIG_FILE = "./config.ini"


def create_app():
    """create flask app"""
    read_config(CONFIG_FILE)
    app = Flask(__name__)

    # Configure flask with values from CONFIG
    for key, value in CONFIG.items():
        app.config[key] = value

    init_xslt(CONFIG['FB2_XSLT'])

    app.register_blueprint(static, url_prefix=app.config['APPLICATION_ROOT'])

    @app.route('/')
    def root():
        return 'Hello, World!'

    return app
