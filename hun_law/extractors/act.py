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

from hun_law.parsers.structure_parser import ActStructureParser
from hun_law.parsers.semantic_parser import ActSemanticsParser
from hun_law.fixups.common import do_all_fixups
from hun_law.fixups import text_fixups
from . import Extractor
from .magyar_kozlony import MagyarKozlonyLawRawText


@Extractor(MagyarKozlonyLawRawText)
def MagyarKozlonyLawFixupper(raw):
    # TODO: assert for 10. § (2)(c) c): 'a cím utolsó szavához a „-ról”, „-ről” rag kapcsolódjon.'
    fixupped_body = do_all_fixups(raw.identifier, raw.body)
    act = ActStructureParser.parse(raw.identifier, raw.subject, fixupped_body)
    act = ActSemanticsParser.parse(act)
    yield act
