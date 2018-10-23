#!/usr/bin/env python3
import sys
from law_tools.extractors import Extractor
from law_tools.extractors.file import BinaryFile
from law_tools.extractors.all import do_extraction
from law_tools.extractors.hungarian_law import MagyarKozlonyLawRawText
from law_tools.hun_law.structure import Act

#@Extractor(MagyarKozlonyLawRawText)
def RawLawPrinter(e):
    print("==== RAW TEXT FOR {} - {} =====\n".format(e.identifier, e.subject))
    for line in e.body:
        virtual_indent = ' '*int(line.indent*0.2)
        print(virtual_indent + line.content)
    print()
    # Empty generator hack
    return
    yield

@Extractor(Act)
def ActPrinter(e):
    print("==== Structured text of {} - {} =====\n".format(e.identifier, e.subject))
    e.print_to_console()
    # Empty generator hack
    return
    yield

extracted = do_extraction([BinaryFile(sys.argv[1])])

for e in extracted:
    print("Final extracted object: {}\n".format(type(e)))
