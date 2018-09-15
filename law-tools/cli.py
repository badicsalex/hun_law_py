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
        self.items = []

    def begin_page(self, page, ctm):
        print("==BEGIN==", page, ctm)

    def end_page(self, page):
        print("==END==", page)

    def render_string(self, textstate, seq):
        actual_chars = []
        for s in seq:
            if isnumber(s):
                if s < textstate.charspace:
                    actual_chars.append(' ')
                continue

            for c in s:
                try:
                    uni_c = textstate.font.to_unichr(c)
                except PDFUnicodeNotDefined:
                    uni_c = '[X]'
                actual_chars.append(uni_c)
        print(''.join(actual_chars))

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
    boilerplate(f)
