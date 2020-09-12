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

import json
from typing import Optional

from hun_law.utils import IndentedLine, IndentedLinePart
from hun_law.structure import Act, Reference, ReferencePartType
from hun_law.parsers.structure_parser import ActStructureParser
from hun_law.parsers.semantic_parser import ActBlockAmendmentParser

from hun_law import dict2object


def ref(
        act: Optional[str] = None,
        article: ReferencePartType = None,
        paragraph: ReferencePartType = None,
        point: ReferencePartType = None,
        subpoint: ReferencePartType = None
) -> Reference:
    return Reference(act, article, paragraph, point, subpoint)


def quick_parse_structure(act_text: str, *, parse_block_amendments: bool = False) -> Act:
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
                spaces_num += 1
            else:
                parts.append(IndentedLinePart(5 + spaces_num * 5, char, bold=bold))
                spaces_num = 0
        lines.append(IndentedLine(tuple(parts)))
    act = ActStructureParser.parse("2345 évi I. törvény", "A tesztelésről", lines)
    if parse_block_amendments:
        act = ActBlockAmendmentParser.parse(act)
    print(json.dumps(dict2object.to_dict(act, Act), indent='  ', ensure_ascii=False))
    return act
