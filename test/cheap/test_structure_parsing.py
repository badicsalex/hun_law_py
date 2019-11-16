# Copyright 2019 Alex Badics <admin@stickman.hu>
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

from hun_law.utils import IndentedLine, IndentedLinePart, object_to_dict_recursive
from hun_law.parsers.structure_parser import ActStructureParser

import pytest
import json
import os
import sys


def quick_parse_structure(act_text):
    lines = []
    for l in act_text.split('\n'):
        parts = []
        spaces_num = 1
        bold = '<BOLD>' in l
        l = l.replace("<BOLD>", "      ")
        for char in l:
            if char == ' ':
                if spaces_num == 0:
                    parts.append(IndentedLinePart(5, char, bold=bold))
                else:
                    spaces_num += 1
            else:
                parts.append(IndentedLinePart(5 + spaces_num * 5, char))
                spaces_num = 0
        lines.append(IndentedLine(parts))
    act = ActStructureParser.parse("2345 évi I. törvény", "A tesztelésről", lines)
    return act


def structure_testcase_provider():
    data_dir = os.path.join(os.path.dirname(__file__), 'data/structure_tests')
    for fname in sorted(os.listdir(data_dir)):
        if not fname.endswith('.txt'):
            continue
        input_fname = os.path.join(data_dir, fname)
        output_fname = input_fname.replace('.txt', '.json')
        with open(input_fname) as infile, open(output_fname) as outfile:
            yield pytest.param(
                infile.read(),
                json.load(outfile),
                id=fname
            )


@pytest.mark.parametrize("text,expected_structure", structure_testcase_provider())
def test_structure_parsing_exact(text, expected_structure):
    resulting_structure = quick_parse_structure(text)
    result_as_dict = object_to_dict_recursive(resulting_structure)

    json.dump(result_as_dict, sys.stdout, indent='    ', ensure_ascii=False, sort_keys=True)

    assert result_as_dict == expected_structure
