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
from urllib import request
from typing import Iterable

from hun_law.cache import CacheObject
from . import Extractor
from .file import PDFFileDescriptor


class KozlonyToDownload:
    URL_TEMPLATE = "http://www.kozlonyok.hu/nkonline/MKPDF/hiteles/MK{:02d}{:03d}.pdf"

    def __init__(self, year: int, issue: int) -> None:
        self.year = year
        self.issue = issue

    def get_url(self) -> str:
        return self.URL_TEMPLATE.format(self.year % 100, self.issue)


@Extractor(KozlonyToDownload)
def MagyarKozlonyHeaderExtractor(descriptor: KozlonyToDownload) -> Iterable[PDFFileDescriptor]:
    cache_id = "MK/{}/{}.pdf".format(descriptor.year, descriptor.issue)
    cache_object = CacheObject(cache_id)
    if not cache_object.exists():
        url_to_download = descriptor.get_url()
        print("Downloading {}".format(url_to_download), file=sys.stderr)
        with request.urlopen(url_to_download) as downloaded_file:
            cache_object.write_bytes(downloaded_file.read())
    yield PDFFileDescriptor(cache_object.get_filename(), cache_id)
