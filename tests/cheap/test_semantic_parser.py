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

from typing import List, Tuple, Union

import pytest
import attr

from hun_law.structure import Act, OutgoingReference, Reference, StructuralReference,\
    SemanticData, BlockAmendment, Repeal, TextAmendment, \
    ActIdAbbreviation, EnforcementDate, DaysAfterPublication, \
    Article, Paragraph, AlphabeticPoint, BlockAmendmentContainer

from hun_law.utils import Date
from hun_law.parsers.semantic_parser import ActSemanticsParser

from .utils import ref, quick_parse_structure


CASES_WITHOUT_POSITIONS: List[Tuple[str, Tuple[Tuple[Reference, Tuple[Union[Reference, SemanticData], ...]], ...]]] = [
    (
        """
            17. §          Hatályát veszti
                           a)   a Polgári Törvénykönyvről szóló 1959. évi IV. törvény 261. § (4) bekezdése,
                           b)   a Polgári Törvénykönyv hatálybalépéséről és végrehajtásáról szóló 1960. évi 11. törvényerejű
                                rendelet 83/A. §-a,
                           c)   az ingatlan-nyilvántartásról szóló 1997. évi CXLI. törvény 16/A. §-a és 91. § (2) bekezdése.
        """,
        (
            (
                ref(None, "17", None, "a"),
                (
                    ref("1959. évi IV. törvény"),
                    ref("1959. évi IV. törvény", "261", "4"),
                    Repeal(position=ref("1959. évi IV. törvény", "261", "4")),
                ),
            ),
            # TODO: Act-like decree ref in b)
            (
                ref(None, "17", None, "b"),
                (
                    ref(None, "83/A"),
                ),
            ),
            (
                ref(None, "17", None, "c"),
                (
                    ref("1997. évi CXLI. törvény"),
                    ref("1997. évi CXLI. törvény", "16/A"),
                    ref("1997. évi CXLI. törvény", "91", "2"),
                    Repeal(position=ref("1997. évi CXLI. törvény", "16/A")),
                    Repeal(position=ref("1997. évi CXLI. törvény", "91", "2")),
                ),
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
            (
                ref(None, "40", "1"),
                (
                    ref("2012. évi CXLVII. törvény"),
                    ref("2012. évi CXLVII. törvény", "2", None, ("19", "20")),
                    BlockAmendment(
                        position=ref('2012. évi CXLVII. törvény', '2', None, ('19', '20')),
                    )
                ),
            ),
            (
                ref(None, "41", None, "1"),
                (
                    ref("1990. évi XCIII. törvény"),
                    ref("1990. évi XCIII. törvény", "17", "1", "c"),
                    Repeal(position=ref("1990. évi XCIII. törvény", "17", "1", "c"), text="vagy egészségügyi hozzájárulás"),
                ),
            ),
            (
                ref(None, "41", None, "2"),
                (
                    ref("2000. évi C. törvény"),
                ),
            ),
            (
                ref(None, "41", None, "2", "a"),
                (
                    ref("2000. évi C. törvény", "79", "4"),
                    Repeal(position=ref("2000. évi C. törvény", "79", "4"), text="az egészségügyi hozzájárulás,"),
                ),
            ),
            (
                ref(None, "41", None, "2", "b"),
                (
                    ref("2000. évi C. törvény", "103", "2", "c"),
                    Repeal(position=ref("2000. évi C. törvény", "103", "2", "c"), text="egészségügyi hozzájárulás,"),
                ),
            ),
            (
                ref(None, "41", None, "3"),
                (
                    ref("2004. évi CXXIII. törvény"),
                ),
            ),
            (
                ref(None, "41", None, "3", "a"),
                (
                    ref("2004. évi CXXIII. törvény", ("8/A", "8/B")),
                    Repeal(position=ref("2004. évi CXXIII. törvény", ("8/A", "8/B"))),
                ),
            ),
            (
                ref(None, "41", None, "3", "b"),
                (
                    ref("2004. évi CXXIII. törvény", ("16/A", "16/B")),
                    Repeal(position=ref("2004. évi CXXIII. törvény", ("16/A", "16/B"))),
                ),
            ),
            (
                ref(None, "41", None, "3", "c"),
                (
                    ref("2004. évi CXXIII. törvény", "17/A", "1"),
                    ref("2004. évi CXXIII. törvény", "17/A", "3"),
                    Repeal(position=ref("2004. évi CXXIII. törvény", "17/A", "1")),
                    Repeal(position=ref("2004. évi CXXIII. törvény", "17/A", "3")),
                ),
            ),
            (
                ref(None, "41", None, "4"),
                (
                    ref("2012. évi CXLVII. törvény"),
                    ref("2012. évi CXLVII. törvény", "2", None, "21"),
                    Repeal(position=ref("2012. évi CXLVII. törvény", "2", None, "21")),
                ),
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
            (
                ref(None, "1"),
                (
                    ref(None, point="a"),
                ),
            ),
            (
                ref(None, "2", "1"),
                (
                    ref(None, None, "2", "1"),
                    ref(None, point="a"),
                ),
            ),
            (
                ref(None, "2", "2", "2"),
                (
                    ref(None, "12/A", ("1", "5")),
                ),
            ),
        ),
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
            (
                ref(None, "1", "1"),
                (
                    ref("2011. évi LXXV. törvény"),
                    ref("2011. évi LXXV. törvény", "1", "1", "1", "c"),
                    BlockAmendment(
                        position=ref('2011. évi LXXV. törvény', '1', '1', '1', 'c'),
                    ),
                ),
            ),
            (
                ref(None, "1", "2"),
                (
                    ref("2011. évi LXXV. törvény"),
                    ref("2011. évi LXXV. törvény", "1", "1", "4"),
                    BlockAmendment(
                        position=ref("2011. évi LXXV. törvény", "1", "1", "4"),
                    ),
                ),
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
            (
                ref(None, "17"),
                (
                    ref("2020. évi I. törvény"),
                ),
            ),
            (
                ref(None, "17", None, "a"), (
                    ref("2020. évi I. törvény", "1", "1"),
                    ref("2020. évi I. törvény", "1", "3"),
                    Repeal(position=ref("2020. évi I. törvény", "1", "1")),
                    Repeal(position=ref("2020. évi I. törvény", "1", "3")),
                ),
            ),
            (
                ref(None, "17", None, "b"),
                (
                    ref("2020. évi I. törvény", "2"),
                    Repeal(position=ref("2020. évi I. törvény", "2")),
                ),
            ),
            (
                ref(None, "17", None, "c"),
                (
                    ref("2020. évi I. törvény", "3", "1"),
                    Repeal(position=ref("2020. évi I. törvény", "3", "1")),
                ),
            ),
        ),
    ),
    (
        """
            16. § Létezik a Rövidítésekről szóló 2020. évi III. törvény (a továbbiakban: Rvtv.).
            17. § Hatályát veszti az Rvtv. 1. § (1)–(5) bekezdése.
            18. § Az Rvtv. 12. § (7) bekezdésében a „fontatlan” szövegrész helyébe a „nem fontos” szöveg lép.
            19. § Az Rvtv. 12. § (8) bekezdése helyébe a következő rendelkezés lép:
                   „(8) Rövidíteni tudni kell.”
        """,
        (
            (
                ref(None, "16"),
                (
                    ref("2020. évi III. törvény"),
                ),
            ),
            (
                ref(None, "17"),
                (
                    ref("2020. évi III. törvény"),
                    ref("2020. évi III. törvény", "1", ("1", "5")),
                    Repeal(position=ref("2020. évi III. törvény", "1", ("1", "5"))),
                ),
            ),
            (
                ref(None, "18"),
                (
                    ref("2020. évi III. törvény"),
                    ref("2020. évi III. törvény", "12", "7"),
                    TextAmendment(
                        position=ref("2020. évi III. törvény", "12", "7"),
                        original_text="fontatlan",
                        replacement_text="nem fontos",
                    ),
                ),
            ),
            (
                ref(None, "19"),
                (
                    ref("2020. évi III. törvény"),
                    ref("2020. évi III. törvény", "12", "8"),
                    BlockAmendment(
                        position=ref("2020. évi III. törvény", "12", "8"),
                    )
                ),
            ),
        ),
    ),
    (
        """
            17. § A Ptk. Harmadik Könyv VIII. Címének helyébe a következő cím lép:
                 „VIII. CÍM
                 NEM

                     1. § Pls no.
                 ”
        """,
        (
            (
                ref(None, "17"), (
                    BlockAmendment(
                        position=StructuralReference(act='Ptk.', book='3', part=None, title='VIII', chapter=None, subtitle=None)
                    ),
                ),
            ),
        ),
    ),
]

CASES_WITH_POSITIONS: List[Tuple[str, Tuple[Tuple[Reference, OutgoingReference], ...]]] = [
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
            (
                ref(None, "1"),
                OutgoingReference(
                    21, 41,
                    ref("2345. évi I. törvény")
                ),
            ),
            (
                ref(None, "1", None, "a"),
                OutgoingReference(

                    0, 4,
                    ref("2345. évi I. törvény", "8")
                ),
            ),
            (
                ref(None, "1", None, "a", "aa"),
                OutgoingReference(

                    0, 13,
                    ref("2345. évi I. törvény", "8", "5")
                ),
            ),
            (
                ref(None, "1", None, "a", "ab"),
                OutgoingReference(
                    0, 22,
                    ref("2345. évi I. törvény", "8", "6", "a")
                ),
            ),
            (
                ref(None, "1", None, "b"),
                OutgoingReference(
                    0, 7,
                    ref("2345. évi I. törvény", "10")
                ),
            ),
            (
                ref(None, "1", None, "c"),
                OutgoingReference(
                    22, 36,
                    ref(None, "1", None, "c")
                ),
            ),
        )
    ),
]


