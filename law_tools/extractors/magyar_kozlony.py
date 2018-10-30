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

import enum
import re
from collections import namedtuple

from law_tools.utils import EMPTY_LINE

from . import Extractor
from .pdf import PdfOfLines


def is_magyar_kozlony(pdf_file):
    # TODO: Lets hope justified text detector works, and it's not something like
    # 'M A G Y A R K O Z L O N Y
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
MagyarKozlonyLawsSection = namedtuple('MagyarKozlonyLawsSection', ['lines'])

SECTION_TYPES = {
    'Tartalomjegyzék': MagyarKozlonyToC,
    'II. Törvények': MagyarKozlonyLawsSection,
    # TODO: tons of stuff, like 'III. Kormányrendeletek', 'V. A Kormány tagjainak rendeletei'
}


@Extractor(KozlonyPagesWithHeaderAndFooter)
def MagyarKozlonySectionExtractor(kozlony):
    current_section_type = None
    content_of_current_section = []

    # Don't parse the last page, as that's just a note from the editor and publisher
    # TODO: assert for this
    for page in kozlony.pages[:-1]:
        for section_type in SECTION_TYPES:
            # This is not something like 'page.lines[0] in SECTION_TYPES' to allow for more
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


MagyarKozlonyLawRawText = namedtuple('MagyarKozlonyLawRawText', ['identifier', 'subject', 'body'])


@Extractor(MagyarKozlonyLawsSection)
def MagyarKozlonyLawExtractor(laws_section):
    States = enum.Enum("States",
        [
            "WAITING_FOR_HEADER",
            "HEADER",
            "BODY_BEFORE_ASTERISK_FOOTER",
            "BODY_AFTER_ASTERISK_FOOTER",
        ]
    )
    header_starting_re = re.compile('^[12][09][0-9][0-9]. évi [IVXLC]+. törvény')
    footer_re = re.compile('köztársasági elnök az Országgyűlés elnöke')

    identifier = ''
    subject = ''
    body = []

    state = States.WAITING_FOR_HEADER
    for line in laws_section.lines:
        if state == States.WAITING_FOR_HEADER:
            if not header_starting_re.match(line.content):
                continue
            identifier = line.content
            state = States.HEADER
            continue

        if state == States.HEADER:
            if subject != '':
                subject = subject + ' ' + line.content
            else:
                subject = line.content
            # TODO: this is alwo a huge hack, because it depend on there being a footer about
            # when the law or amendment was enacted and by whom.
            if subject[-1] == '*':
                subject = subject[:-1]
                state = States.BODY_BEFORE_ASTERISK_FOOTER
            continue

        if state in (States.BODY_BEFORE_ASTERISK_FOOTER, States.BODY_AFTER_ASTERISK_FOOTER):
            body.append(line)
            # TODO: this is also a hack that depends on the things below being true
            if len(body) < 4:
                continue

            # TODO: this whole asterisk footer whatever is ugly. The footer should be detected
            # in extractors before this one, based on other cues.
            # Also let's just hope there are no two small laws on a single page
            if state == States.BODY_BEFORE_ASTERISK_FOOTER:
                if body[-3] == EMPTY_LINE and body[-1] == EMPTY_LINE and body[-2].content[0] == '*':
                    body = body[:-3] + [EMPTY_LINE]
                    state = States.BODY_AFTER_ASTERISK_FOOTER
                    continue

            if body[-3] == EMPTY_LINE and footer_re.match(body[-1].content):
                # TODO: Extract footer
                yield MagyarKozlonyLawRawText(
                    identifier,
                    subject,
                    body[:-3]
                )
                identifier = ''
                subject = ''
                body = []
                state = States.WAITING_FOR_HEADER
            continue

        # TODO: extract Annexes

        raise ValueError("What state is this.")
    # TODO: assert for correct state
