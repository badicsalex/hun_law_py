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

from typing import Tuple, List
import pytest

from hun_law.parsers.grammatical_analyzer import GrammaticalAnalyzer
from hun_law.structure import ActIdAbbreviation


ABBREVIATION_CASES: Tuple[Tuple[str, List[ActIdAbbreviation]], ...] = (
    (
        "A hegyközségekről szóló 2012. évi CCXIX. törvény (a továbbiakban: Hktv.) 28. §-a helyébe a következő rendelkezés lép:",
        [ActIdAbbreviation('Hktv.', '2012. évi CCXIX. törvény')]
    ),
    (
        "A pénzügyi tranzakciós illetékről szóló 2012. évi CXVI. törvény (a továbbiakban: Pti. törvény) 7. § (1) bekezdése helyébe a következő rendelkezés lép:",
        [ActIdAbbreviation('Pti.', '2012. évi CXVI. törvény')]
    ),
    (
        "A víziközmű-szolgáltatásról szóló 2011. évi CCIX. törvény (a továbbiakban: Víziközmű tv.) 2. §-a a következő 31. ponttal egészül ki:",
        [ActIdAbbreviation("Víziközmű tv.", "2011. évi CCIX. törvény")],
    ),
    (
        "Az európai részvénytársaságról szóló 2004. évi XLV. törvény (a továbbiakban: Eurt.tv.) 2. §-a helyébe a következő rendelkezés lép:",
        [ActIdAbbreviation("Eurt.tv.", "2004. évi XLV. törvény")],
    ),
    (
        "E törvény rendelkezéseit a Polgári Törvénykönyvről szóló 2013. évi V. törvénnyel (a továbbiakban: Ptk.) együtt kell alkalmazni.",
        [ActIdAbbreviation("Ptk.", "2013. évi V. törvény")],
    ),
    (
        # Abbreviation used in the text itself
        "Nem kell módosítani, ha a szövetkezetekről szóló 2006. évi X. törvény (a továbbiakban: Sztv.) rendelkezéseire utal "
        "Amennyiben azonban az alapszabály egyéb okból módosul, a szövetkezet köteles az Sztv.-re utalást is módosítani.",
        [ActIdAbbreviation("Sztv.", "2006. évi X. törvény")],
    ),
    (
        # No colon
        "A fogyasztóvédelmi hatósága fogyasztóvédelemrõl szóló 1997. évi CLV. törvény (a továbbiakban Fgytv.) szabályai szerint jár el.",
        [ActIdAbbreviation("Fgytv.", "1997. évi CLV. törvény")],
    ),
    (
        "A szabálysértésekről és egyebekről szóló 2012. évi I. törvény (a továbbiakban: Szabs. tv.) 29. § (2) bekezdés e) pontja helyébe a következő rendelkezés lép:",
        [ActIdAbbreviation("Szabs. tv.", "2012. évi I. törvény")]
    ),
    (
        "A Magyarország 2013. évi központi költségvetéséről szóló 2012. évi CCIV. törvény 44/B. és 44/C. §-a helyébe a következő rendelkezés lép:",
        []
    ),
    (
        "A Kvtv. 72. §-a a következő (9)–(12) bekezdésekkel egészül ki:",
        []
    ),
    (
        "A Büntető Törvénykönyvről szóló 1978. évi IV. törvény (a továbbiakban: 1978. évi IV. törvény) 316. § (4) bekezdése csak úgy.",
        []
    ),
    (
        "A Büntető Törvénykönyvről szóló 1978. évi IV. törvény (a továbbiakban: 1978. évi IV. törvény) 316. § (4) bekezdése a következő c) ponttal egészül ki:",
        []
    ),
)


@pytest.mark.parametrize("s,abbrevs", ABBREVIATION_CASES)
def test_new_abbreviations(s: str, abbrevs: List[ActIdAbbreviation]) -> None:
    parsed = GrammaticalAnalyzer().analyze(s, print_result=True)
    new_abbrevs = list(parsed.act_id_abbreviations)
    assert new_abbrevs == abbrevs
