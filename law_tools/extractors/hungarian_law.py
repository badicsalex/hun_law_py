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

from law_tools.hun_law.structure import Act

from . import Extractor
from .magyar_kozlony import MagyarKozlonyLawRawText
from .fixups.common import do_all_fixups
from .fixups import hungarian_law


@Extractor(MagyarKozlonyLawRawText)
def MagyarKozlonyLawFixupper(raw):
    # TODO: assert for 10. § (2)(c) c): 'a cím utolsó szavához a „-ról”, „-ről” rag kapcsolódjon.'
    fixupped_body = do_all_fixups(raw.identifier, raw.body)
    yield Act(raw.identifier, raw.subject, fixupped_body)
