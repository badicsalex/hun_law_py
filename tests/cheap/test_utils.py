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
from typing import Any, Iterable, Tuple

import pytest

from hun_law.utils import \
    IndentedLine, IndentedLinePart, EMPTY_LINE, \
    text_to_int_hun, int_to_text_hun, \
    text_to_int_roman, int_to_text_roman, \
    roman_to_arabic_with_postfix, arabic_to_roman_with_postfix, \
    Date, \
    split_identifier_to_parts, identifier_less

from hun_law import dict2object

from hun_law.cache import CacheObject, init_cache

from .data.example_content import compression_test_parts


indented_line_converter = dict2object.get_converter(IndentedLine)


def test_indented_line_construction() -> None:
    assert IndentedLine() == IndentedLine()
    assert IndentedLine() == EMPTY_LINE
    assert IndentedLine(tuple()) == EMPTY_LINE
    assert IndentedLine(tuple(), 123.4) == EMPTY_LINE


def test_indented_line_slice() -> None:
    parts = (
        IndentedLinePart(5, 'a'),
        IndentedLinePart(5, 'b'),
        IndentedLinePart(5, 'cde'),
        IndentedLinePart(5, ' '),
        IndentedLinePart(5, 'f')
    )
    line = IndentedLine(parts, 30.0)
    assert line.content == 'abcde f'
    assert line.indent == 5

    assert line.slice(0) == line

    assert line.slice(1).content == 'bcde f'
    assert line.slice(1).indent == 10
    assert line.slice(1).margin_right == 30.0

    assert line.slice(2).content == 'cde f'
    assert line.slice(2).indent == 15
    assert line.slice(2).margin_right == 30.0

    with pytest.raises(Exception):
        _invalid_slice = line.slice(3)

    assert line.slice(5).content == ' f'
    assert line.slice(5).indent == 20

    assert line.slice(7) == EMPTY_LINE
    assert line.slice(100) == EMPTY_LINE

    assert line.slice(-2).content == ' f'
    assert line.slice(-2).indent == 20
    assert line.slice(-2).margin_right == 30.0

    assert line.slice(0, -1).content == 'abcde '
    assert line.slice(0, -2).content == 'abcde'
    assert line.slice(0, 5).content == 'abcde'

    # TODO: This should probably be exact somehow
    assert line.slice(0, -1).margin_right > 30.0
    assert line.slice(0, -2).margin_right > line.slice(0, -1).margin_right

    assert line.slice(1, -1).content == 'bcde '
    assert line.slice(2, -2).content == 'cde'
    assert line.slice(2, 5).content == 'cde'
    assert line.slice(2, 5).indent == 15
    assert line.slice(-2, -1).content == ' '

    assert line.slice(1, 1) == EMPTY_LINE
    assert line.slice(5, 3) == EMPTY_LINE

    with pytest.raises(Exception):
        _invalid_slice = line.slice(0, 4)


def test_indented_line_serialization() -> None:
    parts = (
        IndentedLinePart(5, 'a'),
        IndentedLinePart(5, 'b'),
        IndentedLinePart(5, 'cde'),
        IndentedLinePart(5, ' '),
        IndentedLinePart(5, 'f')
    )
    line = IndentedLine(parts, 43.123)
    serialized_form = indented_line_converter.to_dict(line)
    # test transformability to json
    json_string = json.dumps(serialized_form)
    new_serialized_form = json.loads(json_string)
    new_line = indented_line_converter.to_object(new_serialized_form)

    assert new_line.content == line.content
    assert new_line.indent == line.indent

    assert new_line.slice(5).content == line.slice(5).content
    assert new_line.slice(5).indent == line.slice(5).indent

    unserialized_empty = indented_line_converter.to_object(indented_line_converter.to_dict(EMPTY_LINE))
    assert unserialized_empty == EMPTY_LINE


def test_indented_line_serialization_compactness(tmpdir: Any) -> None:
    prev_x = 0
    parts = []
    for x, c in compression_test_parts:
        parts.append(IndentedLinePart(x-prev_x, c))
        prev_x = x

    line = IndentedLine(tuple(parts))

    # This is a test for an older scheme, where X coordinates were not stored exactly,
    # to save on digits in the JSON. It is not really relevant right now, but might
    # be in the future, so this assert stays here.
    quantization_error = abs(line.slice(50).indent - compression_test_parts[50][0])
    assert quantization_error < 0.01, "IndentedLine does not quantize the X coordinate too much"
    print(indented_line_converter.to_dict(line))

    init_cache(str(tmpdir))
    CacheObject("indented_test").write_json(indented_line_converter.to_dict(line))
    desired_max_len = 7 * len(compression_test_parts)
    assert CacheObject("indented_test").size_on_disk() < desired_max_len, \
        "Serialized IndentedLine is not too bloated. Also Cache is efficient."

    new_line = indented_line_converter.to_object(indented_line_converter.to_dict(line))

    assert new_line.content == line.content
    assert new_line.indent == line.indent

    assert new_line.slice(50).content == line.slice(50).content, "Non-trivial X coordinates survive serialization"
    assert new_line.slice(50).indent == line.slice(50).indent


