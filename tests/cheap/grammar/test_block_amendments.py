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
    BlockAmendment, \
    StructuralReference, SubtitleArticleCombo, SubtitleArticleComboType \

from tests.cheap.utils import ref


BLOCK_AMENDMENT_CASES: Tuple[Tuple[str, BlockAmendment], ...] = (
    (
        "A hegyközségekről szóló 2012. évi CCXIX. törvény (a továbbiakban: Hktv.) 28. §-a helyébe a következő rendelkezés lép:",
        BlockAmendment(
            position=ref("2012. évi CCXIX. törvény", '28'),
        )
    ),
    (
        "A szabálysértésekről és egyebekről szóló 2012. évi I. törvény (a továbbiakban: Szabs. tv.) 29. § (2) bekezdés e) pontja helyébe a következő rendelkezés lép:",
        BlockAmendment(
            position=ref("2012. évi I. törvény", "29", "2", "e"),
        )
    ),
    (
        "A Tv. 1. § 3. pontja helyébe a következő rendelkezés lép:",
        BlockAmendment(
            position=ref('Tv.', "1", None, "3"),
        )
    ),
    (
        "Az alpontok rendjéről szóló 2111. évi LXXV. törvény (a továbbiakban: Tv.) 1. § (1) bekezdés 1. pont c) alpontja helyébe a következő rendelkezés lép:",
        BlockAmendment(
            position=ref("2111. évi LXXV. törvény", "1", "1", "1", "c"),
        )
    ),
    (
        "A Batv. 1. § (2) bekezdés b)–f) pontja helyébe a következő rendelkezés lép:",
        BlockAmendment(
            position=ref("Batv.", "1", "2", ("b", "f")),

        )
    ),
    (
        "Az Eht. 188. §-a a következő 31/a. ponttal egészül ki:",
        BlockAmendment(
            position=ref("Eht.", "188", None, "31/a"),
        )
    ),
    (
        "A légiközlekedésről szóló 1995. évi XCVII. törvény 71. §-a a következő 3a. ponttal egészül ki:",
        BlockAmendment(
            position=ref("1995. évi XCVII. törvény", "71", None, "3a"),
        )
    ),
    (
        "A Víziközmű tv. 63. §-a a következő (5)–(7) bekezdéssel egészül ki:",
        BlockAmendment(
            position=ref("Víziközmű tv.", "63", ("5", "7")),
        )
    ),
    (
        "A Ptk. 6:417. § (4) bekezdése a következő szöveggel lép hatályba:",
        BlockAmendment(
            position=ref("Ptk.", "6:417", "4"),
        )
    ),
    (
        "A Ptk. 6:130. §-a a következő szöveggel lép hatályba:",
        BlockAmendment(
            position=ref("Ptk.", "6:130"),
        )
    ),
    (
        "A Ptk. 3:391. §-a a következő (3) bekezdéssel kiegészülve lép hatályba:",
        BlockAmendment(
            position=ref("Ptk.", "3:391", "3"),
        )
    ),
    (
        "A Ptk. 3:278. § (1) bekezdés e) pontja a következő szöveggel lép hatályba:",
        BlockAmendment(
            position=ref("Ptk.", "3:278", "1", "e"),
        )
    ),
    (
        "A polgári törvénykönyvről szóló 2013. évi V. tv. 3:319. § (5) bekezdése a következő szöveggel lép hatályba:",
        BlockAmendment(
            position=ref("2013. évi V. törvény", "3:319", "5"),
        )
    ),
    (
        "A Gyvt. 69/D. §-a a következő (1a) és (1b) bekezdéssel egészül ki:",
        BlockAmendment(
            position=ref("Gyvt.", "69/D", ("1a", "1b")),
        )
    ),
    (
        "A Ptk. 3:261. § (4) és (5) bekezdése a következő szöveggel lép hatályba:",
        BlockAmendment(
            position=ref("Ptk.", "3:261", ("4", "5")),
        )
    ),
    (
        "A Kkt. 49. § (2) bekezdés i) pontja helyébe a következő rendelkezés lép, és a bekezdés a következő j) ponttal egészül ki:",
        BlockAmendment(
            position=ref("Kkt.", "49", "2", ("i", "j")),
        )
    ),
    (
        "Az Elszámolási tv. 35. § (4) bekezdése helyébe a következő rendelkezés lép, és a § a következő (5) bekezdéssel egészül ki:",
        BlockAmendment(
            position=ref("Elszámolási tv.", "35", ("4", "5")),
        )
    ),
    (
        "A Ptk. 3:268. § (2) és (3) bekezdése helyébe a következő rendelkezések lépnek, és a § a következő (4) bekezdéssel egészül ki:",
        BlockAmendment(
            position=ref("Ptk.", "3:268", ("2", "4")),
        )
    ),
    (
        "A Ptk. 8:6. § r) pontja helyébe a következő rendelkezés lép, és a § a következő s) ponttal egészül ki:",
        BlockAmendment(
            position=ref("Ptk.", "8:6", None, ("r", "s")),
        )
    ),
    (
        "A Tv. 16. § (1) bekezdés f) pontja helyébe a következő rendelkezés lép, és a § a következő g) és h) pontokkal egészül ki:",
        BlockAmendment(
            position=ref("Tv.", "16", "1", ("f", "h")),
        )
    ),
    (
        "Az Tv. 5/A. § (2a) bekezdése helyébe a következő rendelkezés lép, és a § a következő (2b)–(2f) bekezdéssel egészül ki:",
        BlockAmendment(
            position=ref("Tv.", "5/A", ("2a", "2f")),
        )
    ),
    (
        "Az Evt. 108. § (4) bekezdése helyébe a következő rendelkezés lép, valamint a következő (5)–(10) bekezdéssel egészül ki:",
        BlockAmendment(
            position=ref("Evt.", "108", ("4", "10")),
        )
    ),
    (
        "A Btk. 459. § (1) bekezdés 24. pontja helyébe a következő rendelkezés lép, valamint a 459. § (1) bekezdése a következő 24a. ponttal egészül ki:",
        BlockAmendment(
            position=ref("Btk.", "459", "1", ("24", "24a")),
        )
    ),
    (
        "Az egyszerűsített foglalkoztatásról szóló 2010. évi LXXV. törvény (a továbbiakban: Efotv.) a következő 1. § (1a) bekezdéssel egészül ki:",
        BlockAmendment(
            position=ref("2010. évi LXXV. törvény", "1", "1a"),
        )
    ),
    (
        "A társadalombiztosítási nyugellátásról szóló 1997. évi LXXXI. törvény 96. § (2) bekezdés h) pontja helyébe a következő rendelkezés lép, egyidejűleg a bekezdés a következő i) ponttal egészül ki:",
        BlockAmendment(
            position=ref("1997. évi LXXXI. törvény", "96", "2", ("h", "i")),
        )
    ),
    (
        "A Btk. 279. § (1) és (2) bekezdése helyébe a következő rendelkezések lépnek:",
        BlockAmendment(
            position=ref("Btk.", "279", ("1", "2")),
        )
    ),
    (
        "A Btk. 283. § (2) és (2a) bekezdése helyébe a következő rendelkezések lépnek:",
        BlockAmendment(
            position=ref("Btk.", "283", ("2", "2a")),
        )
    ),
    (
        "A Btk. XX. Fejezete a következő alcímmel és 212/A. §-sal kiegészülve lép hatályba:",
        BlockAmendment(
            position=StructuralReference("Btk.", special=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITH_ARTICLE, "212/A")),
        )
    ),
    (
        "A Btk. 349. §-a és a megelőző alcím helyébe a következő rendelkezés és alcím lép:",
        BlockAmendment(
            position=StructuralReference("Btk.", special=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITH_ARTICLE, "349")),
        )
    ),
    (
        "A Btk. a 300. §-t megelőzően a következő alcímmel egészül ki:",
        BlockAmendment(
            position=StructuralReference("Btk.", special=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITHOUT_ARTICLE, "300")),
        )
    ),
    (
        "A Btk. XXVII. Fejezete a következő alcímmel és 300/A. §-sal egészül ki:",
        BlockAmendment(
            position=StructuralReference("Btk.", special=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITH_ARTICLE, "300/A")),
        )
    ),
    (
        "A Btk. Terrorcselekmény alcíme a következő 316/A. §-sal egészül ki:",
        BlockAmendment(
            position=ref("Btk.", "316/A"),
        ),
    ),
    (
        "A Btk. Terrorizmus finanszírozása alcíme a következő 318/A. és 318/B. §-sal egészül ki:",
        BlockAmendment(
            position=ref("Btk.", ("318/A", "318/B")),
        ),
    ),
    (
        "A Btk. a 404. §-t követően a következő alcímmel és 404/A. §-sal kiegészülve lép hatályba:",
        BlockAmendment(
            position=StructuralReference("Btk.", special=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITH_ARTICLE, "404/A")),
        ),
    ),
    (
        "A Btk. a következő 226/A. §-sal és az azt megelőző alcímmel egészül ki:",
        BlockAmendment(
            position=StructuralReference("Btk.", special=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITH_ARTICLE, "226/A")),
        ),
    ),
    (
        "A Btk. „Új pszichoaktív anyaggal visszaélés” alcíme a következő 184/A–184/D. §-sal egészül ki:",
        BlockAmendment(
            position=ref("Btk.", ("184/A", "184/D")),
        ),
    ),
    (
        "A Btk. XXIV. Fejezete a következő alcímmel és 261/A. §-sal egészül ki:",
        BlockAmendment(
            position=StructuralReference("Btk.", special=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITH_ARTICLE, "261/A")),
        ),
    ),
    (
        "A Btk. 388/A. §-a és az azt megelőző alcím helyébe a következő alcím és rendelkezés lép:",
        BlockAmendment(
            position=StructuralReference("Btk.", special=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITH_ARTICLE, "388/A")),
        ),
    ),
    (
        "A Btk. a következő 352/A–352/C. §-sal és az azokat megelőző alcímekkel egészül ki:",
        BlockAmendment(
            # Not a range here, because this is more of an insertion point.
            # MAYBE TODO
            position=StructuralReference("Btk.", special=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITH_ARTICLE, "352/A")),
        ),
    ),
    (
        "A Btk. a következő alcímmel és 410/A. §-sal egészül ki:",
        BlockAmendment(
            position=StructuralReference("Btk.", special=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITH_ARTICLE, "410/A")),
        ),
    ),
    (
        "A Btk. 411. §-át megelőző alcím címe és 411. §-a helyébe a következő rendelkezés lép:",
        BlockAmendment(
            position=StructuralReference("Btk.", special=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITH_ARTICLE, "411")),
        ),
    ),
    (
        "A Btk. IX. Fejezete a 92/A. §-t követően a következő alcímmel egészül ki:",
        BlockAmendment(
            position=StructuralReference("Btk.", special=SubtitleArticleCombo(SubtitleArticleComboType.AFTER, "92/A")),
        ),
    ),
    (
        "A Btk. 83. §-t megelőző alcím helyébe a következő alcím lép:",
        BlockAmendment(
            position=StructuralReference("Btk.", special=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITHOUT_ARTICLE, "83")),
        ),
    ),
    (
        "A Btk. a 124. §-t követően a következő alcímmel és 124/A. §-sal egészül ki:",
        BlockAmendment(
            position=StructuralReference("Btk.", special=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITH_ARTICLE, "124/A")),
        ),
    ),
    (
        "Az elektronikus információszabadságról szóló 2005. évi XC. törvény (a továbbiakban: Einfotv.) 12. §-át megelőző alcíme helyébe a következő alcím lép:",
        BlockAmendment(
            position=StructuralReference("2005. évi XC. törvény", special=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITHOUT_ARTICLE, "12")),
        )
    ),
    (
        "A Büntető Törvénykönyvről szóló 2012. évi C. törvény 350. §-a és az azt megelőző alcím-megjelölése helyébe a következő rendelkezés lép:",
        BlockAmendment(
            position=StructuralReference("2012. évi C. törvény", special=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITH_ARTICLE, "350")),
        )
    ),
    (
        "A számvitelről szóló 2000. évi C. törvény (a továbbiakban: Szt.) 3. § (2) bekezdés 4. és 5. pontja helyébe a következő rendelkezések lépnek és a bekezdés a következő 5a. ponttal egészül ki:",
        BlockAmendment(
            position=ref("2000. évi C. törvény", "3", "2", ("4", "5a")),
        )
    ),
    (
        "A Ptk. Hatodik Könyv Ötödik Része helyébe a következő rész lép:",
        BlockAmendment(
            position=StructuralReference("Ptk.", book="6", part="5"),
        ),
    ),
    (
        "A Ptk. Harmadik Könyv VIII. Címének helyébe a következő cím lép:",
        BlockAmendment(
            position=StructuralReference("Ptk.", book="3", title="8"),
        ),
    ),
    (
        "A Ptk. Harmadik Könyve a következő VIII. Címmel egészül ki:",
        BlockAmendment(
            position=StructuralReference("Ptk.", book="3", title="8"),
        ),
    ),
    (
        "Az Szt. a következő VI/A. Fejezettel egészül ki:",
        BlockAmendment(
            position=StructuralReference("Szt.", chapter="6/A"),
        ),
    ),
    (
        "A Btk. XXIV. Fejezete helyébe a következő fejezet lép:",
        BlockAmendment(
            position=StructuralReference("Btk.", chapter="24"),
        ),
    ),
    (
        "Az Nkt. 11/A. alcíme helyébe a következő rendelkezés lép:",
        BlockAmendment(
            position=StructuralReference("Nkt.", subtitle="11/A"),
        ),
    ),
    (
        "A Ht. 42. § (1) és (2) bekezdése helyébe a következő rendelkezések lépnek, és a § a következő (1a) bekezdéssel egészül ki:",
        BlockAmendment(
            position=ref("Ht.", "42", ("1", "2")),
        ),
    ),
    (
        "A Polgári Törvénykönyvről szóló 2013. évi V. törvény hatálybalépésével összefüggő átmeneti és felhatalmazó rendelkezésekről szóló 2013. évi CLXXVII. törvény 5. alcíme a következő 12/A. §-sal egészül ki:",
        BlockAmendment(
            position=ref("2013. évi CLXXVII. törvény", "12/A"),
        ),
    ),
    (
        "A Ket. 172. § p) és q) pontja helyébe a következő rendelkezések lépnek, és a § a következő r)–t) ponttal egészül ki:",
        BlockAmendment(
            position=ref("Ket.", "172", None, ("p", "t")),
        ),
    ),
    (
        "A Büntető Törvénykönyvről szóló 2012. évi C. törvény (a továbbiakban: Btk.) „Emberkereskedelem” című alcíme helyébe a következő rendelkezés lép:",
        BlockAmendment(
            position=StructuralReference("2012. évi C. törvény", subtitle="Emberkereskedelem"),
        ),
    ),
    (
        "A Btk. Terrorizmus finanszírozása alcíme helyébe a következő rendelkezés lép:",
        BlockAmendment(
            position=StructuralReference("Btk.", subtitle="Terrorizmus finanszírozása"),
        ),
    ),
    (
        "A Büntető Törvénykönyvről szóló 2012. évi C. törvény (a továbbiakban: Btk.) 322. §-át követően a következő alcím címmel és 322/A. §-sal egészül ki:",
        BlockAmendment(
            position=StructuralReference("2012. évi C. törvény",  special=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITH_ARTICLE, "322/A")),
        ),
    ),
)

# TODO:
# Other simultaneous amendment + insertion cases:
# Full articles: "Az R2. 7. §-a helyébe a következő rendelkezés lép, és az R2. a következő 7/A. §-sal egészül ki"
# "követően" constructs:
#   "A Tfvt. a 17/A. §-t követően a következő 17/B. és 17/C. §-sal egészül ki"
#   "Az Ngt. a 6/C. §-át követően a következő alcímmel és 6/D−K. §-sal egészül ki:"
#   "A helyi adókról szóló 1990. évi C. törvény (a továbbiakban: Htv.) a 11. §-t követően a következő 11/A. §-sal egészül ki"


@pytest.mark.parametrize("s,correct_metadata", BLOCK_AMENDMENT_CASES)  # type: ignore
def test_block_amendment_parsing(s: str, correct_metadata: BlockAmendment) -> None:
    parsed = GrammaticalAnalyzer().analyze(s, print_result=True)
    parsed_metadata = parsed.semantic_data
    assert (correct_metadata, ) == parsed_metadata
