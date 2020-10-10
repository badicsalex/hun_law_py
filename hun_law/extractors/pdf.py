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

from typing import cast, List, Dict, Sequence, Any, Iterable

import attr

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfdevice import PDFTextDevice
from pdfminer.pdffont import PDFUnicodeNotDefined, PDFFont

from hun_law.utils import IndentedLine, IndentedLinePart, EMPTY_LINE, chr_latin2
from hun_law.cache import CacheObject
from hun_law import dict2object

from . import Extractor
from .file import PDFFileDescriptor


@attr.s(slots=True, frozen=True, auto_attribs=True)
class TextBox:
    x: float
    y: float
    width: float
    width_of_space: float
    content: str
    bold: bool


@attr.s(slots=True, auto_attribs=True)
class PageOfTextBoxes:
    textboxes: List[TextBox]


@attr.s(slots=True, auto_attribs=True)
class PdfOfTextBoxes:
    pages: List[PageOfTextBoxes]


class PDFMinerAdapter(PDFTextDevice):
    def __init__(self, rsrcmgr: PDFResourceManager):
        super().__init__(rsrcmgr)
        self.pages: List[PageOfTextBoxes] = []
        self.current_page = PageOfTextBoxes([])

    def begin_page(self, page: Any, ctm: Any) -> None:
        self.current_page = PageOfTextBoxes([])
        self.pages.append(self.current_page)

    def end_page(self, page: Any) -> None:
        pass

    @classmethod
    def is_font_bold(cls, font: PDFFont) -> bool:
        if not hasattr(font, 'is_bold'):
            font.is_bold = 'bold' in font.fontname or 'Bold' in font.fontname
        return cast(bool, font.is_bold)

    @classmethod
    def cid_to_string(cls, font: PDFFont, cid: int) -> str:
        text: str
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
        return text

    def render_char(self, matrix: Sequence[float], font: PDFFont, fontsize: float, scaling: float, rise: float, cid: int, *_args: Any) -> float:
        # We need to support multiple pdfminer versions simultaneously.
        # Hence the *args
        # pylint: disable=arguments-differ,too-many-arguments
        text = self.cid_to_string(font, cid)

        textwidth: float = font.char_width(cid) * fontsize * scaling

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
            if unscaled_width_of_space in (1.0, 0.0):
                # Workaround for missing default width of space
                # e.g. the font does not define the space character
                unscaled_width_of_space = 0.25
            textbox = TextBox(
                x=matrix[4],
                y=round(matrix[5], 3),
                width=textwidth * matrix[0],
                width_of_space=unscaled_width_of_space * fontsize * scaling * matrix[0],
                content=text,
                bold=self.is_font_bold(font),
            )
            assert self.current_page is not None
            self.current_page.textboxes.append(textbox)
        return textwidth

    # TODO: parse graphical lines, so that footers can be detected more easily


@attr.s(slots=True)
class PageOfLines:
    lines: List[IndentedLine] = attr.ib(factory=list, converter=list)

    def add_line(self, line: IndentedLine) -> None:
        self.lines.append(line)


@attr.s(slots=True)
class PdfOfLines:
    pages: List[PageOfLines] = attr.ib(factory=list, converter=list)

    def add_page(self, page: PageOfLines) -> None:
        self.pages.append(page)


def extract_textboxes(f: PDFFileDescriptor) -> PdfOfTextBoxes:
    rsrcmgr = PDFResourceManager()
    device = PDFMinerAdapter(rsrcmgr)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.get_pages(f.fp):
        interpreter.process_page(page)
    return PdfOfTextBoxes(device.pages)


