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
from html.parser import HTMLParser
from typing import Any

from hun_law.cli import GenerateCommand
from hun_law.structure import Act, EnforcementDate
from hun_law.utils import Date

from hun_law import dict2object


def test_json_output(tmpdir: Any) -> None:
    generator = GenerateCommand()
    generator.run(["json", "2013/185", "--output-dir", str(tmpdir)])
    body = json.load(tmpdir.join("2013. évi CLXXV. törvény.json").open())

    assert body["identifier"] == "2013. évi CLXXV. törvény"
    assert body["subject"] == "a gondnokoltak és az előzetes jognyilatkozatok nyilvántartásáról"
    assert body["preamble"] == ""

    assert body["children"][0]['__type__'] == "Subtitle"
    assert body["children"][0]['title'] == "A törvény hatálya"

    assert body["children"][4]['__type__'] == "Article"
    assert body["children"][4]['identifier'] == "3"
    assert body["children"][4]['children'][0]['identifier'] == '1'
    assert body["children"][4]['children'][0]['children'][0]['identifier'] == 'a'
    assert body["children"][4]['children'][0]['children'][0]['intro'] == "a gondnokolt"

    assert body["children"][34]['__type__'] == "Article"
    assert body["children"][34]['identifier'] == "29"
    assert body["children"][34]['children'][0]['intro'] == "Az illetékekről szóló 1990. évi XCIII. törvény 43. §-a következő (9) bekezdéssel egészül ki:"

    assert body["children"][36]['__type__'] == "Article"
    assert body["children"][36]['identifier'] == "31"
    assert body["children"][36]['children'][0]['text'] == "Hatályát veszti a gondnokoltak nyilvántartásáról szóló 2010. évi XVIII. törvény."

    # This should not throw
    act: Act = dict2object.to_object(body, Act)
    assert act.article('27').paragraph().semantic_data == (EnforcementDate(position=None, date=Date(2014, 3, 15)),)


class AFindingHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.a_tag_count = 0

    def reset_count(self) -> None:
        self.a_tag_count = 0

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if tag == 'a':
            self.a_tag_count = self.a_tag_count + 1

    def error(self, message: str) -> None:
        pass


def test_html_output_ptk(tmpdir: Any) -> None:

    # Just simply test if html output works.
    generator = GenerateCommand()
    generator.run(["html", "2013/31", "--output-dir", str(tmpdir)])

    parser = AFindingHTMLParser()
    parser.reset_count()
    parser.feed(tmpdir.join("2013. évi V. törvény.html").read())
    assert parser.a_tag_count > 50


def test_html_output_2018_123(tmpdir: Any) -> None:
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
