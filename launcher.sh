#!/bin/sh

BASEDIR=$(dirname "$0")
cd "$BASEDIR"
source ./venv/bin/activate
exec python3 __init__.py
