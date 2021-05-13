#!/bin/sh

BASEDIR=$(dirname "$0")
cd "$BASEDIR"
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