def quick_parse_with_semantics(act_text: str) -> Act:
    act = quick_parse_structure(act_text, parse_block_amendments=True)
    return ActSemanticsParser.add_semantics_to_act(act)


@pytest.mark.parametrize("act_text,act_data", CASES_WITHOUT_POSITIONS)  # type: ignore
def test_outgoing_references_without_position(act_text: str, act_data: Tuple[Tuple[Reference, Tuple[Union[Reference, SemanticData], ...]], ...]) -> None:
    act = quick_parse_with_semantics(act_text)
    assert act.is_semantic_parsed
    for reference, data in act_data:
        expected_outgoing_references = tuple(d for d in data if isinstance(d, Reference))
        expected_semantic_data = tuple(d for d in data if isinstance(d, SemanticData))
        element = act.at_reference(reference)
        assert element.outgoing_references is not None
        outgoing_references = tuple(r.reference for r in element.outgoing_references)
        assert outgoing_references == expected_outgoing_references
        assert element.semantic_data == expected_semantic_data


@pytest.mark.parametrize("act_text,act_data", CASES_WITH_POSITIONS)  # type: ignore
def test_outgoing_ref_positions_are_okay(act_text: str, act_data: Tuple[Tuple[Reference, OutgoingReference], ...]) -> None:
    act = quick_parse_with_semantics(act_text)
    assert act.is_semantic_parsed
    for reference, outgoing_reference in act_data:
        element = act.at_reference(reference)
        assert element.outgoing_references == (outgoing_reference,)