def test_indented_line_concat() -> None:
    parts1 = (
        IndentedLinePart(5, 'a'),
        IndentedLinePart(5, 'b'),
        IndentedLinePart(5, 'cde'),
    )
    parts2 = (
        IndentedLinePart(20, ' '),
        IndentedLinePart(5, 'f'),
    )

    line1 = IndentedLine(parts1, 100.0)
    line2 = IndentedLine(parts2, 30.0)
    line = IndentedLine.from_multiple(line1, line2)

    assert line.content == 'abcde f'
    assert line.indent == 5
    assert line.margin_right == 30.0

    assert line.slice(1).content == 'bcde f'
    assert line.slice(1).indent == 10
    assert line.slice(1).margin_right == 30.0

    assert line.slice(2).content == 'cde f'
    assert line.slice(2).indent == 15
    assert line.slice(2).margin_right == 30.0

    with pytest.raises(Exception):
        _invalid_slice = line.slice(3)

    assert line.slice(-2, -1).content == ' '
    assert line.slice(-2, -1).indent == 20
    assert line.slice(-2, -1).margin_right > 30.0


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


@pytest.mark.parametrize("parts,should_be_bold", BOLDNESS_TESTS)  # type: ignore
def test_indented_line_bold(parts: Iterable[Tuple[str, bool]], should_be_bold: bool) -> None:
    line = IndentedLine(
        tuple(IndentedLinePart(5, s, bold) for s, bold in parts)
    )

    assert line.bold == should_be_bold


def test_text_to_int_hun() -> None:
    assert text_to_int_hun("Nyolcvankilencedik") == 89
    assert text_to_int_hun("tizenegyedik") == 11
    assert text_to_int_hun("HETEDIK") == 7

    assert int_to_text_hun(1) == "első"
    assert int_to_text_hun(25) == "huszonötödik"
    for i in range(1, 100):
        assert i == text_to_int_hun(int_to_text_hun(i))


def test_text_to_int_roman() -> None:
    assert text_to_int_roman("MCMXCVIII") == 1998
    assert int_to_text_roman(1998) == "MCMXCVIII"
    for i in range(1, 2000):
        assert i == text_to_int_roman(int_to_text_roman(i))

    with pytest.raises(ValueError):
        text_to_int_roman("Invalid")
    with pytest.raises(ValueError):
        text_to_int_roman("XIX/A")


def test_text_to_int_roman_to_arabic() -> None:
    assert roman_to_arabic_with_postfix("MCMXCVIII") == '1998'
    assert arabic_to_roman_with_postfix("1998") == "MCMXCVIII"
    assert roman_to_arabic_with_postfix("MCMXCVIII/A") == '1998/A'
    assert arabic_to_roman_with_postfix("1998/A") == "MCMXCVIII/A"

    # This is counterintuitive though.
    assert roman_to_arabic_with_postfix("Invalid") == '1nvalid'
    assert arabic_to_roman_with_postfix("1nvalid") == "Invalid"

    for postfix in ('', '/A', '.X'):
        for i in range(1, 2000):
            test_str = str(i) + postfix
            assert test_str == roman_to_arabic_with_postfix(arabic_to_roman_with_postfix(test_str))

    with pytest.raises(ValueError):
        roman_to_arabic_with_postfix("Nope")
    with pytest.raises(ValueError):
        arabic_to_roman_with_postfix("Nope")


def test_date_from_hungarian_text() -> None:
    assert Date.from_hungarian_text('2010. november 29., hétfő') == Date(2010, 11, 29)
    assert Date.from_hungarian_text('2014. február 11., kedd') == Date(2014, 2, 11)
    assert Date.from_hungarian_text('2019. július 9., kedd') == Date(2019, 7, 9)


def test_date_add() -> None:
    assert Date(2000, 12, 31).add_days(1) == Date(2001, 1, 1)
    assert Date(2020, 2, 28).add_days(1) == Date(2020, 2, 29)
    assert Date(2021, 2, 28).add_days(1) == Date(2021, 3, 1)

    assert Date(2021, 8, 28).add_days(10) == Date(2021, 9, 7)
    assert Date(2011, 3, 28).add_days(45) == Date(2011, 5, 12)
    assert Date(2011, 7, 28).add_days(20) == Date(2011, 8, 17)


def test_identifier_less() -> None:
    assert split_identifier_to_parts('1') == ('', 1)
    assert split_identifier_to_parts('a') == ('a',)
    assert split_identifier_to_parts('ab') == ('ab',)
    assert split_identifier_to_parts('1A') == ('', 1, 'A')
    assert split_identifier_to_parts('1/A') == ('', 1, '/A')
    assert split_identifier_to_parts('2:1/A') == ('', 2, ':', 1, '/A')

    assert identifier_less('1', '1/A')
    assert identifier_less('1', '2')
    assert identifier_less('1', '2/A')
    assert identifier_less('1/A', '2')
    assert identifier_less('1/A', '2/A')

    assert not identifier_less('1/A', '1')
    assert not identifier_less('2', '1')
    assert not identifier_less('2/A', '1')
    assert not identifier_less('2', '1/A')
    assert not identifier_less('2/A', '1/A')

    assert identifier_less('5', '20')
    assert identifier_less('1:20/A', '1:101')
