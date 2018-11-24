#!/usr/bin/env python3
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

import sys
import os

from hun_law.extractors import Extractor
from hun_law.extractors.kozlonyok_hu_downloader import KozlonyToDownload
from hun_law.extractors.all import do_extraction
from hun_law.extractors import magyar_kozlony
from hun_law.structure import Act
from hun_law.cache import init_cache

@Extractor(Act)
def ActPrinter(e):
    print("==== Structured text of {} - {} =====\n".format(e.identifier, e.subject))
    e.print_to_console()
    # Empty generator hack
    return
    yield

init_cache(os.path.join(os.path.dirname(__file__), 'cache'))

extracted = do_extraction([KozlonyToDownload(sys.argv[1], sys.argv[2])])

for e in extracted:
    print("Final extracted object: {}\n".format(type(e)))
