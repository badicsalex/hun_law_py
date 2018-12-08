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

from hun_law.utils import IndentedLine, EMPTY_LINE


def test_indented_line_construction():
    with pytest.raises(Exception):
        line = IndentedLine()

    assert IndentedLine.get_empty_instance() == IndentedLine.get_empty_instance()
    assert IndentedLine.get_empty_instance() == EMPTY_LINE
    assert IndentedLine.from_parts([]) == EMPTY_LINE


def test_indented_line_slice():
    parts = [
        IndentedLine.Part(5, 'a'),
        IndentedLine.Part(10, 'b'),
        IndentedLine.Part(15, 'cde'),
        IndentedLine.Part(20, ' '),
        IndentedLine.Part(25, 'f')
    ]
    line = IndentedLine.from_parts(parts)
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
        IndentedLine.Part(5, 'a'),
        IndentedLine.Part(10, 'b'),
        IndentedLine.Part(15, 'cde'),
        IndentedLine.Part(20, ' '),
        IndentedLine.Part(25, 'f')
    ]
    line = IndentedLine.from_parts(parts)
    serialized_form = line.to_serializable_form()
    # test transformability to json
    json_string = json.dumps(serialized_form)
    new_serialized_form = json.loads(json_string)
    new_line = IndentedLine.from_serializable_form(new_serialized_form)

    assert new_line.content == line.content
    assert new_line.indent == line.indent

    assert new_line.slice(5).content == line.slice(5).content
    assert new_line.slice(5).indent == line.slice(5).indent

    unserialized_empty = IndentedLine.from_serializable_form(EMPTY_LINE.to_serializable_form())
    assert unserialized_empty == EMPTY_LINE


def test_indented_line_concat():
    parts1 = [
        IndentedLine.Part(5, 'a'),
        IndentedLine.Part(10, 'b'),
        IndentedLine.Part(15, 'cde'),
    ]
    parts2 = [
        IndentedLine.Part(20, ' '),
        IndentedLine.Part(25, 'f'),
    ]

    line1 = IndentedLine.from_parts(parts1)
    line2 = IndentedLine.from_parts(parts2)
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
