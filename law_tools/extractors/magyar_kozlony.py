from collections import namedtuple

from . import Extractor
from .pdf import PdfOfLines, IndentedLine, EMPTY_LINE

def is_magyar_kozlony(pdf_file):
    if 'MAGYAR KÖZLÖNY' in pdf_file.pages[0].lines[0].content:
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

    # MAGYAR KÖZLÖNY 71 . szám
    #
    # A MAGYAR KÖZTÁRSASÁG HIVATALOS LAPJA
    # 2011. június 28., kedd
    #

    result_pages = [PageWithHeader(pdf_file.pages[0].lines[:5], pdf_file.pages[0].lines[5:])]
    for page in pdf_file.pages:
        # Others are
        # 15202 M A G Y A R   K Ö Z L Ö N Y  •  2011. évi 71 . szám
        #
        result_pages.append(PageWithHeader(page.lines[:2], page.lines[2:]))
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

    # Don't parse the last page, as that's just a note from the editor and publisher
    # TODO: assert for this
    for page in kozlony.pages[:-1]:
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
        # This is where we do away with the "Page" abstraction, and further processing
        # can only use EMPTY_LINE to have some separation info.
        content_of_current_section.append(EMPTY_LINE)
    yield SECTION_TYPES[current_section_type](content_of_current_section)
