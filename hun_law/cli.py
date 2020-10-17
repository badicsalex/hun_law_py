# Copyright 2018-2019 Alex Badics <admin@stickman.hu>
#
# This file is part of Hun-Law.
#
# Hun-Law is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hun-Law is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hun-Law.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import sys
import os
from typing import Sequence, TextIO, Union

from hun_law.extractors.act import BlockAmendmentOnlyAct, StructureOnlyAct
from hun_law.extractors.kozlonyok_hu_downloader import KozlonyToDownload
from hun_law.extractors.magyar_kozlony import MagyarKozlonyLawRawText
from hun_law.extractors.all import do_extraction
from hun_law.output.json import serialize_to_json_file
from hun_law.output.txt import write_txt
from hun_law.output.html import generate_html_for_act
from hun_law.structure import Act
from hun_law.cache import init_cache

GENERATOR_DESCRIPTION = """
Hun-Law output generator.

Downloads Magyar Közlöny issues as PDFs and converts the Acts in them to machine-parseable formats.
"""


class GenerateCommand:
    EXTRACTION_STEP_TO_CLASS = {
        'full': Act,
        'structure_only': StructureOnlyAct,
        'ba_only': BlockAmendmentOnlyAct,
        'raw_act': MagyarKozlonyLawRawText,
    }

    def __init__(self) -> None:
        self.argparser = argparse.ArgumentParser(description=GENERATOR_DESCRIPTION)
        self.argparser.add_argument(
            'output_format', choices=('txt', 'json', 'html'), metavar='output_format',
            help="Format of output."
        )
        # Declared as a separate function to have nice help messages when
        # the suppied argument is invalid

        def issue(s: str) -> KozlonyToDownload:
            year, act = s.split('/', 1)
            return KozlonyToDownload(int(year), int(act))

        self.argparser.add_argument(
            'issues', nargs='+', metavar='issue', type=issue,
            help="The  Magyar Közlöny issue to download in YEAR/ISSUE format. Example: '2013/31'"
        )
        self.argparser.add_argument(
            '--output-dir', '-o',
            default=None,
            help="Directory to put output files into. If not specified, output is printed to stdout."
        )
        self.argparser.add_argument(
            '--single-act', '-s', default=None,
            help="Extract only a single Act from the MK issue. "
            "Useful for printing single documents to stdout. "
            "Only supported with full parses. "
            "Example: '2013. évi V. törvény'"
        )
        self.argparser.add_argument(
            '--extraction-step', '-e', default="full",
            choices=tuple(sorted(self.EXTRACTION_STEP_TO_CLASS.keys())),
            help="Stop at a specific extraction/parsing step, instead of doing a full parse."
        )
        self.argparser.add_argument(
            '--workers', '-j', default=1,
            type=int,
            help="Worker processes to use for extraction. One worker works on a whole issue at once. 1 means single process mode."
        )

    def run(self, argv: Sequence[str]) -> None:
        init_cache(os.path.join(os.path.dirname(__file__), '..', 'cache'))
        parsed_args = self.argparser.parse_args(argv)
        if parsed_args.output_dir is not None:
            os.makedirs(parsed_args.output_dir, exist_ok=True)

        if parsed_args.workers > 1:
            worker_mode = "using at most {} worker processes".format(parsed_args.workers)
        else:
            worker_mode = "using single-threaded mode"

        print("Starting extraction of {} issue(s) {}".format(len(parsed_args.issues), worker_mode), file=sys.stderr)
        output_fn = getattr(self, "output_" + parsed_args.output_format)
        output_class = self.EXTRACTION_STEP_TO_CLASS[parsed_args.extraction_step]
        for extracted in do_extraction(parsed_args.issues, (output_class,), workers=parsed_args.workers):
            if output_class in (BlockAmendmentOnlyAct, StructureOnlyAct):
                extracted = extracted.act
            if output_class in (Act, MagyarKozlonyLawRawText):
                if parsed_args.single_act is not None and extracted.identifier != parsed_args.single_act:
                    print("Not outputting {}".format(extracted.identifier), file=sys.stderr)
                    continue
            if parsed_args.output_dir is not None:
                file_path = os.path.join(
                    parsed_args.output_dir,
                    "{}.{}".format(extracted.identifier, parsed_args.output_format)
                )
                print("Writing {}".format(file_path), file=sys.stderr)
                with open(file_path, 'w') as output_file:
                    output_fn(extracted, output_file)
            else:
                output_fn(extracted, sys.stdout)

    @classmethod
    def output_txt(cls, extracted: Union[Act, MagyarKozlonyLawRawText], output_file: TextIO) -> None:
        write_txt(output_file, extracted)

    @classmethod
    def output_json(cls, extracted: Union[Act, MagyarKozlonyLawRawText], output_file: TextIO) -> None:
        serialize_to_json_file(extracted, output_file)

    @classmethod
    def output_html(cls, extracted: Union[Act, MagyarKozlonyLawRawText], output_file: TextIO) -> None:
        if not isinstance(extracted, Act):
            raise TypeError("Html output is only supported for Acts")
        generate_html_for_act(extracted, output_file)
