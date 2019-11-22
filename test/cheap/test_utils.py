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
import json
import pytest
import gzip

from hun_law.utils import \
    IndentedLine, IndentedLinePart, EMPTY_LINE, \
    dict_to_object_recursive, object_to_dict_recursive, \
    text_to_int_hun, int_to_text_hun, \
    text_to_int_roman, int_to_text_roman
from hun_law.cache import CacheObject, init_cache
from .data.example_content import compression_test_parts


def test_indented_line_construction():
    assert IndentedLine() == IndentedLine()
    assert IndentedLine() == EMPTY_LINE
    assert IndentedLine([]) == EMPTY_LINE


def test_indented_line_slice():
    parts = [
        IndentedLinePart(5, 'a'),
        IndentedLinePart(5, 'b'),
        IndentedLinePart(5, 'cde'),
        IndentedLinePart(5, ' '),
        IndentedLinePart(5, 'f')
    ]
    line = IndentedLine(parts)
    assert line.content == 'abcde f'
    assert line.indent == 5

    assert line.slice(0) == line

    assert line.slice(1).content == 'bcde f'
    assert line.slice(1).indent == 10

    assert line.slice(2).content == 'cde f'
    assert line.slice(2).indent == 15

    with pytest.raises(Exception):
        invalid_slice = line.slice(3)

    assert line.slice(5).content == ' f'
    assert line.slice(5).indent == 20

    assert line.slice(7) == EMPTY_LINE
    assert line.slice(100) == EMPTY_LINE

    assert line.slice(-2).content == ' f'
    assert line.slice(-2).indent == 20

    assert line.slice(0, -1).content == 'abcde '
    assert line.slice(0, -2).content == 'abcde'
    assert line.slice(0, 5).content == 'abcde'

    assert line.slice(1, -1).content == 'bcde '
    assert line.slice(2, -2).content == 'cde'
    assert line.slice(2, 5).content == 'cde'
    assert line.slice(2, 5).indent == 15
    assert line.slice(-2, -1).content == ' '

    assert line.slice(1, 1) == EMPTY_LINE
    assert line.slice(5, 3) == EMPTY_LINE

    with pytest.raises(Exception):
        invalid_slice = line.slice(0, 4)


def test_indented_line_serialization():
    parts = [
        IndentedLinePart(5, 'a'),
        IndentedLinePart(5, 'b'),
        IndentedLinePart(5, 'cde'),
        IndentedLinePart(5, ' '),
        IndentedLinePart(5, 'f')
    ]
    line = IndentedLine(parts)
    serialized_form = object_to_dict_recursive(line)
    # test transformability to json
    json_string = json.dumps(serialized_form)
    new_serialized_form = json.loads(json_string)
    new_line = dict_to_object_recursive(new_serialized_form, (IndentedLine, IndentedLinePart))

    assert new_line.content == line.content
    assert new_line.indent == line.indent

    assert new_line.slice(5).content == line.slice(5).content
    assert new_line.slice(5).indent == line.slice(5).indent

    unserialized_empty = dict_to_object_recursive(object_to_dict_recursive(EMPTY_LINE), (IndentedLine, IndentedLinePart))
    assert unserialized_empty == EMPTY_LINE


def test_indented_line_serialization_compactness(tmpdir):
    prev_x = 0
    parts = []
    for x, c in compression_test_parts:
        parts.append(IndentedLinePart(x-prev_x, c))
        prev_x = x

    line = IndentedLine(parts)

    # This is a test for an older scheme, where X coordinates were not stored exactly,
    # to save on digits in the JSON. It is not really relevant right now, but might
    # be in the future, so this assert stays here.
    quantization_error = abs(line.slice(50).indent - compression_test_parts[50][0])
    assert quantization_error < 0.01, "IndentedLine does not quantize the X coordinate too much"
    print(object_to_dict_recursive(line))

    init_cache(str(tmpdir))
    CacheObject("indented_test").write_json(object_to_dict_recursive(line))
    desired_max_len = 7 * len(compression_test_parts)
    assert CacheObject("indented_test").size_on_disk() < desired_max_len, \
        "Serialized IndentedLine is not too bloated. Also Cache is efficient."

    new_line = dict_to_object_recursive(
        object_to_dict_recursive(line),
        (IndentedLine, IndentedLinePart)
    )
    assert new_line.content == line.content
    assert new_line.indent == line.indent

    assert new_line.slice(50).content == line.slice(50).content, "Non-trivial X coordinates survive serialization"
    assert new_line.slice(50).indent == line.slice(50).indent


def test_indented_line_concat():
    parts1 = [
        IndentedLinePart(5, 'a'),
        IndentedLinePart(5, 'b'),
        IndentedLinePart(5, 'cde'),
    ]
    parts2 = [
        IndentedLinePart(20, ' '),
        IndentedLinePart(5, 'f'),
    ]

    line1 = IndentedLine(parts1)
    line2 = IndentedLine(parts2)
    line = IndentedLine.from_multiple(line1, line2)

    assert line.content == 'abcde f'
    assert line.indent == 5
    assert line.slice(1).content == 'bcde f'
    assert line.slice(1).indent == 10

    assert line.slice(2).content == 'cde f'
    assert line.slice(2).indent == 15

    with pytest.raises(Exception):
        invalid_slice = line.slice(3)

    assert line.slice(-2, -1).content == ' '
    assert line.slice(-2, -1).indent == 20


BOLDNESS_TESTS = [
    (
        (
            ('a', True),
            ('b', True),
            ('c', True),
            ('d', True),
        ), True,
    ),
    (
        (
            ('a', False),
            ('b', False),
            ('c', False),
            ('d', False),
        ), False,
    ),
    (
        (
            ('a', True),
            ('b', False),
            ('c', False),
            ('d', False),
        ), False,
    ),
    (
        (
            ('a', False),
            ('b', True),
            ('c', True),
            ('d', True),
        ), True,
    ),
    (
        (
            ('abcdef', True),
            ('b', False),
            ('c', False),
        ), True,
    ),
    (
        (
            ('abcdef', False),
            ('b', True),
            ('c', True),
        ), False,
    ),
    (
        (
            ('1. § (1)', True),
            ('A devizakölcsönök...', False),
            ('b', False),
        ), False,
    ),
]


@pytest.mark.parametrize("parts,should_be_bold", BOLDNESS_TESTS)
def test_indented_line_bold(parts, should_be_bold):
    line = IndentedLine(
        IndentedLinePart(5, s, bold) for s, bold in parts
    )

    assert line.bold == should_be_bold


def test_text_to_int_hun():
    assert text_to_int_hun("Nyolcvankilencedik") == 89
    assert text_to_int_hun("tizenegyedik") == 11
    assert text_to_int_hun("HETEDIK") == 7

    assert int_to_text_hun(1) == "első"
    assert int_to_text_hun(25) == "huszonötödik"
    for i in range(1, 100):
        assert i == text_to_int_hun(int_to_text_hun(i))


def test_text_to_int_roman():
    assert text_to_int_roman("MCMXCVIII") == 1998
    assert int_to_text_roman(1998) == "MCMXCVIII"
    for i in range(1, 2000):
        assert i == text_to_int_roman(int_to_text_roman(i))

    with pytest.raises(ValueError):
        text_to_int_roman("Invalid")
    with pytest.raises(ValueError):
        text_to_int_roman("XIX/A")