def test_semantic_reparse_simple() -> None:
    TEST_ACT = Act(
        identifier="2050. évi XD. törvény",
        publication_date=Date(2050, 3, 4),
        subject="A nyelvtani tesztelésről",
        preamble='',
        children=(
            Article(
                identifier="1",
                children=(
                    Paragraph(
                        text="Fontos lesz később a tesztelés X tulajdonságiról szóló 2040. évi DX. törvény (a továbbiakban Xtv.) rövidítésének feloldása.",
                    ),
                )
            ),
            Article(
                identifier="2",
                children=(
                    Paragraph(
                        identifier="1",
                        text="Bekeverünk a tesztelés Y tulajdonságiról szóló 2041. évi X. törvény dolgaival.",
                    ),
                    Paragraph(
                        identifier="2",
                        text="Itt megemlítendő a 1. § és a tesztelés Z tulajdonságiról szóló 2041. évi XXX. törvény (a továbbiakban Ztv.)  1. §-a közötti különbség",
                    ),
                    Paragraph(
                        identifier="3",
                        intro="Az Xtv.",
                        wrap_up="szöveg lép.",
                        children=(
                            AlphabeticPoint(
                                identifier="a",
                                text="12. § (7) bekezdésében a „fontatlan” szövegrész helyébe a „nem fontos”,",
                            ),
                            AlphabeticPoint(
                                identifier="b",
                                text="11. §-ben a „nemigazán” szövegrész helyébe a „nem”",
                            ),
                        ),
                    ),
                ),
            ),
            Article(
                identifier="3",
                children=(
                    Paragraph(
                        text="Ez a törvény a kihirdetését követő napon lép hatályba."
                    ),
                )
            ),
            Article(
                identifier="4",
                children=(
                    Paragraph(
                        intro="A Ztv. 12. § (8) bekezdése helyébe a következő rendelkezés lép:",
                        children=(
                            BlockAmendmentContainer(
                                children=(
                                    Paragraph(
                                        identifier='8',
                                        text="Beillesztett referencia: 11. §, vajon lesz baj?"
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )

    with_semantics_1 = ActSemanticsParser.add_semantics_to_act(TEST_ACT)
    assert with_semantics_1.is_semantic_parsed

    assert with_semantics_1.article('1').paragraph().act_id_abbreviations == (
        ActIdAbbreviation('Xtv.', '2040. évi DX. törvény'),
    )
    assert with_semantics_1.article('2').paragraph('2').act_id_abbreviations == (
        ActIdAbbreviation('Ztv.', '2041. évi XXX. törvény'),
    )
    assert with_semantics_1.article('1').paragraph().outgoing_references == (
        OutgoingReference(start_pos=55, end_pos=76, reference=Reference(act='2040. évi DX. törvény')),
    )
    assert with_semantics_1.article('2').paragraph('1').outgoing_references == (
        OutgoingReference(start_pos=47, end_pos=67, reference=Reference(act='2041. évi X. törvény')),
    )
    assert with_semantics_1.article('2').paragraph('3').point('a').semantic_data == (
        TextAmendment(
            position=Reference(act='2040. évi DX. törvény', article='12', paragraph='7'),
            original_text='fontatlan',
            replacement_text='nem fontos'
        ),
    )
    assert with_semantics_1.article('3').paragraph().semantic_data == (
        EnforcementDate(position=None, date=DaysAfterPublication(days=1)),
    )
    assert with_semantics_1.article('4').paragraph().semantic_data == (
        BlockAmendment(
            position=Reference(act='2041. évi XXX. törvény', article='12', paragraph='8'),
        ),
    )

    a4_children = with_semantics_1.article('4').paragraph().children
    assert a4_children is not None
    the_block_amendment = a4_children[0]
    assert isinstance(the_block_amendment, BlockAmendmentContainer)

    assert the_block_amendment.semantic_data is None
    assert the_block_amendment.outgoing_references is None
    assert the_block_amendment.act_id_abbreviations is None

    with_semantics_2 = ActSemanticsParser.add_semantics_to_act(with_semantics_1)

    assert with_semantics_2 is with_semantics_1

    modified_paragraph = attr.evolve(
        with_semantics_1.article("2").paragraph("1"),
        text="Az 1. § és 3. § egészen fontos.",
        semantic_data=None,
        outgoing_references=None,
        act_id_abbreviations=None,
    )
    modified_article = attr.evolve(
        with_semantics_1.article("2"),
        children=(modified_paragraph,) + with_semantics_1.article("2").children[1:],
    )
    modified_act = attr.evolve(
        with_semantics_1,
        children=(with_semantics_1.children[0], modified_article, with_semantics_1.children[2], with_semantics_1.children[3]),
    )

    assert modified_act.article('1').is_semantic_parsed
    assert not modified_act.article('2').is_semantic_parsed
    assert modified_act.article('3').is_semantic_parsed
    assert modified_act.article('4').is_semantic_parsed
    assert not modified_act.is_semantic_parsed

    modified_with_semantics = ActSemanticsParser.add_semantics_to_act(modified_act)
    assert modified_with_semantics.is_semantic_parsed
    assert modified_with_semantics.article('2').paragraph('1').outgoing_references == (
        OutgoingReference(start_pos=3, end_pos=7, reference=Reference(act=None, article='1')),
        OutgoingReference(start_pos=11, end_pos=15, reference=Reference(act=None, article='3')),
    )

    # Check if nothing else was touched but the modified part.
    assert with_semantics_1.article('1') is modified_with_semantics.article('1')
    assert with_semantics_1.article('2').paragraph('2') is modified_with_semantics.article('2').paragraph('2')
    assert with_semantics_1.article('2').paragraph('3') is modified_with_semantics.article('2').paragraph('3')
    assert with_semantics_1.article('3') is modified_with_semantics.article('3')
    assert with_semantics_1.article('4') is modified_with_semantics.article('4')


def test_semantic_reparse_abbrevs() -> None:
    TEST_ACT = Act(
        identifier="2050. évi XD. törvény",
        publication_date=Date(2050, 3, 4),
        subject="A nyelvtani tesztelésről",
        preamble='',
        children=(
            Article(
                identifier="1",
                children=(
                    Paragraph(
                        text="Fontos lesz később a tesztelés X tulajdonságiról szóló 2040. évi DX. törvény (a továbbiakban Xtv.) rövidítésének feloldása.",
                    ),
                )
            ),
            Article(
                identifier="2",
                children=(
                    Paragraph(
                        identifier="1",
                        text="Bekeverünk a tesztelés Y tulajdonságiról szóló 2041. évi X. törvény (a továbbiakban Ytv.) dolgaival",
                    ),
                    Paragraph(
                        identifier="2",
                        text="Itt megemlítendő az Ytv. 10. §-a és a tesztelés Z tulajdonságiról szóló 2041. évi XXX. törvény (a továbbiakban Ztv.) 1. §-a közötti különbség",
                    ),
                    Paragraph(
                        identifier="3",
                        intro="Mert később használatban van",
                        children=(
                            AlphabeticPoint(
                                identifier="a",
                                text="az Xtv. 1. § c) pontja, és"
                            ),
                            AlphabeticPoint(
                                identifier="b",
                                text="az Ytv. 2. §-a."
                            ),
                        ),
                    ),
                ),
            ),
            Article(
                identifier="3",
                children=(
                    Paragraph(
                        text="Mégegyszer megemlítendő, hogy fontos az Xtv. 1. §-a, Ytv. 1. §-a, és Ztv. 1337. §-a.",
                    ),
                )
            ),
            Article(
                identifier="4",
                children=(
                    Paragraph(
                        intro="Az Ytv. 12. § (8) bekezdése helyébe a következő rendelkezés lép:",
                        children=(
                            BlockAmendmentContainer(
                                children=(
                                    Paragraph(
                                        identifier='8',
                                        text="Beillesztett referencia: 12. §, vajon lesz baj?"
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )

    with_semantics_1 = ActSemanticsParser.add_semantics_to_act(TEST_ACT)
    assert with_semantics_1.is_semantic_parsed

    assert with_semantics_1.article('1').paragraph().act_id_abbreviations == (
        ActIdAbbreviation('Xtv.', '2040. évi DX. törvény'),
    )
    assert with_semantics_1.article('2').paragraph('1').act_id_abbreviations == (
        ActIdAbbreviation('Ytv.', '2041. évi X. törvény'),
    )
    assert with_semantics_1.article('2').paragraph('2').act_id_abbreviations == (
        ActIdAbbreviation('Ztv.', '2041. évi XXX. törvény'),
    )
    assert with_semantics_1.article('3').paragraph().outgoing_references == (
        OutgoingReference(start_pos=40, end_pos=44, reference=Reference(act='2040. évi DX. törvény')),
        OutgoingReference(start_pos=45, end_pos=51, reference=Reference(act='2040. évi DX. törvény', article='1')),
        OutgoingReference(start_pos=53, end_pos=57, reference=Reference(act='2041. évi X. törvény')),
        OutgoingReference(start_pos=58, end_pos=64, reference=Reference(act='2041. évi X. törvény', article='1')),
        OutgoingReference(start_pos=69, end_pos=73, reference=Reference(act='2041. évi XXX. törvény')),
        OutgoingReference(start_pos=74, end_pos=83, reference=Reference(act='2041. évi XXX. törvény', article='1337')),
    )

    with_semantics_2 = ActSemanticsParser.add_semantics_to_act(with_semantics_1)
    # TODO: with_semantics_2 is with_semantics_1
    assert with_semantics_2 == with_semantics_1

    modified_paragraph = attr.evolve(
        with_semantics_1.article("2").paragraph("1"),
        text="Bekeverünk a tesztelés Y új tulajdonságiról szóló 2057. évi X. törvény (a továbbiakban Ytv.) dolgaival",
        semantic_data=None,
        outgoing_references=None,
        act_id_abbreviations=None,
    )
    modified_article = attr.evolve(
        with_semantics_1.article("2"),
        children=(modified_paragraph,) + with_semantics_1.article("2").children[1:],
    )
    modified_act = attr.evolve(
        with_semantics_1,
        children=(with_semantics_1.children[0], modified_article, with_semantics_1.children[2], with_semantics_1.children[3]),
    )

    assert not modified_act.is_semantic_parsed

    modified_with_semantics = ActSemanticsParser.add_semantics_to_act(modified_act)
    assert modified_with_semantics.article('2').paragraph('1').act_id_abbreviations == (
        ActIdAbbreviation('Ytv.', '2057. évi X. törvény'),
    )
    assert modified_with_semantics.article('3').paragraph().outgoing_references == (
        OutgoingReference(start_pos=40, end_pos=44, reference=Reference(act='2040. évi DX. törvény')),
        OutgoingReference(start_pos=45, end_pos=51, reference=Reference(act='2040. évi DX. törvény', article='1')),
        OutgoingReference(start_pos=53, end_pos=57, reference=Reference(act='2057. évi X. törvény')),
        OutgoingReference(start_pos=58, end_pos=64, reference=Reference(act='2057. évi X. törvény', article='1')),
        OutgoingReference(start_pos=69, end_pos=73, reference=Reference(act='2041. évi XXX. törvény')),
        OutgoingReference(start_pos=74, end_pos=83, reference=Reference(act='2041. évi XXX. törvény', article='1337')),
    )
    assert modified_with_semantics.article('4').paragraph().semantic_data == (
        BlockAmendment(
            position=Reference(act='2057. évi X. törvény', article='12', paragraph='8'),
        ),
    )

    assert with_semantics_1.article('1') is modified_with_semantics.article('1')
    # Note that because of the abbreviation change, everything else may be reparsed,
    # so no asserts for e.g. article('3')

    # No need to reparse BlockAmendments though
    a4_children = with_semantics_1.article('4').paragraph().children
    modified_a4_children = modified_with_semantics.article('4').paragraph().children
    assert a4_children is not None
    assert modified_a4_children is not None
    assert a4_children[0] is modified_a4_children[0]
