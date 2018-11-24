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


# The whole module is a bunch of fixups to existing Acts, that aren't
# well-formed enough to be parsed by the parser out-of-the-box
import re

from hun_law.utils import IndentedLine, EMPTY_LINE
all_fixups = {}

def add_fixup(law_id, fixup_cb):
    global all_fixups
    if law_id in all_fixups:
        all_fixups[law_id].append(fixup_cb)
    else:
        all_fixups[law_id] = [fixup_cb]

def do_all_fixups(law_id, body):
    global all_fixups
    if law_id not in all_fixups:
        return body
    for fixup in all_fixups[law_id]:
        try:
            body  = fixup(body)
        except Exception as e:
            raise ValueError(
                "Fixup {} could not be done for {}: {}".format(fixup.__name__, law_id, e)
            ) from e
    return body


def add_empty_line_after(needle):
    def empty_line_adder(body):
        result = []
        needle_count = 0
        for l in body:
            result.append(l)
            if l.content == needle:
                result.append(EMPTY_LINE)
                needle_count = needle_count + 1
        if needle_count == 0:
            raise ValueError("Text '{}' not found in body".format(needle))
        if needle_count != 1:
            raise ValueError("Text '{}' found too many times in body: {}".format(needle, needle_count))
        return result
    return empty_line_adder


def replace_line_content(needle, replacement):
    def line_content_replacer(body):
        result = []
        needle_count = 0
        for l in body:
            if l.content != needle:
                result.append(l)
            else:
                result.append(IndentedLine(replacement, l.indent))
                needle_count = needle_count + 1
        if needle_count == 0:
            raise ValueError("Text '{}' not found in body".format(needle))
        if needle_count != 1:
            raise ValueError("Text '{}' found too many times in body: {}".format(needle, needle_count))
        return result
    return line_content_replacer


def ptke_article_header_fixer(body):
# BEFORE:
#            (A Ptk. 2:18. §-ához)
#    2. §    A Ptk. hatálybalépésekor a tize
#            helyezett kiskorú jognyilatkoza
#
# AFTER:
#    2. §    [A Ptk. 2:18. §-ához]
#            A Ptk. hatálybalépésekor a tize
#            helyezett kiskorú jognyilatkoza

    title_re = re.compile('^[\\[(](.*)[)\\]]$')
    article_re = re.compile('^([0-9]+\\. § )(.*)$')
    there_was_a_match = False

    result = []
    prev_line = None
    for line in body:
        if prev_line is None:
            prev_line = line
            continue

        title_match = title_re.match(prev_line.content)
        article_match = article_re.match(line.content)
        if title_match and article_match:
            fixed_title = IndentedLine("{}[{}]".format(article_match.group(1), title_match.group(1)), line.indent)
            # TODO: The indentation here is wrong for Paragraphs.
            fixed_body = IndentedLine(article_match.group(2), prev_line.indent)
            result.append(fixed_title)
            result.append(fixed_body)
            prev_line = None
            continue

        result.append(prev_line)
        prev_line = line

    result.append(prev_line)
    return result
