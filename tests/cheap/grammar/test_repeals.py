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

from typing import Tuple

import pytest

from hun_law.parsers.grammatical_analyzer import GrammaticalAnalyzer
from hun_law.structure import Repeal

from tests.cheap.utils import ref

CASES: Tuple[Tuple[str, Tuple[Repeal, ...]], ...] = (
    (
        "Nem lép hatályba a Ptk. 3:329. § (3) bekezdése.",
        (
            Repeal(position=ref("Ptk.", "3:329", "3")),
        )
    ),
    (
        "Nem lép hatályba a Ptk. 3:404. § (4) bekezdése.",
        (
            Repeal(position=ref("Ptk.", "3:404", "4")),
        )
    ),
    (
        "Nem lép hatályba a Ptk. 5:96. § (3) bekezdésében az „A zálogjogosulti bizományos kérheti, hogy az ingatlan-nyilvántartás, a lajstrom vagy a hitelbiztosítéki nyilvántartás zálogjogosultként feltüntesse.” szövegrész.",
        (
            Repeal(position=ref("Ptk.", "5:96", "3"), text="A zálogjogosulti bizományos kérheti, hogy az ingatlan-nyilvántartás, a lajstrom vagy a hitelbiztosítéki nyilvántartás zálogjogosultként feltüntesse."),
        )
    ),
    (
        "Nem lép hatályba az Iktv. 116. § f) pontja.",
        (
            Repeal(position=ref("Iktv.", "116", None, "f")),
        )
    ),
    (
        "Hatályát veszti a Kttv. 164. § (2) bekezdése.",
        (
            Repeal(position=ref("Kttv.", "164", "2")),
        )
    ),
    (
        "Hatályát veszti a Pft. 18. § (1) bekezdés a) pontjában az „és a jogi személyiséggel nem rendelkező gazdasági társaság” szövegrész.",
        (
            Repeal(position=ref("Pft.", "18", "1", "a"), text="és a jogi személyiséggel nem rendelkező gazdasági társaság"),
        )
    ),
    (
        "Hatályát veszti a Jöt. 116/B. § (1) bekezdésében a „, jogi személyiség nélküli gazdasági társaság” szövegrész.",
        (
            Repeal(position=ref("Jöt.", "116/B", "1"), text=", jogi személyiség nélküli gazdasági társaság"),
        )
    ),
    (
        "Hatályát veszti az Eva tv. 2. § (3) bekezdés a) és e) pontjában, 11. § (4) bekezdésében, 18. § (5) és(10) bekezdésében, 19. § (1) és(2) bekezdésében, 22. § (4) és(10) bekezdésében az „, a jogi személyiség nélküli gazdasági társaság” szövegrész.",
        (
            Repeal(position=ref("Eva tv.", "2", "3", "a"), text=", a jogi személyiség nélküli gazdasági társaság"),
            Repeal(position=ref("Eva tv.", "2", "3", "e"), text=", a jogi személyiség nélküli gazdasági társaság"),
            Repeal(position=ref("Eva tv.", "11", "4"), text=", a jogi személyiség nélküli gazdasági társaság"),
            Repeal(position=ref("Eva tv.", "18", "5"), text=", a jogi személyiség nélküli gazdasági társaság"),
            Repeal(position=ref("Eva tv.", "18", "10"), text=", a jogi személyiség nélküli gazdasági társaság"),
            Repeal(position=ref("Eva tv.", "19", ("1", "2")), text=", a jogi személyiség nélküli gazdasági társaság"),
            Repeal(position=ref("Eva tv.", "22", "4"), text=", a jogi személyiség nélküli gazdasági társaság"),
            Repeal(position=ref("Eva tv.", "22", "10"), text=", a jogi személyiség nélküli gazdasági társaság"),
        )
    ),
    (
        "Hatályát veszti a Polgári Törvénykönyvről szóló 2013. évi V. törvény 6:155. § (2) bekezdése.",
        (
            Repeal(position=ref("2013. évi V. törvény", "6:155", "2")),
        )
    ),
    (
        "Hatályát veszti a Ptk. 8:6. § a), l), n) és p) pontja.",
        (
            Repeal(position=ref("Ptk.", "8:6", None, "a")),
            Repeal(position=ref("Ptk.", "8:6", None, "l")),
            Repeal(position=ref("Ptk.", "8:6", None, "n")),
            Repeal(position=ref("Ptk.", "8:6", None, "p")),
        )
    ),
    (
        "Hatályát veszti az Flt. 39. § (3) bekezdés a) pontjában az „a pályakezdők munkanélküli segélye, az előnyugdíj”, valamint az „az álláskeresést ösztönző juttatás” szövegrész.",
        (
            Repeal(position=ref("Flt.", "39", "3", "a"), text="a pályakezdők munkanélküli segélye, az előnyugdíj"),
            Repeal(position=ref("Flt.", "39", "3", "a"), text="az álláskeresést ösztönző juttatás"),
        )
    ),
)


@ pytest.mark.parametrize("s,correct_metadata", CASES)  # type: ignore
def test_text_amendment_parsing(s: str, correct_metadata: Tuple[Repeal, ...]) -> None:
    parsed = GrammaticalAnalyzer().analyze(s, print_result=True)
    parsed_metadata = parsed.semantic_data
    assert correct_metadata == parsed_metadata
