#!/bin/sh
VENV_PATH=.venv
python3 -m venv "${VENV_PATH}"
"${VENV_PATH}/bin/pip" install --upgrade pip
"${VENV_PATH}/bin/pip" install -r requirements.txt

