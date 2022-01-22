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

import collections
import textwrap
import datetime
import re
from string import ascii_uppercase
from typing import Tuple, List, Iterable, TypeVar, Optional, Union, Dict, Any, TextIO

import attr


@attr.s(slots=True, frozen=True, auto_attribs=True)
class IndentedLinePart:
    dx: float
    content: str
    bold: bool = False


@attr.s(slots=True, frozen=True)
class IndentedLine:
    _parts: Tuple[IndentedLinePart, ...] = attr.ib(factory=tuple)
    margin_right: float = attr.ib(default=0, eq=False, hash=False)
    content: str = attr.ib(init=False)
    indent: float = attr.ib(init=False)
    bold: bool = attr.ib(init=False)

    @_parts.validator
    def _parts_validator(self, _attribute: Any, parts: Tuple[IndentedLinePart, ...]) -> None:
        # pylint: disable=no-self-use
        for p in parts:
            if not isinstance(p, IndentedLinePart):
                raise TypeError("IndentedLine must be initialized with IndentedLineParts")

    @content.default
    def _content_default(self) -> str:
        return ''.join(t.content for t in self._parts)

    @indent.default
    def _indent_default(self) -> float:
        if not self._parts:
            return 0.0
        return self._parts[0].dx

    @bold.default
    def _bold_default(self) -> bool:
        sum_len = 0
        bold_len = 0
        for p in self._parts:
            sum_len += len(p.content)
            if p.bold:
                bold_len += len(p.content)
        return bold_len * 2 > sum_len

    def slice(self, start: int, end: Optional[int] = None) -> 'IndentedLine':
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

        skipped_x = 0.0
        skipped_len = 0
        skipped_parts_index = 0
        while skipped_len < start and skipped_parts_index < len(self._parts):
            skipped_x += self._parts[skipped_parts_index].dx
            skipped_len += len(self._parts[skipped_parts_index].content)
            skipped_parts_index += 1
        if skipped_parts_index >= len(self._parts):
            return EMPTY_LINE
        if skipped_len != start:
            offending_part = self._parts[skipped_parts_index-1].content
            raise ValueError(
                "Couldn't slice precisely at requested start index (multi-char part '{}' in the way)"
                .format(offending_part)
            )

        included_parts_index = skipped_parts_index
        included_len = 0
        while included_len < end-start and included_parts_index < len(self._parts):
            included_len += len(self._parts[included_parts_index].content)
            included_parts_index += 1

        if included_len != end-start:
            offending_part = self._parts[included_parts_index-1].content
            raise ValueError(
                "Couldn't slice precisely at requested end index (multi-char part '{}' in the way)"
                .format(offending_part)
            )

        first_part = self._parts[skipped_parts_index]
        if skipped_x:
            first_part = attr.evolve(first_part, dx=first_part.dx + skipped_x)

        # TODO: This is a heuristic, hard coded character width.
        # Really ugly hack, I know, but it's kind of the same as the space
        # detection in PDF parser
        margin_right = self.margin_right + 20 * (len(self._parts) - included_parts_index)

        return IndentedLine((first_part,) + self._parts[skipped_parts_index+1:included_parts_index], margin_right)

    @classmethod
    def from_multiple(cls, *others: 'IndentedLine') -> 'IndentedLine':
        parts = []
        x = 0.0
        for o in others:
            first = True
            # Accessing protected properties is literally the point of
            # classmethods.
            # pylint: disable=protected-access
            for p in o._parts:
                if first:
                    parts.append(IndentedLinePart(p.dx - x, p.content))
                    x = p.dx
                    first = False
                else:
                    parts.append(p)
                    x += p.dx
        return IndentedLine(tuple(parts), others[-1].margin_right if others else 0)


EMPTY_LINE = IndentedLine()


@attr.s(slots=True, frozen=True, auto_attribs=True)
class Date:
    year: int
    month: int
    day: int

    def __attrs_post_init__(self) -> None:
        _should_not_raise = datetime.date(self.year, self.month, self.day)

    @classmethod
    def from_hungarian_text(cls, s: str) -> 'Date':
        # e.g. 2011. június 28., kedd
        s = s.split(',', 1)[0]
        year, month, day = s.split(' ')
        return cls(int(year[:-1]), text_to_month_hun(month), int(day[:-1]))

    @classmethod
    def from_simple_string(cls, s: str) -> 'Date':
        parts = []
        if '.' in s:
            if s.endswith('.'):
                s = s[:-1]
            parts = s.split('.')
        elif '/' in s:
            parts = s.split('/')
        if len(parts) != 3:
            raise ValueError("Date not in YEAR/MONTH/DAY or YEAR.MONTH.DAY format")
        return cls(int(parts[0]), int(parts[1]), int(parts[2]))

    def add_days(self, days: int) -> 'Date':
        native_date = datetime.date(self.year, self.month, self.day) + datetime.timedelta(days=days)
        return Date(native_date.year, native_date.month, native_date.day)

    @classmethod
    def today(cls) -> 'Date':
        native_date = datetime.date.today()
        return Date(native_date.year, native_date.month, native_date.day)


