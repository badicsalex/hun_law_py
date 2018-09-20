#!/usr/bin/env python3
import sys

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfdevice import PDFTextDevice
from pdfminer.utils import isnumber
from pdfminer.pdffont import PDFUnicodeNotDefined

class LowLevelPdfExtractor(PDFTextDevice):
    def __init__(self, rsrcmgr):
        super().__init__(rsrcmgr)
        self.pages = []

    def begin_page(self, page, ctm):
        self.lines = {}

    def end_page(self, page):
        self.pages.append(self.lines)

    def append_to_line(self, s, y_coordinate):
        if y_coordinate not in self.lines:
            self.lines[y_coordinate] = s
        else:
            self.lines[y_coordinate] = self.lines[y_coordinate] + ' ' + s

    def render_string(self, textstate, seq):
        net_scaling = textstate.fontsize * textstate.scaling * 0.0001
        # Sometimes the space char is used instead of "repositionings", with a little hack
        # where space is actually very short, or even of negative length
        space_is_not_used_for_space = textstate.wordspace < -1

        actual_chars = []
        for s in seq:
            if isnumber(s):
                # horizontal repositioning
                reposition_diff = s * net_scaling
                if reposition_diff < -1.5:
                    # This is two cases as one right now:
                    # 1) Tabulating and things like table of contents. We flatten it to space for now, for
                    #    easier downstream processing. This may change if messy things (like characters not
                    #    present in the document left to right, etc.
                    # 2) Justified text sometimes use these "reposition"s instead of space characters,
                    #    if the width of the space is different for each word
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
                        uni_c = '[X]'
                    actual_chars.append(uni_c)
        y_coordinate = textstate.matrix[5]
        self.append_to_line(''.join(actual_chars), y_coordinate)

    def render_char(self, matrix, font, fontsize, scaling, rise, cid):
        text = font.to_unichr(cid)
        textwidth = font.char_width(cid)
        self.items.append(text)
        x = matrix[4]
        y = matrix[5]
        print(text, x, y)
        return textwidth * fontsize * scaling

def boilerplate(in_file):
    rsrcmgr = PDFResourceManager()
    device = LowLevelPdfExtractor(rsrcmgr)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.get_pages(in_file):
        interpreter.process_page(page)
    return device

with open(sys.argv[1], 'rb') as f:
    extracted = boilerplate(f)
    for page in extracted.pages:
        for line_index in sorted(page, reverse=True):
            print(page[line_index])
        print('')
        print('============')
        print('')
