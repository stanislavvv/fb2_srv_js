#!/bin/bash

if [[ -d venv ]]; then
    . venv/bin/activate
fi

BIND="0.0.0.0:8000"
gunicorn -e APP_ENV=production --bind="${BIND}" --timeout=600 --workers=3 'app:create_app()' --access-logfile -
