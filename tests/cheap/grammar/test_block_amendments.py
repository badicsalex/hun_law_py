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
from hun_law.structure import \
    BlockAmendmentMetadata, \
    Article, Paragraph, NumericPoint, AlphabeticPoint, AlphabeticSubpoint, \
    StructuralReference, SubtitleReferenceArticleRelative, RelativePosition, \
    Subtitle

from tests.cheap.utils import ref


BLOCK_AMENDMENT_CASES: Tuple[Tuple[str, BlockAmendmentMetadata], ...] = (
    (
        "A hegyközségekről szóló 2012. évi CCXIX. törvény (a továbbiakban: Hktv.) 28. §-a helyébe a következő rendelkezés lép:",
        BlockAmendmentMetadata(
            expected_type=Article,
            expected_id_range=("28", "28"),
            position=ref("2012. évi CCXIX. törvény", '28'),
            replaces=(ref("2012. évi CCXIX. törvény", '28'),),
        )
    ),
    (
        "A szabálysértésekről és egyebekről szóló 2012. évi I. törvény (a továbbiakban: Szabs. tv.) 29. § (2) bekezdés e) pontja helyébe a következő rendelkezés lép:",
        BlockAmendmentMetadata(
            expected_type=AlphabeticPoint,
            expected_id_range=("e", "e"),
            position=ref("2012. évi I. törvény", "29", "2", "e"),
            replaces=(ref("2012. évi I. törvény", "29", "2", "e"),)
        )
    ),
    (
        "A Tv. 1. § 3. pontja helyébe a következő rendelkezés lép:",
        BlockAmendmentMetadata(
            expected_type=NumericPoint,
            expected_id_range=("3", "3"),
            position=ref('Tv.', "1", None, "3"),
            replaces=(ref('Tv.', "1", None, "3"),)
        )
    ),
    (
        "Az alpontok rendjéről szóló 2111. évi LXXV. törvény (a továbbiakban: Tv.) 1. § (1) bekezdés 1. pont c) alpontja helyébe a következő rendelkezés lép:",
        BlockAmendmentMetadata(
            expected_type=AlphabeticSubpoint,
            expected_id_range=("c", "c"),
            position=ref("2111. évi LXXV. törvény", "1", "1", "1", "c"),
            replaces=(ref("2111. évi LXXV. törvény", "1", "1", "1", "c"),),
        )
    ),
    (
        "A Batv. 1. § (2) bekezdés b)–f) pontja helyébe a következő rendelkezés lép:",
        BlockAmendmentMetadata(
            expected_type=AlphabeticPoint,
            expected_id_range=("b", "f"),
            position=ref("Batv.", "1", "2", "b"),
            replaces=(ref("Batv.", "1", "2", ("b", "f")),),

        )
    ),
    (
        "Az Eht. 188. §-a a következő 31/a. ponttal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=NumericPoint,
            expected_id_range=("31/a", "31/a"),
            position=ref("Eht.", "188", None, "31/a"),
        )
    ),
    (
        "A légiközlekedésről szóló 1995. évi XCVII. törvény 71. §-a a következő 3a. ponttal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=NumericPoint,
            expected_id_range=("3a", "3a"),
            position=ref("1995. évi XCVII. törvény", "71", None, "3a"),
        )
    ),
    (
        "A Víziközmű tv. 63. §-a a következő (5)–(7) bekezdéssel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("5", "7"),
            position=ref("Víziközmű tv.", "63", "5"),
        )
    ),
    (
        "A Ptk. 6:417. § (4) bekezdése a következő szöveggel lép hatályba:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("4", "4"),
            position=ref("Ptk.", "6:417", "4"),
            replaces=(ref("Ptk.", "6:417", "4"),),
        )
    ),
    (
        "A Ptk. 6:130. §-a a következő szöveggel lép hatályba:",
        BlockAmendmentMetadata(
            expected_type=Article,
            expected_id_range=("6:130", "6:130"),
            position=ref("Ptk.", "6:130"),
            replaces=(ref("Ptk.", "6:130"),),
        )
    ),
    (
        "A Ptk. 3:391. §-a a következő (3) bekezdéssel kiegészülve lép hatályba:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("3", "3"),
            position=ref("Ptk.", "3:391", "3"),
        )
    ),
    (
        "A Ptk. 3:278. § (1) bekezdés e) pontja a következő szöveggel lép hatályba:",
        BlockAmendmentMetadata(
            expected_type=AlphabeticPoint,
            expected_id_range=("e", "e"),
            position=ref("Ptk.", "3:278", "1", "e"),
            replaces=(ref("Ptk.", "3:278", "1", "e"),),
        )
    ),
    (
        "A polgári törvénykönyvről szóló 2013. évi V. tv. 3:319. § (5) bekezdése a következő szöveggel lép hatályba:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("5", "5"),
            position=ref("2013. évi V. törvény", "3:319", "5"),
            replaces=(ref("2013. évi V. törvény", "3:319", "5"),),
        )
    ),
    (
        "A Gyvt. 69/D. §-a a következő (1a) és (1b) bekezdéssel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("1a", "1b"),
            position=ref("Gyvt.", "69/D", "1a"),
        )
    ),
    (
        "A Ptk. 3:261. § (4) és (5) bekezdése a következő szöveggel lép hatályba:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("4", "5"),
            position=ref("Ptk.", "3:261", "4"),
            replaces=(ref("Ptk.", "3:261", ("4", "5")),),
        )
    ),
    (
        "A Kkt. 49. § (2) bekezdés i) pontja helyébe a következő rendelkezés lép, és a bekezdés a következő j) ponttal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=AlphabeticPoint,
            expected_id_range=("i", "j"),
            position=ref("Kkt.", "49", "2", "i"),
            replaces=(ref("Kkt.", "49", "2", "i"),)
        )
    ),
    (
        "Az Elszámolási tv. 35. § (4) bekezdése helyébe a következő rendelkezés lép, és a § a következő (5) bekezdéssel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("4", "5"),
            position=ref("Elszámolási tv.", "35", "4"),
            replaces=(ref("Elszámolási tv.", "35", "4"),),
        )
    ),
    (
        "A Ptk. 3:268. § (2) és (3) bekezdése helyébe a következő rendelkezések lépnek, és a § a következő (4) bekezdéssel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("2", "4"),
            position=ref("Ptk.", "3:268", "2"),
            replaces=(ref("Ptk.", "3:268", ("2", "3")),)
        )
    ),
    (
        "A Ptk. 8:6. § r) pontja helyébe a következő rendelkezés lép, és a § a következő s) ponttal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=AlphabeticPoint,
            expected_id_range=("r", "s"),
            position=ref("Ptk.", "8:6", None, "r"),
            replaces=(ref("Ptk.", "8:6", None, "r"),),
        )
    ),
    (
        "A Tv. 16. § (1) bekezdés f) pontja helyébe a következő rendelkezés lép, és a § a következő g) és h) pontokkal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=AlphabeticPoint,
            expected_id_range=("f", "h"),
            position=ref("Tv.", "16", "1", "f"),
            replaces=(ref("Tv.", "16", "1", "f"),),
        )
    ),
    (
        "Az Tv. 5/A. § (2a) bekezdése helyébe a következő rendelkezés lép, és a § a következő (2b)–(2f) bekezdéssel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("2a", "2f"),
            position=ref("Tv.", "5/A", "2a"),
            replaces=(ref("Tv.", "5/A", "2a"),),
        )
    ),
    (
        "Az Evt. 108. § (4) bekezdése helyébe a következő rendelkezés lép, valamint a következő (5)–(10) bekezdéssel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("4", "10"),
            position=ref("Evt.", "108", "4"),
            replaces=(ref("Evt.", "108", "4"),),
        )
    ),
    (
        "A Btk. 459. § (1) bekezdés 24. pontja helyébe a következő rendelkezés lép, valamint a 459. § (1) bekezdése a következő 24a. ponttal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=NumericPoint,
            expected_id_range=("24", "24a"),
            position=ref("Btk.", "459", "1", "24"),
            replaces=(ref("Btk.", "459", "1", "24"),),
        )
    ),
    (
        "Az egyszerűsített foglalkoztatásról szóló 2010. évi LXXV. törvény (a továbbiakban: Efotv.) a következő 1. § (1a) bekezdéssel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("1a", "1a"),
            position=ref("2010. évi LXXV. törvény", "1", "1a"),
        )
    ),
    (
        "A társadalombiztosítási nyugellátásról szóló 1997. évi LXXXI. törvény 96. § (2) bekezdés h) pontja helyébe a következő rendelkezés lép, egyidejűleg a bekezdés a következő i) ponttal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=AlphabeticPoint,
            expected_id_range=("h", "i"),
            position=ref("1997. évi LXXXI. törvény", "96", "2", "h"),
            replaces=(ref("1997. évi LXXXI. törvény", "96", "2", "h"),),
        )
    ),
    (
        "A Btk. 279. § (1) és (2) bekezdése helyébe a következő rendelkezések lépnek:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("1", "2"),
            position=ref("Btk.", "279", "1"),
            replaces=(ref("Btk.", "279", ("1", "2")),),
        )
    ),
    (
        "A Btk. 283. § (2) és (2a) bekezdése helyébe a következő rendelkezések lépnek:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("2", "2a"),
            position=ref("Btk.", "283", "2"),
            replaces=(ref("Btk.", "283", ("2", "2a")),),
        )
    ),
    (
        "A Btk. XX. Fejezete a következő alcímmel és 212/A. §-sal kiegészülve lép hatályba:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("212/A", "212/A"),
            position=StructuralReference("Btk."),
        )
    ),
    (
        "A Btk. 349. §-a és a megelőző alcím helyébe a következő rendelkezés és alcím lép:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("349", "349"),
            position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "349")),
            replaces=(
                StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "349")),
                ref("Btk.", "349"),
            )
        )
    ),
    (
        "A Btk. a 300. §-t megelőzően a következő alcímmel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "300")),
        )
    ),
    (
        "A Btk. XXVII. Fejezete a következő alcímmel és 300/A. §-sal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("300/A", "300/A"),
            position=StructuralReference("Btk."),
        )
    ),
    (
        "A Btk. Terrorcselekmény alcíme a következő 316/A. §-sal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Article,
            expected_id_range=("316/A", "316/A"),
            position=ref("Btk.", "316/A"),
        ),
    ),
    (
        "A Btk. Terrorizmus finanszírozása alcíme a következő 318/A. és 318/B. §-sal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Article,
            expected_id_range=("318/A", "318/B"),
            position=ref("Btk.", "318/A"),
        ),
    ),
    (
        "A Btk. a 404. §-t követően a következő alcímmel és 404/A. §-sal kiegészülve lép hatályba:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("404/A", "404/A"),
            position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.AFTER, "404")),
        ),
    ),
    (
        "A Btk. a következő 226/A. §-sal és az azt megelőző alcímmel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("226/A", "226/A"),
            position=StructuralReference("Btk."),
        ),
    ),
    (
        "A Btk. „Új pszichoaktív anyaggal visszaélés” alcíme a következő 184/A–184/D. §-sal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Article,
            expected_id_range=("184/A", "184/D"),
            position=ref("Btk.", "184/A"),
        ),
    ),
    (
        "A Btk. XXIV. Fejezete a következő alcímmel és 261/A. §-sal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("261/A", "261/A"),
            position=StructuralReference("Btk."),
        ),
    ),
    (
        "A Btk. 388/A. §-a és az azt megelőző alcím helyébe a következő alcím és rendelkezés lép:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("388/A", "388/A"),
            position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "388/A")),
            replaces=(
                StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "388/A")),
                ref("Btk.", "388/A"),
            ),
        ),
    ),
    (
        "A Btk. a következő 352/A–352/C. §-sal és az azokat megelőző alcímekkel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("352/A", "352/C"),
            position=StructuralReference("Btk."),
        ),
    ),
    (
        "A Btk. a következő alcímmel és 410/A. §-sal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("410/A", "410/A"),
            position=StructuralReference("Btk."),
        ),
    ),
    (
        "A Btk. 411. §-át megelőző alcím címe és 411. §-a helyébe a következő rendelkezés lép:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("411", "411"),
            position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "411")),
            replaces=(
                StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "411")),
                ref("Btk.", "411"),
            ),
        ),
    ),
    (
        "A Btk. IX. Fejezete a 92/A. §-t követően a következő alcímmel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.AFTER, "92/A")),
        ),
    ),
    (
        "A Btk. 83. §-t megelőző alcím helyébe a következő alcím lép:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "83")),
            replaces=(
                StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "83")),
            ),
        ),
    ),
    (
        "A Btk. a 124. §-t követően a következő alcímmel és 124/A. §-sal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("124/A", "124/A"),
            position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.AFTER, "124")),
        ),
    ),
    (
        "Az elektronikus információszabadságról szóló 2005. évi XC. törvény (a továbbiakban: Einfotv.) 12. §-át megelőző alcíme helyébe a következő alcím lép:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            position=StructuralReference("2005. évi XC. törvény", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "12")),
            replaces=(
                StructuralReference("2005. évi XC. törvény", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "12")),
            ),
        )
    ),
    (
        "A Büntető Törvénykönyvről szóló 2012. évi C. törvény 350. §-a és az azt megelőző alcím-megjelölése helyébe a következő rendelkezés lép:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("350", "350"),
            position=StructuralReference("2012. évi C. törvény", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "350")),
            replaces=(
                StructuralReference("2012. évi C. törvény", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "350")),
                ref("2012. évi C. törvény", "350"),
            ),
        )
    ),


    # TODO:
    # (
    #     "A Ptk. Hatodik Könyv Ötödik Része helyébe a következő rész lép:",
    #     BlockAmendmentMetadata(
    #         expected_type=Part,
    #         position=StructuralReference("Ptk."),
    #         replaces=(StructuralReference("Ptk.", book="6", part="5"),),
    #     ),
    # ),
    # (
    #     "A Ptk. Harmadik Könyv VIII. Címének helyébe a következő cím lép:",
    #     BlockAmendmentMetadata(
    #         expected_type=Title,
    #         position=StructuralReference("Ptk."),
    #         replaces=(StructuralReference("Ptk.", book="3", title="8"),),
    #     ),
    # ),
)

# TODO:
# Other simultaneous amendment + insertion cases:
# Full articles: "Az R2. 7. §-a helyébe a következő rendelkezés lép, és az R2. a következő 7/A. §-sal egészül ki"
# "követően" constructs:
#   "A Tfvt. a 17/A. §-t követően a következő 17/B. és 17/C. §-sal egészül ki"
#   "Az Ngt. a 6/C. §-át követően a következő alcímmel és 6/D−K. §-sal egészül ki:"
#   "A helyi adókról szóló 1990. évi C. törvény (a továbbiakban: Htv.) a 11. §-t követően a következő 11/A. §-sal egészül ki"


@pytest.mark.parametrize("s,correct_metadata", BLOCK_AMENDMENT_CASES)  # type: ignore
def test_block_amendment_parsing(s: str, correct_metadata: BlockAmendmentMetadata) -> None:
    parsed = GrammaticalAnalyzer().analyze(s, print_result=True)
    parsed_metadata = parsed.semantic_data
    assert (correct_metadata, ) == parsed_metadata
