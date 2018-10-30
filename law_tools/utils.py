# Copyright 2018 Alex Badics <admin@stickman.hu>
#
# This file is part of Law-tools.
#
# Law-tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Law-tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Law-tools.  If not, see <https://www.gnu.org/licenses/>.

import textwrap
from collections import namedtuple
from string import ascii_uppercase

IndentedLine = namedtuple('IndentedLine', ['content', 'indent'])
EMPTY_LINE = IndentedLine('', 0)


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
        40: 'negzvenedik',
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


def indented_line_wrapped_print(s, indent_string="", width=120):
    for l in textwrap.wrap(s, width-len(indent_string)):
        print(indent_string + l)
        indent_string = " "*len(indent_string)
