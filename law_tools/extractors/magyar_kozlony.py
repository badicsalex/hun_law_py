from collections import namedtuple

from . import Extractor
from .pdf import PdfOfLines, IndentedLine

def is_magyar_kozlony(pdf_file):
    if 'MAGYAR  KÖZLÖNY' in pdf_file.pages[0].lines[0].content:
        return True
    return False

PageWithHeader = namedtuple('PageWithHeader', ['header', 'lines'])
KozlonyPagesWithHeaderAndFooter = namedtuple('FullKozlonyPagesWithHeaderAndFooter', ['pages'])

@Extractor(PdfOfLines)
def MagyarKozlonyHeaderExtractor(pdf_file):
    if not is_magyar_kozlony(pdf_file):
        return
    # TODO: assert the header.

    # The first page is special:
    # MAGYAR  KÖZLÖNY 107 . szám
    # A MAGYAR KÖZTÁRSASÁG HIVATALOS LAPJA
    # 2011. szeptember 19., hétfõ

    result_pages = [PageWithHeader(pdf_file.pages[0].lines[:3], pdf_file.pages[0].lines[3:])]
    for page in pdf_file.pages:
        # Others are TODO
        result_pages.append(PageWithHeader(page.lines[:1], page.lines[1:]))
    yield KozlonyPagesWithHeaderAndFooter(result_pages)

MagyarKozlonyToC = namedtuple('MagyarKozlonyToC', ['lines'])
MagyarKozlonyLaws = namedtuple('MagyarKozlonyLaws', ['lines'])
MagyarKozlonyDecrees = namedtuple('MagyarKozlonyDecrees', ['lines'])
SECTION_TYPES = {
    'Tartalomjegyzék': MagyarKozlonyToC,
    'II. Törvények': MagyarKozlonyLaws,
    'III. Kormányrendeletek': MagyarKozlonyDecrees,
}

@Extractor(KozlonyPagesWithHeaderAndFooter)
def MagyarKozlonySectionExtractor(kozlony):
    current_section_type = None
    content_of_current_section = []
    for page in kozlony.pages:
        for section_type in SECTION_TYPES:
            # This is not somethign line 'page.lines[0] in SECTION_TYPES to allow for more
            # complex conditions, like regex section types later.
            if page.lines[0].content != section_type:
                continue
            if current_section_type == section_type:
                content_of_current_section.extend(page.lines[1:])
                break
            if current_section_type is not None:
                yield SECTION_TYPES[current_section_type](content_of_current_section)
            current_section_type = section_type
            content_of_current_section = page.lines[1:]
            break
        else:
            if current_section_type is None:
                raise ValueError("Unknown starting section: '{}'".format(page.lines[0]))
            content_of_current_section.extend(page.lines)
    yield SECTION_TYPES[current_section_type](content_of_current_section)
