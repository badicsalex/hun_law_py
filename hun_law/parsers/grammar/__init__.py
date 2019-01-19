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

import os
import hashlib
import tatsu

# TODO, XXX: Ultra hacks. Will not be compatible with installing to /usr/lib
# This module regenerate model.py and parser.py, if necessary.
# We depend on __init__ getting loaded strictly before the modules themselves.

dir_of_this_file = os.path.dirname(__file__)
with open(os.path.join(dir_of_this_file, 'grammar.ebnf')) as f:
    grammar_file_content = f.read()
grammar_file_hash = hashlib.sha256(grammar_file_content.encode('utf-8')).hexdigest()
header_for_generated_files = "# Version of tatsu: {}, SHA256 of grammar file: {}\n".format(tatsu.__version__, grammar_file_hash)

need_regen = False
if not os.path.isfile((os.path.join(dir_of_this_file, 'model.py'))):
    need_regen = True
else:
    with open(os.path.join(dir_of_this_file, 'model.py')) as f:
        if f.readline() != header_for_generated_files:
            need_regen = True

if not os.path.isfile((os.path.join(dir_of_this_file, 'parser.py'))):
    need_regen = True
else:
    with open(os.path.join(dir_of_this_file, 'parser.py')) as f:
        if f.readline() != header_for_generated_files:
            need_regen = True

if need_regen:
    with open(os.path.join(dir_of_this_file, 'model.py'), 'w') as f:
        f.write(header_for_generated_files)
        f.write(tatsu.to_python_model(grammar_file_content))
    with open(os.path.join(dir_of_this_file, 'parser.py'), 'w') as f:
        f.write(header_for_generated_files)
        f.write(tatsu.to_python_sourcecode(grammar_file_content))
