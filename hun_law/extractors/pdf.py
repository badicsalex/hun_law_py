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

import unicodedata

from collections import namedtuple

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfdevice import PDFTextDevice
from pdfminer.utils import isnumber
from pdfminer.pdffont import PDFUnicodeNotDefined

from hun_law.utils import IndentedLine, IndentedLinePart, EMPTY_LINE, chr_latin2
from hun_law.cache import CacheObject

from . import Extractor
from .file import PDFFileDescriptor

TextBox = namedtuple('TextBox', ['x', 'y', 'width', 'width_of_space', 'content'])
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

    def render_char(self, matrix, font, fontsize, scaling, rise, cid, *args):
        try:
            text = font.to_unichr(cid)
            # Keep in mind that 'text' can be multiple characters, like 'ffi'
            # This is the same reason the TextBox type name was kept, and it's not "CharBox"
        except PDFUnicodeNotDefined:
            # ... and the above is why this is absolutely correct for now.
            # TODO: it's not really correct.
            text = '[X]'

        if cid < 256 and chr_latin2(cid) != text and chr_latin2(cid).upper() == text.upper():
            # TODO: horrible workaround for a horrible bug in 2013 era InDesign, where
            # in some cases, the casing is wrong for several characters in the
            # ToUnicode map. Usually in allcaps fonts.
            # I'm pretty sure this does not work for accented characters
            text = chr_latin2(cid)

        # TODO: this is a quick hack for one of the character coding fcukups.
        # Basically all encodings should be Latin-2, but if that's not in the
        # PDF, de default encoding is Latin-1, with the weird squiggly accents
        # Maybe I should have done the other chars too, but only these caused problems.
        # This is also done with "replace()" because "text" might be multiple characters.
        text = text.replace("Õ", "Ő")  # Note the ~ on top of the first ő
        text = text.replace("õ", "ő")  # note the ~ on top of the first ő
        text = text.replace("Û", "Ű")  # Note the ^ on top of the first ű
        text = text.replace("û", "ű")  # note the ^ on top of the first ű

        textwidth = font.char_width(cid) * fontsize * scaling

        # Workaround for some malformed texts, such as the 2018 L. Act about the budget
        # in it, these weird "private" characters denote | signs, for constructing
        # tables (poorly). The  main issue is that sometimes they render these characters
        # exactly where other characters are, and that throws an error in later processing.
        # We will just throw these away for now, as it's in an appendix
        # And we do not even parse Appendixes (TODO)
        if unicodedata.category(text[0]) in ('Co', 'Cf'):
            return textwidth

        if not text.isspace():
            unscaled_width_of_space = font.char_width(32)
            if unscaled_width_of_space == 1.0 or unscaled_width_of_space == 0.0:
                # Workaround for missing default width of space
                # e.g. the font does not define the space character
                unscaled_width_of_space = 0.25
            x = matrix[4]
            y = round(matrix[5], 3)
            textbox_width = textwidth * matrix[0]
            width_of_space = unscaled_width_of_space * fontsize * scaling * matrix[0]
            self.current_page.textboxes.append(TextBox(x, y, textbox_width, width_of_space, text))
        return textwidth

    # TODO: parse graphical lines, so that footers can be detected more easily


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
                page_to_save.append(line.to_serializable_form())
            data_to_save.append(page_to_save)
        cache_object.write_json(data_to_save)

    def load_from_cache(self, cache_object):
        data_to_load = cache_object.read_json()
        self.pages = []
        for page_to_load in data_to_load:
            page = PageOfLines()
            for line in page_to_load:
                page.add_line(IndentedLine.from_serializable_form(line))
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
    for page_num, page in enumerate(potb.pages):
        processed_page = PageOfLines()
        textboxes_as_dicts = {}
        for tb in page.textboxes:
            if tb.y not in textboxes_as_dicts:
                # TODO: quantize y if needed. We are only lucky that
                # lines don't have an epsilon amount of y space between words
                # And that sub and superscripts are not used
                textboxes_as_dicts[tb.y] = {}
            if tb.x in textboxes_as_dicts[tb.y]:
                if tb.content != textboxes_as_dicts[tb.y][tb.x].content:
                    raise ValueError(
                        "Multiple textboxes on the exact same coordinates on page  {}"
                        "(Already there: '{}', to-be-inserted: '{}')"
                        .format(page_num, textboxes_as_dicts[tb.y][tb.x], tb.content)
                    )
            else:
                textboxes_as_dicts[tb.y][tb.x] = tb

        last_y_coord = None
        for y_coord in sorted(textboxes_as_dicts):
            # TODO: instad of 0.2, use some real line height thing
            # 0.2 is small enough not to trigger for the e.g. the 2 in "m2" (the unit).
            # And this is okay for now
            if last_y_coord is not None and abs(y_coord-last_y_coord)<0.2:
                # TODO: let's hope there is no intersection between the previous line's
                # X coordinates and the current one. There shouldn't be any though.
                textboxes_as_dicts[last_y_coord].update(textboxes_as_dicts[y_coord])
                # Deleting elements during this iteration should be okay,
                # because "sorted" creates a copy of the keys
                del textboxes_as_dicts[y_coord]
            else:
                last_y_coord = y_coord

        prev_y = 0
        for y in sorted(textboxes_as_dicts, reverse=True):
            # TODO: do't hardcode the 18, but use actual textbox dimensions
            if prev_y != 0 and (prev_y - y) > 18:
                processed_page.add_line(EMPTY_LINE)
            prev_y = y

            parts = []
            threshold_to_space = None
            prev_x = 0
            for x in sorted(textboxes_as_dicts[y]):
                box = textboxes_as_dicts[y][x]
                if threshold_to_space is not None and x > threshold_to_space or box.content == '„':
                    if parts and parts[-1].content[-1] != ' ':
                        parts.append(IndentedLinePart(threshold_to_space - prev_x, ' '))
                        prev_x = threshold_to_space
                parts.append(IndentedLinePart(box.x - prev_x, box.content))
                prev_x = box.x
                threshold_to_space = x + box.width + box.width_of_space * 0.5
                current_right_side = x + box.width

            processed_page.add_line(IndentedLine(parts))

        result.add_page(processed_page)
    return result


@Extractor(PDFFileDescriptor)
def CachedPdfParser(f):
    cache_object = CacheObject(f.cache_id + ".parsed_v2.gz")
    if cache_object.exists():
        result = PdfOfLines()
        result.load_from_cache(cache_object)
        yield result
    else:
        textboxes = extract_textboxes(f)
        result = extract_lines(textboxes)
        result.save_to_cache(cache_object)
        yield result
