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
from hun_law.structure import ArticleTitleAmendment

from tests.cheap.utils import ref

CASES: Tuple[Tuple[str, Tuple[ArticleTitleAmendment, ...]], ...] = (
    (
        "A Ptk. 5:99. § címében az „átruházása” szövegrész helyébe az „átruházása és megterhelése” szöveg lép.",
        (
            ArticleTitleAmendment(
                position=ref("Ptk.", "5:99"),
                original_text="átruházása",
                replacement_text="átruházása és megterhelése"
            ),
        )
    ),
    (
        "A Ptk. 6:534. § címe az „életviszonyok” szövegrész helyett az „értékviszonyok” szöveggel lép hatályba.",
        (
            ArticleTitleAmendment(
                position=ref("Ptk.", "6:534"),
                original_text="életviszonyok",
                replacement_text="értékviszonyok",
            ),
        ),
    ),
)


@pytest.mark.parametrize("s,correct_metadata", CASES)
def test_article_title_amendment_parsing(s: str, correct_metadata: Tuple[ArticleTitleAmendment, ...]) -> None:
    parsed = GrammaticalAnalyzer().analyze(s, print_result=True)
    parsed_metadata = parsed.semantic_data
    assert correct_metadata == parsed_metadata
