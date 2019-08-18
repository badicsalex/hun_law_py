#!/usr/bin/env python3
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

import sys
import os
import traceback
import importlib
import copy
import json
import subprocess

from tempfile import NamedTemporaryFile

from hun_law.extractors.kozlonyok_hu_downloader import KozlonyToDownload
from hun_law.extractors.all import do_extraction
from hun_law.extractors.magyar_kozlony import MagyarKozlonyLawRawText
from hun_law.parsers.structure_parser import ActStructureParser
from hun_law.cache import init_cache
from hun_law.utils import iterate_with_quote_level

import hun_law.fixups.common
import hun_law.fixups.text_fixups
import hun_law.fixups.replacement_fixups


EDITOR = "vim"


def do_file_editing(body):
    with NamedTemporaryFile(mode="w", prefix="hun_law_editor", delete=False) as f:
        first_negative = None
        last_zero = None
        for line_number, (quote_level, l) in enumerate(iterate_with_quote_level(body, throw_exceptions=False)):
            assert l.content.strip() == l.content, "Line content should be stripped, or else we will do it accidentally"
            indentation = " " * int(l.indent*0.2)
            representation = "{:>4} {} {}\n".format(quote_level, indentation, l.content)
            f.write(representation)
            if quote_level < 0 and first_negative is None:
                first_negative = line_number
            if quote_level == 0:
                last_zero = line_number
        tempfile_name = f.name

    if first_negative is not None:
        open_at_line = first_negative
    elif last_zero is not None:
        open_at_line = last_zero
    else:
        open_at_line = 0

    subprocess.run([EDITOR, tempfile_name, "+{}".format(open_at_line + 1)])
    result = []
    with open(tempfile_name, "r") as f:
        for l in f:
            result.append(l[5:].strip())
    os.unlink(tempfile_name)
    return result


def extract_replacements(original_lines, new_lines):
    if len(original_lines) != len(new_lines):
        # TODO: Line insertion  and deletion
        raise ValueError("Can only process modified lines, do not add or remove them.")

    result = []
    for line_num in range(len(new_lines)):
        original_line = original_lines[line_num]
        new_line = new_lines[line_num]
        if original_line == new_line:
            continue
        if original_lines.count(original_line) == 1:
            result.append({"needle": original_line, "replacement": new_line})
            continue

        # Before needle context: this will be already modified, hence the "new_lines"
        if new_lines.count(new_lines[line_num-1]) == 1:
            result.append({
                "needle": original_line,
                "replacement": new_line,
                "needle_prev_lines": [new_lines[line_num-1]]
            })
            continue
        # TODO
        raise ValueError("Super multiline needle not yet supported")
    return result


def save_replacements_and_reload(identifier, replacements):
    new_replacement_fixups = copy.deepcopy(hun_law.fixups.replacement_fixups.replacement_fixups)
    if identifier not in new_replacement_fixups:
        new_replacement_fixups[identifier] = []
    new_replacement_fixups[identifier].extend(replacements)

    with open(hun_law.fixups.replacement_fixups.__file__, "w") as f:
        f.write(
            "# THIS FILE IS GENERATED BY A TOOL. PLEASE DO NOT MODIFY MANUALLY.\n\n"
            "replacement_fixups = "
        )
        json.dump(new_replacement_fixups, f, indent="    ", sort_keys=True, ensure_ascii=False)
        f.write("\n")

    importlib.reload(hun_law.fixups.replacement_fixups)
    importlib.reload(hun_law.fixups.common)
    importlib.reload(hun_law.fixups.text_fixups)


def detect_errors_and_try_fix(raw):
    while True:
        print("Parsing {} {}".format(raw.identifier, raw.subject))
        print("Using {} fixups".format(len(hun_law.fixups.common.all_fixups.get(raw.identifier, []))))
        fixupped_body = hun_law.fixups.common.do_all_fixups(raw.identifier, raw.body)
        try:
            ActStructureParser.parse(raw.identifier, raw.subject, fixupped_body)
            print("Parsing successful")
            break
        except:
            traceback.print_exc()
        if input("Do you want to fix it? (Yes/No, default: Yes)") not in ("", "y", "Y", "yes", "YES", "Yes"):
            break

        edited_body = do_file_editing(fixupped_body)
        replacements = extract_replacements([l.content for l in fixupped_body], edited_body)
        save_replacements_and_reload(raw.identifier, replacements)


init_cache(os.path.join(os.path.dirname(__file__), 'cache'))

extracted = do_extraction(
    [KozlonyToDownload(sys.argv[1], sys.argv[2])],
    end_result_classes=[MagyarKozlonyLawRawText]
)

for e in extracted:
    detect_errors_and_try_fix(e)
