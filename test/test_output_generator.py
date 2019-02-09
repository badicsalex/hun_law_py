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

import json
import os
from html.parser import HTMLParser

from hun_law.cli import GenerateCommand


def test_json_output(tmpdir):
    generator = GenerateCommand()
    generator.run(["json", "2013/185", "--output-dir", str(tmpdir)])
    body = json.load(tmpdir.join("2013. évi CLXXV. törvény.json").open())

    assert body["id"] == "2013. évi CLXXV. törvény"
    assert body["subject"] == "a gondnokoltak és az előzetes jognyilatkozatok nyilvántartásáról"
    assert body["preamble"] == ""

    assert body["content"][0]['type'] == "Subtitle"
    assert body["content"][0]['title'] == "A törvény hatálya"

    assert body["content"][4]['type'] == "Article"
    assert body["content"][4]['id'] == "3"
    assert body["content"][4]['content']['1']['a']['_intro'] == "a gondnokolt"
    assert body["content"][4]['content']['1']['a']['ad'] == "anyjának születési családi és utónevét,"

    assert body["content"][34]['type'] == "Article"
    assert body["content"][34]['id'] == "29"
    assert body["content"][34]['content']['_intro'] == "Az illetékekről szóló 1990. évi XCIII. törvény 43. §-a következő (9) bekezdéssel egészül ki:"
    assert body["content"][34]['content']['content'] == "(9) Az előzetes jognyilatkozatok nyilvántartásba való bejegyzésének illetéke 15 000 forint."

    assert body["content"][36]['type'] == "Article"
    assert body["content"][36]['id'] == "31"
    assert body["content"][36]['content'] == "Hatályát veszti a gondnokoltak nyilvántartásáról szóló 2010. évi XVIII. törvény."


class AFindingHTMLParser(HTMLParser):
    def reset_count(self):
        self.a_tag_count = 0

    def handle_starttag(self, tag, attributes):
        if tag == 'a':
            self.a_tag_count = self.a_tag_count + 1


def test_html_output_ptk(tmpdir):

    # Just simply test if html output works.
    generator = GenerateCommand()
    generator.run(["html", "2013/31", "--output-dir", str(tmpdir)])

    parser = AFindingHTMLParser()
    parser.reset_count()
    parser.feed(tmpdir.join("2013. évi V. törvény.html").read())
    assert parser.a_tag_count > 50


def test_html_output_2018_123(tmpdir):
    # Just simply test if html output works on modern MK issues
    generator = GenerateCommand()
    generator.run(["html", "2018/123", "--output-dir", str(tmpdir)])
    acts = [
        "2018. évi LV. törvény.html",
        "2018. évi LIV. törvény.html",
        "2018. évi LIII. törvény.html",
        "2018. évi LII. törvény.html",
        "2018. évi LI. törvény.html",
        "2018. évi L. törvény.html",
    ]
    for act in acts:
        assert tmpdir.join(act).check(file=1)
