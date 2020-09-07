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

from typing import List, Tuple

import pytest

from hun_law.structure import Act, OutgoingReference, Reference, \
    SemanticData, BlockAmendmentMetadata, Repeal, \
    NumericPoint, AlphabeticSubpoint
from hun_law.parsers.semantic_parser import ActSemanticsParser

from .utils import ref, quick_parse_structure


CASES_WITHOUT_POSITIONS: List[Tuple[str, Tuple[Tuple[Reference, Reference], ...], Tuple[Tuple[Reference, SemanticData], ...]]] = [
    (
        """
            17. §          Hatályát veszti
                           a)   a Polgári Törvénykönyvről szóló 1959. évi IV. törvény 261. § (4) bekezdése,
                           b)   a Polgári Törvénykönyv hatálybalépéséről és végrehajtásáról szóló 1960. évi 11. törvényerejű
                                rendelet 83/A. §-a,
                           c)   az ingatlan-nyilvántartásról szóló 1997. évi CXLI. törvény 16/A. §-a és 91. § (2) bekezdése.
        """,
        (
            (ref(None, "17", None, "a"), ref("1959. évi IV. törvény")),
            (ref(None, "17", None, "a"), ref("1959. évi IV. törvény", "261", "4")),
            # TODO: Act-like decree ref in b)
            (ref(None, "17", None, "b"), ref(None, "83/A")),
            (ref(None, "17", None, "c"), ref("1997. évi CXLI. törvény")),
            (ref(None, "17", None, "c"), ref("1997. évi CXLI. törvény", "16/A")),
            (ref(None, "17", None, "c"), ref("1997. évi CXLI. törvény", "91", "2")),
        ),
        (
            (
                ref(None, "17", None, "a"),
                Repeal(position=ref("1959. évi IV. törvény", "261", "4")),
            ),
            (
                ref(None, "17", None, "c"),
                Repeal(position=ref("1997. évi CXLI. törvény", "16/A")),
            ),
            (
                ref(None, "17", None, "c"),
                Repeal(position=ref("1997. évi CXLI. törvény", "91", "2")),
            ),
        ),
    ),
    (
        """
        40. § (1)  A kisadózó vállalkozások tételes adójáról és a kisvállalati adóról szóló 2012. évi CXLVII. törvény (a továbbiakban: Katv.) 2. § 19–20. pontja helyébe a következő rendelkezés lép:
               „19. Torolve
                20. Torolve2”

        41. §   Hatályát veszti
                1. az illetékekről szóló 1990. évi XCIII. törvény 17. § (1) bekezdés c) pontjában a „vagy egészségügyi hozzájárulás” szövegrész;
                2. a számvitelről szóló 2000. évi C. törvény
                    a) 79. § (4) bekezdésében az „az egészségügyi hozzájárulás,” szövegrész;
                    b) 103. § (2) bekezdés c) pontjában az „egészségügyi hozzájárulás,” szövegrész;
                3. a különösen sok dologról szóló 2004. évi CXXIII. törvény
                    a) 8/A. §–8/B. §-a,
                    b) 16/A. §–16/B. §-a,
                    c) 17/A. § (1) és (3) bekezdése;
                4. a Katv. 2. § 21. pontja;
        """,
        (
            (ref(None, "40", "1"), ref("2012. évi CXLVII. törvény")),
            (ref(None, "40", "1"), ref("2012. évi CXLVII. törvény", "2", None, ("19", "20"))),
            (ref(None, "41", None, "1"), ref("1990. évi XCIII. törvény")),
            (ref(None, "41", None, "1"), ref("1990. évi XCIII. törvény", "17", "1", "c")),
            (ref(None, "41", None, "2"), ref("2000. évi C. törvény")),
            (ref(None, "41", None, "2", "a"), ref("2000. évi C. törvény", "79", "4")),
            (ref(None, "41", None, "2", "b"), ref("2000. évi C. törvény", "103", "2", "c")),
            (ref(None, "41", None, "3"), ref("2004. évi CXXIII. törvény")),
            (ref(None, "41", None, "3", "a"), ref("2004. évi CXXIII. törvény", ("8/A", "8/B"))),
            (ref(None, "41", None, "3", "b"), ref("2004. évi CXXIII. törvény", ("16/A", "16/B"))),
            (ref(None, "41", None, "3", "c"), ref("2004. évi CXXIII. törvény", "17/A", "1")),
            (ref(None, "41", None, "3", "c"), ref("2004. évi CXXIII. törvény", "17/A", "3")),
            (ref(None, "41", None, "4"), ref("2012. évi CXLVII. törvény")),
            (ref(None, "41", None, "4"), ref("2012. évi CXLVII. törvény", "2", None, "21")),
        ),
        (
            (
                ref(None, "40", "1"),
                BlockAmendmentMetadata(
                    position=ref('2012. évi CXLVII. törvény', '2', None, '19'),
                    expected_type=NumericPoint,
                    expected_id_range=('19', '20'),
                    replaces=(
                        ref('2012. évi CXLVII. törvény', '2', None, ('19', '20')),
                    )
                )
            ),
            (
                ref(None, "41", None, "1"),
                Repeal(position=ref("1990. évi XCIII. törvény", "17", "1", "c"), text="vagy egészségügyi hozzájárulás"),
            ),
            (
                ref(None, "41", None, "2", "a"),
                Repeal(position=ref("2000. évi C. törvény", "79", "4"), text="az egészségügyi hozzájárulás,"),
            ),
            (
                ref(None, "41", None, "2", "b"),
                Repeal(position=ref("2000. évi C. törvény", "103", "2", "c"), text="egészségügyi hozzájárulás,"),
            ),
            (
                ref(None, "41", None, "3", "a"),
                Repeal(position=ref("2004. évi CXXIII. törvény", ("8/A", "8/B")))
            ),
            (
                ref(None, "41", None, "3", "b"),
                Repeal(position=ref("2004. évi CXXIII. törvény", ("16/A", "16/B")))
            ),
            (
                ref(None, "41", None, "3", "c"),
                Repeal(position=ref("2004. évi CXXIII. törvény", "17/A", "1"))
            ),
            (
                ref(None, "41", None, "3", "c"),
                Repeal(position=ref("2004. évi CXXIII. törvény", "17/A", "3"))
            ),
            (
                ref(None, "41", None, "4"),
                Repeal(position=ref("Katv.", "2", None, "21"))
            ),
        ),
    ),
    (
        """
        1. §        A relatív referenciák, mint az a) pont működnek cikkre.

        2. §    (1) A relatív referenciák, mint a (2) bekezdés 1. pontja, vagy simáncsak a) pont is mennek.
                (2) Van második bekezdés, a pontjai
                    1. első pont
                    2. második pont, ami referál a 12/A. § (1)–(5) bekezdéseire.
        """,
        (
            (ref(None, "1"), ref(None, point="a")),
            (ref(None, "2", "1"), ref(None, None, "2", "1")),
            (ref(None, "2", "1"), ref(None, point="a")),
            (ref(None, "2", "2", "2"), ref(None, "12/A", ("1", "5"))),
        ),
        (),
    ),
    (
        """
        1. §      (1)  A devizakölcsönök törlesztési árfolyamának rögzítéséről és a lakóingatlanok kényszerértékesítésének
                       rendjéről szóló 2011. évi LXXV. törvény (a továbbiakban: Tv.) 1. § (1) bekezdés 1. pont c) alpontja
                       helyébe a következő rendelkezés lép: (E törvényben és az e törvény felhatalmazása alapján kiadott
                       jogszabályban: 1. devizakölcsön: a természetes személy mint adós vagy adóstárs és a pénzügyi intézmény
                       között létrejött olyan kölcsönszerződés alapján fennálló tartozás, amelynél)
                       „c) a kölcsön fedezete a Magyar Köztársaság területén lévő lakóingatlanon alapított zálogjog vagy a Magyar
                            Köztársaság 2005. évi költségvetéséről szóló 2004. évi CXXXV. törvény 44. §-a alapján vállalt állami készfizető
                            kezesség;
                       ”
                  (2)  A Tv. 1. § (1) bekezdés 4. pontja helyébe a következő rendelkezés lép: (E törvényben és az e törvény
                       felhatalmazása alapján kiadott jogszabályban:)
                       „4. gyűjtőszámlahitel: nem annyira fontos”
        """,
        (
            (ref(None, "1", "1"), ref("2011. évi LXXV. törvény")),
            (ref(None, "1", "1"), ref("2011. évi LXXV. törvény", "1", "1", "1", "c")),
            (ref(None, "1", "2"), ref("2011. évi LXXV. törvény")),
            (ref(None, "1", "2"), ref("2011. évi LXXV. törvény", "1", "1", "4")),
        ),
        (
            (
                ref(None, "1", "1"),
                BlockAmendmentMetadata(
                    position=ref('2011. évi LXXV. törvény', '1', '1', '1', 'c'),
                    expected_type=AlphabeticSubpoint,
                    expected_id_range=('c', 'c'),
                    replaces=(
                        ref('2011. évi LXXV. törvény', '1', '1', '1', 'c'),
                    )
                )
            ),
            (
                ref(None, "1", "2"),
                BlockAmendmentMetadata(
                    position=ref("2011. évi LXXV. törvény", "1", "1", "4"),
                    expected_type=NumericPoint,
                    expected_id_range=('4', '4'),
                    replaces=(
                        ref("2011. évi LXXV. törvény", "1", "1", "4"),
                    )
                )
            ),
        ),
    ),
    (
        """
            17. § Hatályát veszti a Tesztelésről Szóló 2020. évi I. törvény (a továbbiakban: Teszttv.)
                  a)   1. § (1) és (3) bekezdése,
                  b)   2. §-a, valamint
                  c)   3. § (1) bekezdése.
        """,
        (
            (ref(None, "17"), ref("2020. évi I. törvény")),
            (ref(None, "17", None, "a"), ref("2020. évi I. törvény", "1", "1")),
            (ref(None, "17", None, "a"), ref("2020. évi I. törvény", "1", "3")),
            (ref(None, "17", None, "b"), ref("2020. évi I. törvény", "2")),
            (ref(None, "17", None, "c"), ref("2020. évi I. törvény", "3", "1")),
        ),
        (
            (
                ref(None, "17", None, "a"),
                Repeal(position=ref("2020. évi I. törvény", "1", "1")),
            ),
            (
                ref(None, "17", None, "a"),
                Repeal(position=ref("2020. évi I. törvény", "1", "3")),
            ),
            (
                ref(None, "17", None, "b"),
                Repeal(position=ref("2020. évi I. törvény", "2")),
            ),
            (
                ref(None, "17", None, "c"),
                Repeal(position=ref("2020. évi I. törvény", "3", "1")),
            ),
        ),
    ),
]