T = TypeVar('T')


def split_list(haystack: Iterable[T], needle: T) -> Iterable[List[T]]:
    # Thanks, stackoverflow
    result: List[T] = []
    for e in haystack:
        if e == needle:
            if result:
                yield result
                result = []
        result.append(e)
    if result:
        yield result


TEXT_TO_INT_HUN_DICT_ORDINAL: Optional[Dict[str, int]] = None
INT_TO_TEXT_HUN_DICT_ORDINAL: Optional[Dict[int, str]] = None


def init_text_to_int_dict() -> None:
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


def text_to_int_hun(s: str) -> int:
    global TEXT_TO_INT_HUN_DICT_ORDINAL
    if TEXT_TO_INT_HUN_DICT_ORDINAL is None:
        init_text_to_int_dict()
    assert TEXT_TO_INT_HUN_DICT_ORDINAL is not None
    if s.lower() not in TEXT_TO_INT_HUN_DICT_ORDINAL:
        raise ValueError("{} is not a number in written form".format(s))
    return TEXT_TO_INT_HUN_DICT_ORDINAL[s.lower()]


def int_to_text_hun(i: int) -> str:
    global INT_TO_TEXT_HUN_DICT_ORDINAL
    if INT_TO_TEXT_HUN_DICT_ORDINAL is None:
        init_text_to_int_dict()
    assert INT_TO_TEXT_HUN_DICT_ORDINAL is not None
    if i not in INT_TO_TEXT_HUN_DICT_ORDINAL:
        raise ValueError("{} is out of range for conversion into text form".format(i))
    return INT_TO_TEXT_HUN_DICT_ORDINAL[i]


ROMAN_NUMERALS = (
    ("M", 1000), ("CM", 900), ("D", 500), ("CD", 400),
    ("C", 100), ("XC", 90), ("L", 50), ("XL", 40),
    ("X", 10), ("IX", 9), ("V", 5), ("IV", 4),
    ("I", 1)
)


def int_to_text_roman(i: int) -> str:
    # TODO: assert for i is int, and is not tooo big.
    result = ''
    while i > 0:
        for text, val in ROMAN_NUMERALS:
            if val <= i:
                i = i - val
                result = result + text
                break
    return result


def text_to_int_roman_with_postfix(s: str) -> Tuple[int, str]:
    result = 0
    while s:
        for text, val in ROMAN_NUMERALS:
            if text == s[:len(text)]:
                s = s[len(text):]
                result = result + val
                break
        else:  # No valid numeral found
            break
    if result == 0:
        raise ValueError("No roman numerals found.")
    return result, s


def text_to_int_roman(s: str) -> int:
    result, postfix = text_to_int_roman_with_postfix(s)
    if postfix:
        raise ValueError("Numeral is not roman.")
    return result


NUMBER_FINDER_RE = re.compile("([0-9]+)(.*)")


def arabic_to_roman_with_postfix(s: str) -> str:
    m = NUMBER_FINDER_RE.match(s)
    if m is None:
        raise ValueError("String does not begin with a number", s)
    return int_to_text_roman(int(m.group(1))) + m.group(2)


def roman_to_arabic_with_postfix(s: str) -> str:
    result, postfix = text_to_int_roman_with_postfix(s)
    return str(result) + postfix


HUNGARIAN_UPPERCASE_CHARS = set(ascii_uppercase + 'ÉÁŐÚŰÖÜÓÍ')


def is_uppercase_hun(s: str) -> bool:
    for c in s:
        if c not in HUNGARIAN_UPPERCASE_CHARS:
            return False
    return True


def indented_line_wrapped_print(s: str, indent_string: str = "", width: int = 90, file: Optional[TextIO] = None) -> None:
    if not width:
        print(indent_string + s)
        return
    for l in textwrap.wrap(s, width-len(indent_string)):
        if file is not None:
            print(indent_string + l, file=file)
        else:
            print(indent_string + l)
        indent_string = " "*len(indent_string)


