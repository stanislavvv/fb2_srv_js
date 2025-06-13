#!/bin/bash

if [[ -d venv ]]; then
    . venv/bin/activate
fi

./opds.py

