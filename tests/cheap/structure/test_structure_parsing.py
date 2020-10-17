# Copyright 2019 Alex Badics <admin@stickman.hu>
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
import sys
from typing import Iterable, Any

import pytest

from hun_law import dict2object

from tests.cheap.utils import quick_parse_structure


def structure_testcase_provider() -> Iterable[Any]:
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    for fname in sorted(os.listdir(data_dir)):
        if not fname.endswith('.txt'):
            continue
        input_fname = os.path.join(data_dir, fname)
        output_fname = input_fname.replace('.txt', '.json')
        with open(input_fname) as infile, open(output_fname) as outfile:
            yield pytest.param(
                infile.read(),
                json.load(outfile),
                id=fname
            )


@pytest.mark.parametrize("text,expected_structure", structure_testcase_provider())
def test_structure_parsing_exact(text: str, expected_structure: Any) -> None:
    resulting_structure = quick_parse_structure(text)
    result_as_dict = dict2object.to_dict(resulting_structure, type(resulting_structure))

    json.dump(result_as_dict, sys.stdout, indent='    ', ensure_ascii=False, sort_keys=True)

    assert result_as_dict == expected_structure


def test_quoting_parsing() -> None:
    text = """
         1. § Az Önkéntes Kölcsönös Biztosító Pénztárakról szóló 1993. évi XCVI. törvény 40/A. § (1) bekezdésében
              az „a Ptk. 2:47. § (1) bekezdésében” szövegrész helyébe az „az üzleti titok védelméről szóló 2018. évi LIV. törvény
              1. § (1) bekezdésében” szöveg lép.
         2. § A második szakasz viszont mar
              „Csodalatos quote-olt blokk”
              meghozzá szöveggel utána
         3. § A harmadik szakasz pedig
              „Többet is tartalmaz”
              „Egyes idezett szövegeket
              több sorban is
              akár”

              “Kihagzott sorokkal, „nestelt

              idezetekkel” es egyeb
              finomsagokkal”
              meg persze idezojelen kivuli
              befejezessel.
    """
    resulting_structure = quick_parse_structure(text)
    assert resulting_structure.article("1").paragraph().text is not None

    paragraph = resulting_structure.article("2").paragraph()
    assert paragraph.children_type is not None
    assert paragraph.children is not None
    assert len(paragraph.children) == 1
    assert paragraph.intro is not None
    assert paragraph.wrap_up is not None

    paragraph = resulting_structure.article("3").paragraph()
    assert paragraph.children_type is not None
    assert paragraph.children is not None
    assert len(paragraph.children) == 3
    assert paragraph.intro is not None
    assert paragraph.wrap_up is not None


def test_quoting_parsing_2() -> None:
    text = """
       1. § A földgázellátásról szóló 2008. évi XL. törvény 48. § (4) bekezdésében az „a villamos energiáról szóló 2007. évi
                LXXXVI. törvény szerinti átviteli rendszerirányítóra” szövegrész helyébe az „a rendszerirányítást végző szállítási
                rendszerüzemeltetőre és a villamos energiáról szóló 2007. évi LXXXVI. törvény szerinti átviteli rendszerirányítóra”
                szöveg lép.
       2. § Ez a törvény a kihirdetését követő 15. napon lép hatályba.
    """

    resulting_structure = quick_parse_structure(text)
    assert resulting_structure.article("1").paragraph().text is not None
    assert resulting_structure.article("2").paragraph().text is not None


def test_multiline_article_header() -> None:
    text = """
       294. § [A fővárosi és megyei kormányhivatalokról, valamint a fővárosi és megyei kormányhivatalok kialakításával és a területi
                integrációval összefüggő törvénymódosításokról szóló 2010. évi CXXVI. törvény egyes rendelkezéseinek hatályon kívül
                helyezése]
             (1) Hatályát veszti a fővárosi és megyei kormányhivatalokról, valamint a fővárosi és megyei kormányhivatalok
                kialakításával és a területi integrációval összefüggő törvénymódosításokról szóló 2010. évi CXXVI. törvény
                (a továbbiakban: Khtv.)
                a) 1–20/F. §-a,
                b) 21. § a)–f) pontja,
                c) 21/A. §-a,
                d) 21/B. § (1) bekezdése.
             (2) Hatályát veszti a Khtv.
                a) 21/B. § (3) bekezdésében az „– a szakmai irányító miniszter véleményének kikérésével –”,
                b) 21/B. § (4) bekezdésében az „a szakmai irányító miniszter egyetértésével kiadott”
                szövegrész.
    """
    resulting_structure = quick_parse_structure(text)
    article = resulting_structure.article("294")
    assert article.title is not None
    assert len(article.title) == 348
