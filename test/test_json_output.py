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

from hun_law.extractors.kozlonyok_hu_downloader import KozlonyToDownload
from hun_law.extractors.all import do_extraction
from hun_law.cache import init_cache
from hun_law.output.json import serialize_act_to_json_compatible
from hun_law.structure import Act


def parse_single_kozlony(year, issue):
    init_cache(os.path.join(os.path.join(os.path.dirname(__file__), '..'), 'cache'))
    extracted = do_extraction([KozlonyToDownload(year, issue)])
    return extracted


def test_html_output_ptk():
    acts = {a.identifier: a for a in parse_single_kozlony(2013, 185) if isinstance(a, Act)}
    assert len(acts) == 11, "Issue 2013/185 of Magyar Kozlony contains 11 separate Acts"

    body = serialize_act_to_json_compatible(acts["2013. évi CLXXV. törvény"])
    assert json.loads(json.dumps(body)) == body, "The output is json serializable"

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
