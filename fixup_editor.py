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
from typing import Iterable, Sequence, Union, List, Dict, Tuple

from tempfile import NamedTemporaryFile

from hun_law.extractors.kozlonyok_hu_downloader import KozlonyToDownload
from hun_law.extractors.all import do_extraction
from hun_law.extractors.magyar_kozlony import MagyarKozlonyLawRawText
from hun_law.parsers.structure_parser import ActStructureParser
from hun_law.parsers.semantic_parser import ActSemanticsParser, ActBlockAmendmentParser
from hun_law.cache import init_cache
from hun_law.utils import iterate_with_quote_level, IndentedLine

import hun_law.fixups.common
import hun_law.fixups.text_fixups
import hun_law.fixups.replacement_fixups


EDITOR = "vim"

FixupType = Dict[str, Union[str, List[str]]]
ReplacementsType = Dict[str, List[FixupType]]


def do_file_editing(body: Iterable[IndentedLine]) -> Tuple[str, ...]:
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

    subprocess.run([EDITOR, tempfile_name, "+{}".format(open_at_line + 1)], check=True)
    with open(tempfile_name, "r") as tempfile_opened_again:
        result = tuple(fl[5:].strip() for fl in tempfile_opened_again)
    os.unlink(tempfile_name)
    return result


def count_sublists(haystack: List[str], needle: List[str]) -> int:
    return sum(1 for i in range(len(haystack) - len(needle)) if haystack[i:i+len(needle)] == needle)


def extract_replacements(original_lines: Sequence[str], new_lines: Sequence[str]) -> Iterable[FixupType]:
    if len(original_lines) != len(new_lines):
        # TODO: Line insertion  and deletion
        raise ValueError("Can only process modified lines, do not add or remove them.")

    result: List[FixupType] = []
    for line_num, (original_line, new_line) in enumerate(zip(original_lines, new_lines)):
        new_line = new_lines[line_num]
        if original_line == new_line:
            continue
        if original_lines.count(original_line) == 1:
            result.append({"needle": original_line, "replacement": new_line})
            continue

        # When doing fixups, this will be the real state of the text.
        simulated_current_lines = list(new_lines[:line_num]) + list(original_lines[line_num:])
        for before_context_len in range(1, 10):
            # The previous lines will already be fixupped at this point
            needle_prev_lines = list(new_lines[line_num-before_context_len:line_num])
            if count_sublists(simulated_current_lines, needle_prev_lines + [original_line]) == 1:
                fixup: FixupType = {
                    "needle": original_line,
                    "replacement": new_line,
                    "needle_prev_lines": needle_prev_lines,
                }
                result.append(fixup)
                break
        else:  # there was no break
            raise ValueError("Huge before context would be needed for replacement")
    return result


def save_replacements_and_reload(identifier: str, replacements: Iterable[FixupType]) -> None:
    new_replacement_fixups = copy.deepcopy(hun_law.fixups.replacement_fixups.replacement_fixups)
    if identifier not in new_replacement_fixups:
        new_replacement_fixups[identifier] = []
    new_replacement_fixups[identifier].extend(replacements)

    with open(hun_law.fixups.replacement_fixups.__file__, "w") as f:
        f.write(
            "# THIS FILE IS GENERATED BY A TOOL. PLEASE DO NOT MODIFY MANUALLY.\n"
            "import typing\n"
            "\n"
            "FixupType = " + repr(FixupType) + "\n"
            "ReplacementsType = " + repr(ReplacementsType) + "\n"
            "\n"
            "replacement_fixups: ReplacementsType = "
        )
        json.dump(new_replacement_fixups, f, indent="    ", sort_keys=True, ensure_ascii=False)
        f.write("\n")

    importlib.reload(hun_law.fixups.replacement_fixups)
    importlib.reload(hun_law.fixups.common)
    importlib.reload(hun_law.fixups.text_fixups)


def detect_errors_and_try_fix(raw: MagyarKozlonyLawRawText) -> None:
    while True:
        print("Parsing {} {}".format(raw.identifier, raw.subject))
        print("Using {} fixups".format(len(hun_law.fixups.common.all_fixups.get(raw.identifier, []))))
        fixupped_body = hun_law.fixups.common.do_all_fixups(raw.identifier, raw.body)
        try:
            act = ActStructureParser.parse(raw.identifier, raw.publication_date, raw.subject, tuple(fixupped_body))
            act = ActBlockAmendmentParser.parse(act)
            act = ActSemanticsParser.add_semantics_to_act(act)
            print("Parsing successful")
            break
        except:  # pylint: disable=bare-except
            traceback.print_exc()
        if input("Do you want to fix it? (Yes/No, default: Yes)") not in ("", "y", "Y", "yes", "YES", "Yes"):
            break

        edited_body = do_file_editing(fixupped_body)
        replacements = extract_replacements([l.content for l in fixupped_body], edited_body)
        save_replacements_and_reload(raw.identifier, replacements)


init_cache(os.path.join(os.path.dirname(__file__), 'cache'))

extracted = do_extraction(
    [KozlonyToDownload(int(sys.argv[1]), int(sys.argv[2]))],
    result_classes=(MagyarKozlonyLawRawText, )
)

for e in extracted:
    detect_errors_and_try_fix(e)
