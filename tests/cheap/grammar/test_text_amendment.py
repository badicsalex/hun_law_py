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
from hun_law.structure import TextAmendment

from tests.cheap.utils import ref

CASES: Tuple[Tuple[str, Tuple[TextAmendment, ...]], ...] = (
    (
        "A Bv. tv. 12. § (7) bekezdésében a „(4)–(5a) bekezdésben” szövegrész helyébe a „(4)–(5a) és (5c) bekezdésben” szöveg lép.",
        (
            TextAmendment(
                position=ref("Bv. tv.", "12", "7"),
                original_text="(4)–(5a) bekezdésben",
                replacement_text="(4)–(5a) és (5c) bekezdésben"
            ),
        )
    ),
    (
        "A Bv. tv. 12. § (8) bekezdésében a „(3)–(5a) bekezdés” szövegrész helyébe a „(3)–(5a) és (5c) bekezdés” szöveg, "
        "valamint a „(4)–(5a) bekezdés” szövegrészek helyébe a „(4)–(5a) és (5c) bekezdés” szöveg lép.",
        (
            TextAmendment(
                position=ref("Bv. tv.", "12", "8"),
                original_text="(3)–(5a) bekezdés",
                replacement_text="(3)–(5a) és (5c) bekezdés",
            ),
            TextAmendment(
                position=ref("Bv. tv.", "12", "8"),
                original_text="(4)–(5a) bekezdés",
                replacement_text="(4)–(5a) és (5c) bekezdés",
            ),
        )
    ),
    (
        "A Ptk. 7:43. § (3) bekezdése a „Semmis” szövegrész helyett az „Érvénytelen” szöveggel lép hatályba.",
        (
            TextAmendment(
                position=ref("Ptk.", "7:43", "3"),
                original_text="Semmis",
                replacement_text="Érvénytelen",
            ),
        )
    ),
    (
        "A Ptk. 4:129. § (2) bekezdése az „átmeneti nevelésbe vett vagy tartós nevelésbe vett” szövegrész helyett "
        "a „nevelésbe vett” szöveggel, az „a gyermeket a tartós nevelésbe vételt vagy az örökbefogadhatóvá "
        "nyilvánítást követően” szövegrész helyett az „a nevelésbe vett, örökbefogadható gyermeket” szöveggel lép hatályba.",
        (
            TextAmendment(
                position=ref("Ptk.", "4:129", "2"),
                original_text="átmeneti nevelésbe vett vagy tartós nevelésbe vett",
                replacement_text="nevelésbe vett",
            ),
            TextAmendment(
                position=ref("Ptk.", "4:129", "2"),
                original_text="a gyermeket a tartós nevelésbe vételt vagy az örökbefogadhatóvá nyilvánítást követően",
                replacement_text="a nevelésbe vett, örökbefogadható gyermeket",
            ),
        )
    ),
    (
        "A Ptk. 3:186. § (1) bekezdés b) pontjában és a 3:263. § (1) bekezdés b) pontjában „az utolsó beszámoló szerinti üzleti "
        "év könyveinek lezárása óta kimutatott, az előző üzleti évi” szövegrész helyébe „a közbenső mérlegben kimutatott” "
        "szöveg lép.",
        (
            TextAmendment(
                position=ref("Ptk.", "3:186", "1", "b"),
                original_text="az utolsó beszámoló szerinti üzleti év könyveinek lezárása óta kimutatott, az előző üzleti évi",
                replacement_text="a közbenső mérlegben kimutatott",
            ),
            TextAmendment(
                position=ref("Ptk.", "3:263", "1", "b"),
                original_text="az utolsó beszámoló szerinti üzleti év könyveinek lezárása óta kimutatott, az előző üzleti évi",
                replacement_text="a közbenső mérlegben kimutatott",
            ),
        )
    ),
    (
        "A Polgári Törvénykönyvről szóló 2013. évi V. törvény 3:88. § (2) bekezdésében a „tárgyévi adózott eredménye, illetve” "
        "szövegrész helyébe az „az előző üzleti évi adózott eredménnyel kiegészített” szöveg lép.",
        (
            TextAmendment(
                position=ref("2013. évi V. törvény", "3:88", "2"),
                original_text="tárgyévi adózott eredménye, illetve",
                replacement_text="az előző üzleti évi adózott eredménnyel kiegészített",
            ),
        )
    ),
    (
        "A Polgári Törvénykönyvről szóló 2013. évi V. törvény  3:331. § (3) bekezdésében a „jogtanácsosa” szövegrészek helyébe "
        "a „kamarai jogtanácsosa” szöveg lép.",
        (
            TextAmendment(
                position=ref("2013. évi V. törvény", "3:331", "3"),
                original_text="jogtanácsosa",
                replacement_text="kamarai jogtanácsosa",
            ),
        )
    ),
    (
        "A Teszt tv. 28. §-ában az „idézőjelek „idézőjelekben” jellegű” szövegrész helyébe a  „„na ne” ” szövegrész lép.",
        (
            TextAmendment(
                position=ref("Teszt tv.", "28"),
                original_text="idézőjelek „idézőjelekben” jellegű",
                replacement_text="„na ne”",
            ),
        )
    ),
    (
        "A Teszt tv. 29. §-ában az „idézőjelek„ idéző„j”elekben ”jellegű” szövegrész helyébe a  „ „na ne”” szövegrész lép.",
        (
            TextAmendment(
                position=ref("Teszt tv.", "29"),
                original_text="idézőjelek„ idéző„j”elekben ”jellegű",
                replacement_text="„na ne”",
            ),
        )
    ),
    (
        "A Btk. 294. § (1) bekezdésében és 296. § (1) bekezdésében az „előnyt kér, az előnyt” szövegrész helyébe a „jogtalan előnyt kér, a jogtalan előnyt”, az „előny kérőjével” szövegrész helyébe a „jogtalan előny kérőjével” szöveg lép.",
        (
            TextAmendment(
                position=ref("Btk.", "294", "1"),
                original_text="előnyt kér, az előnyt",
                replacement_text="jogtalan előnyt kér, a jogtalan előnyt",
            ),
            TextAmendment(
                position=ref("Btk.", "294", "1"),
                original_text="előny kérőjével",
                replacement_text="jogtalan előny kérőjével",
            ),
            TextAmendment(
                position=ref("Btk.", "296", "1"),
                original_text="előnyt kér, az előnyt",
                replacement_text="jogtalan előnyt kér, a jogtalan előnyt",
            ),
            TextAmendment(
                position=ref("Btk.", "296", "1"),
                original_text="előny kérőjével",
                replacement_text="jogtalan előny kérőjével",
            ),
        )
    )
)


@pytest.mark.parametrize("s,correct_metadata", CASES)  # type: ignore
def test_text_amendment_parsing(s: str, correct_metadata: Tuple[TextAmendment, ...]) -> None:
    parsed = GrammaticalAnalyzer().analyze(s, print_result=True)
    parsed_metadata = parsed.semantic_data
    assert correct_metadata == parsed_metadata
