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

import attr
import textwrap
from collections import namedtuple
from string import ascii_uppercase


@attr.s(slots=True, frozen=True)
class IndentedLinePart:
    dx = attr.ib(converter=float)
    content = attr.ib(converter=str)


@attr.s(slots=True, frozen=True)
class IndentedLine:
    _parts = attr.ib(factory=tuple, converter=tuple)
    content = attr.ib(init=False)
    indent = attr.ib(init=False)

    @_parts.validator
    def _parts_validator(self, attribute, parts):
        for p in parts:
            if not isinstance(p, IndentedLinePart):
                raise TypeError("IndentedLine must be initialized with IndentedLineParts")

    @content.default
    def _content_default(self):
        return ''.join(t.content for t in self._parts)

    @indent.default
    def _indent_default(self):
        if not self._parts:
            return 0
        return self._parts[0].dx

    def to_serializable_form(self):
        return tuple((p.x, p.content) for p in self._parts)

    @classmethod
    def from_serializable_form(cls, serializable_form):
        return cls(IndentedLinePart(x, c) for x,c in serializable_form)

    def slice(self, start, end=None):
        if start < 0:
            start = len(self.content) + start
        if end is None:
            end = len(self.content)
        if end < 0:
            end = len(self.content) + end

        if start == 0 and end == len(self.content):
            return self

        if end <= start:
            return EMPTY_LINE

        skipped_x = 0
        skipped_len = 0
        skipped_parts_index = 0
        while skipped_len < start and skipped_parts_index < len(self._parts):
            skipped_x += self._parts[skipped_parts_index].dx
            skipped_len += len(self._parts[skipped_parts_index].content)
            skipped_parts_index += 1
        if skipped_parts_index >= len(self._parts):
            return EMPTY_LINE
        if skipped_len != start:
            raise ValueError("Couldn't slice precisely at requested index (multi-char part in the way)")

        included_parts_index = skipped_parts_index
        included_len = 0
        while included_len < end-start and included_parts_index < len(self._parts):
            included_len += len(self._parts[included_parts_index].content)
            included_parts_index += 1

        if included_len != end-start:
            raise ValueError("Couldn't slice precisely at requested index (multi-char part in the way)")

        first_part = self._parts[skipped_parts_index]
        if skipped_x:
            first_part = attr.evolve(first_part, dx=first_part.dx + skipped_x)

        return IndentedLine((first_part,) + self._parts[skipped_parts_index+1:included_parts_index])

    @classmethod
    def from_multiple(cls, *others):
        parts = []
        x = 0
        for o in others:
            first = True
            for p in o._parts:
                if first:
                    parts.append(IndentedLinePart(p.dx - x, p.content))
                    x = p.dx
                    first = False
                else:
                    parts.append(p)
                    x += p.dx
        return IndentedLine(parts)


EMPTY_LINE = IndentedLine()


def split_list(haystack, needle):
    # Thanks, stackoverflow
    result = []
    for e in haystack:
        if e == needle:
            if result != []:
                yield result
                result = []
        result.append(e)
    if result != []:
        yield result


TEXT_TO_INT_HUN_DICT_ORDINAL = None
INT_TO_TEXT_HUN_DICT_ORDINAL = None


