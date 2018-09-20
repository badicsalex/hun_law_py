#!/usr/bin/env python3
import sys
from extractors.file import BinaryFile
from extractors.all import do_extraction

extracted = do_extraction([BinaryFile(sys.argv[1])])

print(extracted)
