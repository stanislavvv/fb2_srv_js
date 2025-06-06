# -*- coding: utf-8 -*-

from flask import Flask
from .config import read_config, CONFIG

CONFIG_FILE = "./config.ini"


def create_app():
    read_config(CONFIG_FILE)
    app = Flask(__name__)

    # Configure flask with values from CONFIG
    for key, value in CONFIG.items():
        app.config[key] = value

    @app.route('/')
    def hello_world():
        return 'Hello, World!'

    return app
