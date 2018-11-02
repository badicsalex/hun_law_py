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

from collections import namedtuple

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfdevice import PDFTextDevice
from pdfminer.utils import isnumber
from pdfminer.pdffont import PDFUnicodeNotDefined

from law_tools.utils import IndentedLine, EMPTY_LINE
from law_tools.cache import CacheObject

from . import Extractor
from .file import PDFFileDescriptor

TextBox = namedtuple('TextBox', ['x', 'y', 'content'])
PageOfTextBoxes = namedtuple('PageOfTextBoxes', ['textboxes'])
PdfOfTextBoxes = namedtuple('PdfOfTextBoxes', ['pages'])


class PDFMinerAdapter(PDFTextDevice):
    def __init__(self, rsrcmgr):
        super().__init__(rsrcmgr)
        self.pages = []
        self.current_page = None

    def begin_page(self, page, ctm):
        self.current_page = PageOfTextBoxes([])
        self.pages.append(self.current_page)

    def end_page(self, page):
        pass

    def add_textbox(self, x, y, s):
        self.current_page.textboxes.append(TextBox(x, y, s))

    def render_string(self, textstate, seq):
        # Sometimes the space char is used instead of "repositionings", with a little hack
        # where space is actually very short, or even of negative length
        space_is_not_used_for_space = textstate.wordspace < -1

        actual_chars = []
        for s in seq:
            if isnumber(s):
                # horizontal repositioning
                if s < -100:  # TODO: make this constant dymanic
                    # This is two cases as one right now:
                    # 1) Tabulating and things like table of contents. We flatten it to space for now, for
                    #    easier downstream processing. This may change if messy things (like characters not
                    #    present in the document left to right, etc.
                    # 2) Justified text sometimes use these "reposition"s instead of space characters,
                    #    if the width of the space is different for each word
                    # A more correct solution would be to handle these as different textboxes
                    actual_chars.append(' ')
                else:
                    # But sometimes it just signifies special "kern pairs", i.e. some characters need
                    # to be rendered with different char spacing than the rest to look pretty. E.g. AV
                    # We don't do anything in this case
                    pass
            else:
                # We have an actual string, yay
                for c in s:
                    if c == 32 and space_is_not_used_for_space:
                        continue
                    try:
                        uni_c = textstate.font.to_unichr(c)
                    except PDFUnicodeNotDefined:
                        # Some chars are simply not mapped in pdfminer, like little centered dot and whatnot >_>
                        # They are not in important places anyway, so whatever
                        # TODO: fix these characters either here, on in pdfminer itself
                        uni_c = '[X]'
                    actual_chars.append(uni_c)

        self.add_textbox(textstate.matrix[4], textstate.matrix[5], ''.join(actual_chars))
    # TODO: parse lines, so that footers can be detected more easily


class PageOfLines:
    def __init__(self):
        self.lines = []

    def add_line(self, line):
        self.lines.append(line)


class PdfOfLines:
    def __init__(self):
        self.pages = []

    def add_page(self, page):
        self.pages.append(page)

    def save_to_cache(self, cache_object):
        data_to_save = []
        for page in self.pages:
            page_to_save = []
            for line in page.lines:
                page_to_save.append({'content': line.content, 'indent': line.indent})
            data_to_save.append(page_to_save)
        cache_object.write_json(data_to_save)

    def load_from_cache(self, cache_object):
        data_to_load = cache_object.read_json()
        self.pages = []
        for page_to_load in data_to_load:
            page = PageOfLines()
            for line in page_to_load:
                page.add_line(IndentedLine(line['content'], line['indent']))
            self.add_page(page)


def extract_textboxes(f):
    rsrcmgr = PDFResourceManager()
    device = PDFMinerAdapter(rsrcmgr)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.get_pages(f.fp):
        interpreter.process_page(page)
    return PdfOfTextBoxes(device.pages)


def extract_lines(potb):
    result = PdfOfLines()
    for page in potb.pages:
        processed_page = PageOfLines()
        textboxes_as_dicts = {}
        for tb in page.textboxes:
            if tb.y not in textboxes_as_dicts:
                textboxes_as_dicts[tb.y] = {}
            if tb.x not in textboxes_as_dicts[tb.y]:
                textboxes_as_dicts[tb.y][tb.x] = tb.content
            else:
                # Workaround for weirdness where two textboxes are printed on the same coordinate
                # They are probably some kind of left-and right justification
                # TODO: handle correctly
                textboxes_as_dicts[tb.y][tb.x + 0.0001] = tb.content

        prev_y = 0
        for y in sorted(textboxes_as_dicts, reverse=True):
            # TODO: do't hardcode the 18, but use actual textbox dimensions
            if prev_y != 0 and (prev_y - y) > 18:
                processed_page.add_line(EMPTY_LINE)
            prev_y = y

            textboxes_in_line = textboxes_as_dicts[y]
            content = ' '.join([textboxes_in_line[x] for x in sorted(textboxes_in_line)])
            # The following line does:
            # - Repalce any string of whitespaces  to a single space
            # - strip the string
            # Thanks, stackoverflow.
            content = ' '.join(content.split())
            indent = min(textboxes_in_line)
            # TODO: this is a quick hack for one of the character coding fcukups.
            # Maybe I should have done the other chars too, but only this caused problems.
            content = content.replace("Õ", "Ő")  # Note the ~ on top of the first ő
            content = content.replace("õ", "ő")  # note the ~ on top of the first ő
            content = content.replace("Û", "Ű")  # Note the ^ on top of the first ő
            content = content.replace("û", "ű")  # note the ^ on top of the first ő

            processed_page.add_line(IndentedLine(content, indent))

        result.add_page(processed_page)
    return result


@Extractor(PDFFileDescriptor)
def CachedPdfParser(f):
    cache_object = CacheObject(f.cache_id + ".parsed")
    if cache_object.exists():
        result = PdfOfLines()
        result.load_from_cache(cache_object)
        yield result
    else:
        textboxes = extract_textboxes(f)
        result = extract_lines(textboxes)
        result.save_to_cache(cache_object)
        yield result
