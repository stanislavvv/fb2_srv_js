#!/bin/bash

if [[ -d venv ]]; then
    . venv/bin/activate
fi

exec ./opds.py

