#!/bin/sh
# Copyright 2018 Alex Badics <admin@stickman.hu>
#
# This file is part of Hun-Law.
#
# Hun-Law is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hun-Law is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hun-Law.  If not, see <https://www.gnu.org/licenses/>.

function create_venv(){
    PYTHON_INTERPRETER="$1"
    VENV_PATH="$2"
    "${PYTHON_INTERPRETER}" -m venv "${VENV_PATH}"
    "${VENV_PATH}/bin/pip" install --upgrade pip
    "${VENV_PATH}/bin/pip" install -r requirements.txt
}

create_venv python3 .venv
if ! command -v pypy3 &> /dev/null; then
    echo "WARN: Pypy3 venv not installed. Consider installing pypy3 for 10x faster execution."
else
    create_venv pypy3 .venv-pypy
fi