def chr_latin2(num: int) -> str:
    if num > 255 or num < 0:
        raise ValueError("Code point {} not present in latin-2".format(num))
    return bytes([num]).decode('latin2')


def quote_level_diff(s: str) -> int:
    return s.count("„") + s.count("“") - s.count("”")


def iterate_with_quote_level(lines: Iterable[IndentedLine], *, throw_exceptions: bool = True) -> Iterable[Tuple[int, IndentedLine]]:
    quote_level = 0
    for line in lines:
        yield quote_level, line
        quote_level = quote_level + quote_level_diff(line.content)
        if throw_exceptions and quote_level < 0:
            raise ValueError("Malformed quoting. (Quote_level = {}, line='{}')".format(quote_level, line.content))

    if throw_exceptions and quote_level != 0:
        raise ValueError("Malformed quoting. (Quote_level = {})".format(quote_level))


SPECIAL_NEXT_LETTER_PAIRS = set((
    ('g', 'gy'),
    ('gy', 'h'),
    ('n', 'ny'),
    ('ny', 'o'),
    ('s', 'sz'),
    ('sz', 't'),
    ('t', 'ty'),
    ('ty', 'u'),
    ('G', 'GY'),
    ('GY', 'H'),
    ('N', 'NY'),
    ('NY', 'O'),
    ('S', 'SZ'),
    ('SZ', 'T'),
    ('T', 'TY'),
    ('TY', 'U'),
))


def is_next_letter_hun(a: str, b: str) -> bool:
    if (a, b) in SPECIAL_NEXT_LETTER_PAIRS:
        return True
    if len(a) == 1 and len(b) == 1 and ord(a) + 1 == ord(b):
        return True
    return False


MONTHS_HUN = (
    "január",
    "február",
    "március",
    "április",
    "május",
    "június",
    "július",
    "augusztus",
    "szeptember",
    "október",
    "november",
    "december"
)


def text_to_month_hun(s: str) -> int:
    if s not in MONTHS_HUN:
        raise KeyError("{} is not a valid month name".format(s))
    return MONTHS_HUN.index(s) + 1


def flatten(l: Iterable[Any]) -> Iterable[Any]:
    l = collections.deque(l)
    while l:
        element = l.popleft()
        if isinstance(element, list):
            l.extendleft(reversed(element))
        else:
            yield element


def split_identifier_to_parts(s: str) -> Tuple[Union[str, int], ...]:
    result: List[Union[str, int]] = []
    current_str = ''
    last_was_digit = False
    for c in s:
        if c.isdigit() != last_was_digit:
            if last_was_digit:
                result.append(int(current_str))
            else:
                result.append(current_str)
            current_str = ''
            last_was_digit = c.isdigit()
        current_str = current_str + c
    if current_str:
        if last_was_digit:
            result.append(int(current_str))
        else:
            result.append(current_str)
    return tuple(result)


def identifier_less(a: str, b: str) -> bool:
    """ Returns a<b, but smartly."""
    a_parts = split_identifier_to_parts(a)
    b_parts = split_identifier_to_parts(b)
    return a_parts < b_parts


def is_next_numeric_identifier(identifier: str, next_identifier: str) -> bool:
    identifier = identifier.replace('/', '')
    next_identifier = next_identifier.replace('/', '')
    if identifier.isdigit():
        if next_identifier.isdigit():
            # "1" and "2"
            return int(identifier) + 1 == int(next_identifier)
        # "1" and "1a"
        return next_identifier in (identifier + 'a', identifier + 'A')
    if next_identifier.isdigit():
        # "1a" and "2"
        # TODO: lets hope for no "1sz" or similar
        return int(identifier[:-1]) + 1 == int(next_identifier)
    # "1a" and "1b"
    return identifier[:-1] == next_identifier[:-1] and is_next_letter_hun(identifier[-1], next_identifier[-1])


def join_line_strs(lines: Iterable[str]) -> str:
    result = ''
    for s in lines:
        if result and result[-1] != '-':
            result = result + ' '
        result = result + s
    return result


_HIT = TypeVar("_HIT")


def cut_by_identifier(elements: Iterable[_HIT], from_identifier: str, to_identifier: str) -> Tuple[_HIT, ...]:
    result = []
    for element in elements:
        if (
            element.identifier is None or  # type: ignore
            identifier_less(element.identifier, from_identifier) or  # type: ignore
            identifier_less(to_identifier, element.identifier)  # type: ignore
        ):
            continue
        result.append(element)
    return tuple(result)
