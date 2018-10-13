#!/usr/bin/env python3
import sys
from law_tools.extractors.file import BinaryFile
from law_tools.extractors.all import do_extraction
from law_tools.extractors.hungarian_law import HungarianRawLaw
extracted = do_extraction([BinaryFile(sys.argv[1])])

for e in extracted:
    if isinstance(e, HungarianRawLaw):
        print("==== {} - {} =====\n".format(e.identifier, e.subject))
        for line in e.body:
            virtual_indent = ' '*int(line.indent*0.2)
            print(virtual_indent + line.content)
        print()
    else:
        print("Extracted object: {}\n".format(type(e)))
