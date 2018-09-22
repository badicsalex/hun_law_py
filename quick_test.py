#!/usr/bin/env python3
import sys
from law_tools.extractors.file import BinaryFile
from law_tools.extractors.all import do_extraction
from law_tools.extractors.magyar_kozlony import MagyarKozlonyLaws
extracted = do_extraction([BinaryFile(sys.argv[1])])

for e in extracted:
    print("Extractied object: {}".format(type(e)))
    if isinstance(e, MagyarKozlonyLaws):
        for line in e.lines:
            virtual_indent = ' '*int(line.indent*0.2)
            print(virtual_indent + line.content)