CASES_WITH_POSITIONS: List[Tuple[str, Tuple[OutgoingReference, ...]]] = [
    (
        """
            1. §    A tesztelésről szóló 2345. évi I. törvény
                    a) 8. §
                        aa) (5) bekezdése,
                        ab) (6) bekezdés a) pontja,
                    b) 10. §-a, és
                    c) egy totál másik dolog 1. § c) pontja, még utána ezzel szöveggel
                    jól van feldolgozva.
            """,
        (
            OutgoingReference(
                ref(None, "1"),
                21, 41,
                ref("2345. évi I. törvény")
            ),
            OutgoingReference(
                ref(None, "1", None, "a"),
                0, 4,
                ref("2345. évi I. törvény", "8")
            ),
            OutgoingReference(
                ref(None, "1", None, "a", "aa"),
                0, 13,
                ref("2345. évi I. törvény", "8", "5")
            ),
            OutgoingReference(
                ref(None, "1", None, "a", "ab"),
                0, 22,
                ref("2345. évi I. törvény", "8", "6", "a")
            ),
            OutgoingReference(
                ref(None, "1", None, "b"),
                0, 7,
                ref("2345. évi I. törvény", "10")
            ),
            OutgoingReference(
                ref(None, "1", None, "c"),
                22, 36,
                ref(None, "1", None, "c")
            ),
        )
    ),
]


def quick_parse_with_semantics(act_text: str) -> Act:
    act = quick_parse_structure(act_text, parse_block_amendments=True)
    return ActSemanticsParser.parse(act)


@pytest.mark.parametrize("act_text,references,semantic_data", CASES_WITHOUT_POSITIONS)  # type: ignore
def test_outgoing_references_without_position(act_text: str, references: Tuple[Tuple[Reference, Reference], ...], semantic_data: Tuple[Tuple[Reference, SemanticData], ...]) -> None:
    act = quick_parse_with_semantics(act_text)
    assert act.outgoing_references is not None
    outgoing_references = tuple((r.from_reference, r.to_reference) for r in act.outgoing_references)
    assert outgoing_references == references
    assert act.semantic_data == semantic_data


@pytest.mark.parametrize("act_text,outgoing_references", CASES_WITH_POSITIONS)  # type: ignore
def test_outgoing_ref_positions_are_okay(act_text: str, outgoing_references: Tuple[OutgoingReference]) -> None:
    act = quick_parse_with_semantics(act_text)
    assert act.outgoing_references == outgoing_references
