from . import Extractor
from .pdf import PdfOfLines

class NotKozlonyError(ValueError):
    pass

class KozlonyCollector:
    def __init__(self):
        self.on_cover_page = True
        self.line_number = -1

    def handle_next_page(self):
        self.on_cover_page = False
        self.line_number = -1
        print()
        print('===== PAGE =====')
        print()

    def handle_line(self, line):
        self.line_number = self.line_number + 1
        if self.on_cover_page:
            # MAGYAR  KÖZLÖNY 107 . szám
            # A MAGYAR KÖZTÁRSASÁG HIVATALOS LAPJA
            # 2011. szeptember 19., hétfõ
            # TODO: moar asserts
            if self.line_number == 0 and 'MAGYAR  KÖZLÖNY' not in line.content:
                print(line)
                raise NotKozlonyError
            if self.line_number < 3:
                return
        else:
            if self.line_number == 0:
                # 28402 M A G Y A R   K Ö Z L Ö N Y  •  2011. évi 107 . szám
                # TODO: assert for page header
                return
        print(line.content)

@Extractor(PdfOfLines)
def MagyarKozlonyExtractor(pdf_file):
    collector = KozlonyCollector()
    try:
        for page in pdf_file.pages:
            for line in page.lines:
                collector.handle_line(line)
            collector.handle_next_page()
    except NotKozlonyError:
        return
    yield None
