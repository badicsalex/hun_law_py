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
from collections import namedtuple

from hun_law.extractors.kozlonyok_hu_downloader import KozlonyToDownload
from hun_law.extractors.all import do_extraction
from hun_law.output.json import serialize_act_to_json_file
from hun_law.output.txt import write_txt
from hun_law.output.html import generate_html_for_act
from hun_law.structure import Act
from hun_law.cache import init_cache

GENERATOR_DESCRIPTION = """
Hun-Law output generator.

Downloads Magyar Közlöny issues as PDFs and converts the Acts in them to machine-parseable formats.
"""


class GenerateCommand:
    def __init__(self):
        self.argparser = argparse.ArgumentParser(description=GENERATOR_DESCRIPTION)
        self.argparser.add_argument(
            'output_format', choices=('txt', 'json', 'html'), metavar='output_format',
            help="Format of output."
        )
        # Declared as a separate function to have nice help messages when
        # the suppied argument is invalid

        def issue(s):
            return KozlonyToDownload(*s.split('/', 1))
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
            "Example: '2013. évi V. törvény'"
        )

    def run(self, argv):
        init_cache(os.path.join(os.path.dirname(__file__), 'cache'))
        parsed_args = self.argparser.parse_args(argv)
        if parsed_args.output_dir is not None:
            os.makedirs(parsed_args.output_dir, exist_ok=True)

        print("Starting extraction of {} issue(s)".format(len(parsed_args.issues)))
        output_fn = getattr(self, "output_" + parsed_args.output_format)
        for act in do_extraction(parsed_args.issues, (Act,)):
            if parsed_args.single_act is not None and act.identifier != parsed_args.single_act:
                print("Not outputting {}".format(act.identifier), file=sys.stderr)
                continue
            if parsed_args.output_dir is not None:
                file_path = os.path.join(
                    parsed_args.output_dir,
                    "{}.{}".format(act.identifier, parsed_args.output_format)
                )
                print("Writing {}".format(file_path))
                with open(file_path, 'w') as output_file:
                    output_fn(act, output_file)
            else:
                output_fn(act, sys.stdout)

    @classmethod
    def output_txt(cls, act, output_file):
        write_txt(output_file, act)

    @classmethod
    def output_json(cls, act, output_file):
        serialize_act_to_json_file(act, output_file)

    @classmethod
    def output_html(cls, act, output_file):
        generate_html_for_act(act, output_file)