def sort_textboxes_into_dicts(textboxes: Iterable[TextBox]) -> Dict[float, Dict[float, TextBox]]:
    textboxes_as_dicts: Dict[float, Dict[float, TextBox]] = {}
    for tb in textboxes:
        if tb.y not in textboxes_as_dicts:
            # TODO: quantize y if needed. We are only lucky that
            # lines don't have an epsilon amount of y space between words
            # And that sub and superscripts are not used
            textboxes_as_dicts[tb.y] = {}
        if tb.x in textboxes_as_dicts[tb.y]:
            if tb.content != textboxes_as_dicts[tb.y][tb.x].content:
                raise ValueError(
                    "Multiple textboxes on the exact same coordinates"
                    "(Already there: '{}', to-be-inserted: '{}')"
                    .format(textboxes_as_dicts[tb.y][tb.x], tb.content)
                )
        else:
            textboxes_as_dicts[tb.y][tb.x] = tb

    # Consolidate boxes into lines, i.e. try to put characters
    # from the same line to the same "y" bucket.
    last_y_coord = None
    for y_coord in sorted(textboxes_as_dicts):
        # TODO: instad of 0.2, use some real line height thing
        # 0.2 is small enough not to trigger for the e.g. the 2 in "m2" (the unit).
        # And this is okay for now
        if last_y_coord is not None and abs(y_coord-last_y_coord) < 0.2:
            # TODO: let's hope there is no intersection between the previous line's
            # X coordinates and the current one. There shouldn't be any though.
            textboxes_as_dicts[last_y_coord].update(textboxes_as_dicts[y_coord])
            # Deleting elements during this iteration should be okay,
            # because "sorted" creates a copy of the keys
            del textboxes_as_dicts[y_coord]
        else:
            last_y_coord = y_coord

    return textboxes_as_dicts


def convert_textbox_dict_to_line(textbox_dict: Dict[float, TextBox], rightmost_on_page: float) -> IndentedLine:
    parts = []
    threshold_to_space = None
    prev_x = 0.0
    margin_right = 0.0
    for x in sorted(textbox_dict):
        box = textbox_dict[x]
        if threshold_to_space is not None and (x > threshold_to_space or box.content == '„'):
            if parts and parts[-1].content[-1] != ' ':
                parts.append(IndentedLinePart(threshold_to_space - prev_x, ' '))
                prev_x = threshold_to_space
        parts.append(IndentedLinePart(box.x - prev_x, box.content, box.bold))
        prev_x = box.x
        threshold_to_space = x + box.width + box.width_of_space * 0.5
        margin_right = rightmost_on_page - (box.x - box.width)

    return IndentedLine(tuple(parts), margin_right)


def extract_single_page(page: PageOfTextBoxes) -> PageOfLines:
    processed_page = PageOfLines()
    textboxes_as_dicts = sort_textboxes_into_dicts(page.textboxes)
    rightmost_on_page = max(tb.width + tb.x for tb in page.textboxes)
    prev_y = 0.0
    for y in sorted(textboxes_as_dicts, reverse=True):
        # TODO: don't hardcode the 18, but use actual textbox dimensions
        if prev_y != 0 and (prev_y - y) > 18:
            processed_page.add_line(EMPTY_LINE)
        prev_y = y
        processed_page.add_line(convert_textbox_dict_to_line(textboxes_as_dicts[y], rightmost_on_page))
    return processed_page


def extract_lines(potb: PdfOfTextBoxes) -> PdfOfLines:
    result = PdfOfLines()
    for page in potb.pages:
        result.add_page(extract_single_page(page))
    return result


PDF_OF_LINES_CONVERTER = dict2object.get_converter(PdfOfLines)


@Extractor(PDFFileDescriptor)
def CachedPdfParser(f: PDFFileDescriptor) -> Iterable[PdfOfLines]:
    cache_object = CacheObject(f.cache_id + ".parsed_v5.gz")
    if cache_object.exists():
        result = PDF_OF_LINES_CONVERTER.to_object(cache_object.read_json())
        yield result
    else:
        textboxes = extract_textboxes(f)
        result = extract_lines(textboxes)
        cache_object.write_json(PDF_OF_LINES_CONVERTER.to_dict(result))
        yield result
