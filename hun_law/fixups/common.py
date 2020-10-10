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
from typing import Dict, Callable, List, Optional, Sequence, Iterable

from hun_law.utils import IndentedLine, IndentedLinePart, EMPTY_LINE

FixupFn = Callable[[Iterable[IndentedLine]], Iterable[IndentedLine]]
all_fixups: Dict[str, List[FixupFn]] = {}


def add_fixup(law_id: str, fixup_cb: FixupFn) -> None:
    global all_fixups
    if law_id in all_fixups:
        all_fixups[law_id].append(fixup_cb)
    else:
        all_fixups[law_id] = [fixup_cb]


def do_all_fixups(law_id: str, body: Iterable[IndentedLine]) -> Iterable[IndentedLine]:
    global all_fixups
    if law_id not in all_fixups:
        return body
    for fixup in all_fixups[law_id]:
        try:
            body = fixup(body)
        except Exception as e:
            raise ValueError(
                "Fixup {} could not be done for {}: {}".format(fixup.__name__, law_id, e)
            ) from e
    return body


def add_empty_line_after(needle: str) -> FixupFn:
    def empty_line_adder(body: Iterable[IndentedLine]) -> Iterable[IndentedLine]:
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


def delete_line(needle: str) -> FixupFn:
    def line_deleter(body: Iterable[IndentedLine]) -> Iterable[IndentedLine]:
        result = []
        needle_count = 0
        for l in body:
            if l.content == needle:
                needle_count = needle_count + 1
            else:
                result.append(l)
        if needle_count == 0:
            raise ValueError("Text '{}' not found in body".format(needle))
        if needle_count != 1:
            raise ValueError("Text '{}' found too many times in body: {}".format(needle, needle_count))
        return result
    return line_deleter


def replace_line_content(needle: str, replacement: str, *, needle_prev_lines: Optional[Sequence[str]] = None) -> FixupFn:
    common_prefix_len = 0
    while common_prefix_len < len(needle) and \
            common_prefix_len < len(replacement) and \
            needle[common_prefix_len] == replacement[common_prefix_len]:
        common_prefix_len += 1

    common_postfix_len = 1
    while common_prefix_len + common_postfix_len <= len(needle) and \
            common_prefix_len + common_postfix_len <= len(replacement) and \
            needle[-common_postfix_len] == replacement[-common_postfix_len]:
        common_postfix_len += 1
    common_postfix_len = common_postfix_len - 1

    def line_content_replacer(body: Iterable[IndentedLine]) -> Iterable[IndentedLine]:
        result: List[IndentedLine] = []
        needle_count = 0
        for l in body:
            needle_prev_lines_are_same = (
                needle_prev_lines is None or
                len(result) >= len(needle_prev_lines) and
                all(result[-i].content == needle_prev_lines[-i] for i in range(1, len(needle_prev_lines)+1))
            )
            if l.content != needle or not needle_prev_lines_are_same:
                result.append(l)
            elif replacement:
                # TODO: slicability depends on the part replaced.
                common_prefix = l.slice(0, common_prefix_len)
                replacement_indent = l.slice(common_prefix_len).indent
                if common_postfix_len:
                    replacement_part_s = replacement[common_prefix_len: -common_postfix_len]
                    common_postfix = l.slice(-common_postfix_len)
                else:
                    replacement_part_s = replacement[common_prefix_len:]
                    common_postfix = IndentedLine((), l.margin_right)
                replacement_part = IndentedLine((
                    IndentedLinePart(
                        replacement_indent,
                        replacement_part_s
                    ),
                ))
                to_append = IndentedLine.from_multiple(common_prefix, replacement_part, common_postfix)
                result.append(to_append)
                needle_count = needle_count + 1
            else:
                # Do nothing, delete line.
                needle_count = needle_count + 1

        if needle_count == 0:
            raise ValueError("Text '{}' not found in body".format(needle))
        if needle_count != 1:
            raise ValueError("Text '{}' found too many times in body: {}".format(needle, needle_count))
        return result
    return line_content_replacer


def ptke_article_header_fixer(body: Iterable[IndentedLine]) -> Iterable[IndentedLine]:
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

    result = []
    prev_line = None
    for line in body:
        if prev_line is None:
            prev_line = line
            continue

        title_match = title_re.match(prev_line.content)
        article_match = article_re.match(line.content)
        if title_match and article_match:
            article_header = line.slice(article_match.start(1), article_match.end(1))
            article_rest = line.slice(article_match.end(1))
            # TODO: Will not be sliceable
            fixed_title_string = IndentedLine(
                [
                    IndentedLinePart(
                        prev_line.indent, "[{}]".format(title_match.group(1))
                    )
                ],
                prev_line.margin_right
            )

            fixed_title = IndentedLine.from_multiple(article_header, fixed_title_string)
            fixed_body = IndentedLine.from_multiple(article_rest)
            result.append(fixed_title)
            result.append(fixed_body)
            prev_line = None
            continue

        result.append(prev_line)
        prev_line = line
    if prev_line is not None:
        result.append(prev_line)
    return result