def init_text_to_int_dict():
    # "Good enough for the demo, 1o1"
    global TEXT_TO_INT_HUN_DICT_ORDINAL
    global INT_TO_TEXT_HUN_DICT_ORDINAL
    TEXT_TO_INT_HUN_DICT_ORDINAL = {}
    INT_TO_TEXT_HUN_DICT_ORDINAL = {}
    SPECIAL_VALUES = {
        1: 'első',
        2: 'második',
        10: 'tizedik',
        20: 'huszadik',
        30: 'harmincadik',
        40: 'negyvenedik',
        50: 'ötvenedik',
        60: 'hatvanadik',
        70: 'hetvenedik',
        80: 'nyolcvanadik',
        90: 'kilencvenedik',
        100: 'századik',
    }
    ONES_DIGIT = (
        ('egyedik', 1),
        ('kettedik', 2),
        ('harmadik', 3),
        ('negyedik', 4),
        ('ötödik', 5),
        ('hatodik', 6),
        ('hetedik', 7),
        ('nyolcadik', 8),
        ('kilencedik', 9),
    )
    TENS_DIGIT = (
        ('', 0),
        ('tizen', 10),
        ('huszon', 20),
        ('harminc', 30),
        ('negyven', 40),
        ('ötven', 50),
        ('hatvan', 60),
        ('hetven', 70),
        ('nyolcvan', 80),
        ('kilencven', 90),
    )
    for ones_text, ones_val in ONES_DIGIT:
        for tens_text, tens_val in TENS_DIGIT:
            value = tens_val + ones_val
            if value in SPECIAL_VALUES:
                continue
            text = tens_text + ones_text
            TEXT_TO_INT_HUN_DICT_ORDINAL[text] = value
            INT_TO_TEXT_HUN_DICT_ORDINAL[value] = text

    for value, text in SPECIAL_VALUES.items():
        TEXT_TO_INT_HUN_DICT_ORDINAL[text] = value
        INT_TO_TEXT_HUN_DICT_ORDINAL[value] = text


def text_to_int_hun(s):
    global TEXT_TO_INT_HUN_DICT_ORDINAL
    if TEXT_TO_INT_HUN_DICT_ORDINAL is None:
        init_text_to_int_dict()
    if s.lower() not in TEXT_TO_INT_HUN_DICT_ORDINAL:
        raise ValueError("{} is not a number in written form".format(s))
    return TEXT_TO_INT_HUN_DICT_ORDINAL[s.lower()]


def int_to_text_hun(i):
    global INT_TO_TEXT_HUN_DICT_ORDINAL
    if INT_TO_TEXT_HUN_DICT_ORDINAL is None:
        init_text_to_int_dict()
    if i not in INT_TO_TEXT_HUN_DICT_ORDINAL:
        raise ValueError("{} is out of range for conversion into text form".format(i))
    return INT_TO_TEXT_HUN_DICT_ORDINAL[i]


def int_to_text_roman(i):
    # TODO: assert for i is int, and is not tooo big.
    numerals = (
        ("M", 1000), ("CM", 900), ("D", 500), ("CD", 400),
        ("C", 100), ("XC", 90), ("L", 50), ("XL", 40),
        ("X", 10), ("IX", 9), ("V", 5), ("IV", 4),
        ("I", 1)
    )
    result = ''
    while i > 0:
        for text, val in numerals:
            if val <= i:
                i = i - val
                result = result + text
                break
    return result


HUNGARIAN_UPPERCASE_CHARS = set(ascii_uppercase + 'ÉÁŐÚŰÖÜÓÍ')


def is_uppercase_hun(s):
    for c in s:
        if c not in HUNGARIAN_UPPERCASE_CHARS:
            return False
    return True


def indented_line_wrapped_print(s, indent_string="", width=120, file=None):
    for l in textwrap.wrap(s, width-len(indent_string)):
        if file is not None:
            print(indent_string + l, file=file)
        else:
            print(indent_string + l)
        indent_string = " "*len(indent_string)


def chr_latin2(num):
    if num > 255 or num < 0:
        raise ValueError("Code point {} not present in latin-2".format(num))
    return bytes([num]).decode('latin2')


def quote_level_diff(s):
    return s.count("„") + s.count("“") - s.count("”")


def iterate_with_quote_level(lines, *, throw_exceptions=True):
    quote_level = 0
    for line in lines:
        yield quote_level, line
        quote_level = quote_level + quote_level_diff(line.content)
        if throw_exceptions and quote_level < 0:
            raise ValueError("Malformed quoting. (Quote_level = {}, line='{}')".format(quote_level, line.content))

    if throw_exceptions and quote_level != 0:
        raise ValueError("Malformed quoting. (Quote_level = {})".format(quote_level))
