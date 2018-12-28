#!/usr/bin/env python3
# Copyright 2018 Alex Badics <admin@stickman.hu>
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

import sys
import os
import xml.etree.ElementTree as ET

from hun_law.extractors.kozlonyok_hu_downloader import KozlonyToDownload
from hun_law.extractors.all import do_extraction
from hun_law.output.html import generate_html_body_for_act
from hun_law.structure import Act
from hun_law.cache import init_cache

init_cache(os.path.join(os.path.dirname(__file__), 'cache'))

extracted = do_extraction([KozlonyToDownload(sys.argv[1], sys.argv[2])])


def generate_head_section(title_text):
    head = ET.Element('head')
    title = ET.SubElement(head, 'title')
    title.text = title_text
    ET.SubElement(head, 'meta', {'http-equiv': "Content-Type", 'content': "text/html; charset=utf-8"})
    ET.SubElement(head, 'link', {'rel': "stylesheet", 'href': 'style.css'})
    return head


def generate_html_document_for_act(act, output_file):
    html = ET.Element('html')
    html.append(generate_head_section(act.identifier))

    body = ET.SubElement(html, 'body')
    body.text = "\n"
    body.append(generate_html_body_for_act(act))
    document = ET.ElementTree(html)
    output_file.write('<!DOCTYPE html>\n')
    document.write(output_file, encoding="unicode", method="html", xml_declaration=True)


for e in extracted:
    if not isinstance(e, Act):
        continue
    print("Generating {}.html".format(e.identifier))
    with open(os.path.join('html', e.identifier + '.html'), 'w') as f:
        generate_html_document_for_act(e, f)
