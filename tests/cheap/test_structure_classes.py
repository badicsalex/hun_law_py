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
from typing import Type
import pytest

from hun_law.structure import \
    Act, Book, \
    Article, Paragraph, AlphabeticPoint, NumericPoint, NumericSubpoint, AlphabeticSubpoint, \
    Reference

TEST_STRUCTURE = Act(
    identifier="2345. évi XD. törvény",
    subject="A tesztelésről",
    preamble="A tesztelés nagyon fontos, és egyben kötelező",
    children=(
        Book(identifier="1", title="Egyszerű dolgok"),
        Article(
            identifier="1:1",
            title="Az egyetlen cikk, aminek cime van.",
            children=(
                Paragraph(
                    text="Meg szövege",
                ),
            )
        ),
        Article(
            identifier="1:2",
            children=(
                Paragraph(
                    identifier="1",
                    text="Valami valami"
                ),
                Paragraph(
                    identifier="2",
                    intro="Egy felsorolás legyen",
                    wrap_up="minden esetben.",
                    children=(
                        AlphabeticPoint(
                            identifier="a",
                            text="többelemű"
                        ),
                        AlphabeticPoint(
                            identifier="b",
                            intro="kellően",
                            children=(
                                AlphabeticSubpoint(
                                    identifier="ba",
                                    text="átláthatatlan"
                                ),
                                AlphabeticSubpoint(
                                    identifier="bb",
                                    text="komplex"
                                ),
                            )
                        )
                    )
                ),
            )
        ),
        Book(identifier="2", title="Amended stuff in english"),
        Article(
            identifier="2:1",
            children=(
                Paragraph(
                    text="Nothing fancy yet"
                ),
            )
        ),
        Article(
            identifier="2:1/A",
            children=(
                Paragraph(
                    text="Added after the fact"
                ),
            )
        ),
        Article(
            identifier="2:2",
            children=(
                Paragraph(
                    identifier="1",
                    intro="This can legally be after 2:1/A. Also, ",
                    wrap_up="Can also be amended",
                    children=(
                        NumericPoint(
                            identifier="1",
                            text="Paragraphs",
                        ),
                        NumericPoint(
                            identifier="1a",
                            text="Numeric points",
                        ),
                        NumericPoint(
                            identifier="2",
                            text="Alphabetic points",
                        ),
                    )
                ),
            )
        ),
    )
)


def test_reference_equality() -> None:
    assert Reference() == Reference()
    assert Reference(article="1") != Reference(article="2")
    assert Reference("2345. évi XD. törvény", "1", "2", "a", "ab") == Reference("2345. évi XD. törvény", "1", "2", "a", "ab")


def test_relative_references() -> None:
    act_ref = Reference(TEST_STRUCTURE.identifier)

    article_ref = TEST_STRUCTURE.article("1:2").relative_reference.relative_to(act_ref)
    assert article_ref == Reference("2345. évi XD. törvény", "1:2")

    paragraph_ref = TEST_STRUCTURE.article("1:2").paragraph("2") \
        .relative_reference.relative_to(article_ref)
    assert paragraph_ref == Reference("2345. évi XD. törvény", "1:2", "2")

    point_ref = TEST_STRUCTURE.article("1:2").paragraph("2").point("b") \
        .relative_reference.relative_to(paragraph_ref)
    assert point_ref == Reference("2345. évi XD. törvény", "1:2", "2", "b")

    subpoint_ref = TEST_STRUCTURE.article("1:2").paragraph("2").point("b").subpoint("bb") \
        .relative_reference.relative_to(point_ref)
    assert subpoint_ref == Reference("2345. évi XD. törvény", "1:2", "2", "b", "bb")

    ref_1 = Reference(article="1", point="1")
    ref_2 = Reference(point="2", subpoint="a")
    ref_expected = Reference(article="1", point="2", subpoint="a")
    assert ref_2.relative_to(ref_1) == ref_expected, "Reference relative_to overrides too exact original ref"

    ref_1 = Reference(article="1", point="1", subpoint='a')
    ref_2 = Reference(point="2")
    ref_expected = Reference(article="1", point="2")
    assert ref_2.relative_to(ref_1) == ref_expected, "Reference relative_to overrides too exact original ref"


def test_reference_ranges() -> None:
    not_range = Reference("2345. évi XD. törvény", "1:2", "2")
    range1 = Reference("2345. évi XD. törvény", "1:2", ("2", "3"))
    range2 = Reference(None, None, "2", ("a", "b"))

    assert not not_range.is_range()
    assert range1.is_range()
    assert range2.is_range()

    assert not_range.first_in_range() == not_range
    assert range1.first_in_range() == Reference("2345. évi XD. törvény", "1:2", "2")
    assert range2.first_in_range() == Reference(None, None, "2", "a")


def test_next_identifiers_article_happy() -> None:
    assert Article.is_next_identifier("2", "3")
    assert Article.is_next_identifier("2", "2/A")
    assert Article.is_next_identifier("2/C", "3")
    assert Article.is_next_identifier("2/C", "2/D")
    assert Article.is_next_identifier("2/S", "2/T")
    assert Article.is_next_identifier("2/S", "2/SZ")
    assert Article.is_next_identifier("2/SZ", "2/T")

    assert Article.is_next_identifier("1:2", "1:3")
    assert Article.is_next_identifier("1:2", "1:2/A")
    assert Article.is_next_identifier("1:2/C", "1:3")
    assert Article.is_next_identifier("1:2/C", "1:2/D")
    assert Article.is_next_identifier("1:1", "2:1")
    assert Article.is_next_identifier("1:3", "2:1")
    assert Article.is_next_identifier("1:2/C", "2:1")


def test_next_identifiers_article_unhappy() -> None:
    assert not Article.is_next_identifier("1:2", "3")
    assert not Article.is_next_identifier("1:2", "2/A")
    assert not Article.is_next_identifier("1:2/C", "3")
    assert not Article.is_next_identifier("1:2/C", "2/D")
    assert not Article.is_next_identifier("1:1", "1")
    assert not Article.is_next_identifier("1:3", "1")
    assert not Article.is_next_identifier("1:2/C", "1")

    assert not Article.is_next_identifier("2", "1:3")
    assert not Article.is_next_identifier("2", "1:2/A")
    assert not Article.is_next_identifier("2/C", "1:3")
    assert not Article.is_next_identifier("2/C", "1:2/D")
    assert not Article.is_next_identifier("1", "2:1")
    assert not Article.is_next_identifier("3", "2:1")
    assert not Article.is_next_identifier("2/C", "2:1")

    assert not Article.is_next_identifier("3", "2")
    assert not Article.is_next_identifier("3", "5")

    assert not Article.is_next_identifier("2", "3/A")
    assert not Article.is_next_identifier("2", "2/B")
    assert not Article.is_next_identifier("2/A", "2")
    assert not Article.is_next_identifier("2/A", "1")

    assert not Article.is_next_identifier("1:3", "1:2")
    assert not Article.is_next_identifier("1:3", "1:5")

    assert not Article.is_next_identifier("1:2", "1:3/A")
    assert not Article.is_next_identifier("1:2", "1:2/B")
    assert not Article.is_next_identifier("1:2/A", "1:2")
    assert not Article.is_next_identifier("1:2/A", "1:1")

    assert not Article.is_next_identifier("2:2", "1:3")
    assert not Article.is_next_identifier("3:2", "2:2/A")
    assert not Article.is_next_identifier("3:2/C", "2:3")
    assert not Article.is_next_identifier("3:2/C", "2:2/D")
    assert not Article.is_next_identifier("3:1", "2:1")
    assert not Article.is_next_identifier("3:3", "2:1")
    assert not Article.is_next_identifier("3:2/C", "2:1")


@pytest.mark.parametrize("numeric_cls", (Paragraph, NumericPoint, NumericSubpoint))  # type: ignore
def test_next_identifiers_simple_numeric(numeric_cls: Type) -> None:
    assert numeric_cls.is_next_identifier("2", "3")
    assert numeric_cls.is_next_identifier("2", "2a")
    assert numeric_cls.is_next_identifier("2b", "2c")
    assert numeric_cls.is_next_identifier("2b", "3")

    assert not numeric_cls.is_next_identifier("2", "4")
    assert not numeric_cls.is_next_identifier("2", "2")
    assert not numeric_cls.is_next_identifier("3", "2")
    assert not numeric_cls.is_next_identifier("2c", "2c")
    assert not numeric_cls.is_next_identifier("2c", "2b")
    assert not numeric_cls.is_next_identifier("2b", "2")
    assert not numeric_cls.is_next_identifier("2b", "1")
    assert not numeric_cls.is_next_identifier("2b", "2d")
    assert not numeric_cls.is_next_identifier("3", "2a")


def test_next_identifiers_alphabetic() -> None:
    assert AlphabeticPoint.is_next_identifier("c", "d")
    assert AlphabeticPoint.is_next_identifier("n", "ny")
    assert AlphabeticPoint.is_next_identifier("ny", "o")
    assert not AlphabeticPoint.is_next_identifier("c", "f")
    assert not AlphabeticPoint.is_next_identifier("c", "c")
    assert not AlphabeticPoint.is_next_identifier("c", "a")

    assert AlphabeticSubpoint.is_next_identifier("c", "d")
    assert not AlphabeticSubpoint.is_next_identifier("c", "f")
    assert not AlphabeticSubpoint.is_next_identifier("c", "c")
    assert not AlphabeticSubpoint.is_next_identifier("c", "a")

    assert AlphabeticSubpoint.is_next_identifier("ac", "ad")
    assert not AlphabeticSubpoint.is_next_identifier("ac", "af")
    assert not AlphabeticSubpoint.is_next_identifier("ac", "ac")
    assert not AlphabeticSubpoint.is_next_identifier("ac", "aa")

    assert not AlphabeticSubpoint.is_next_identifier("ac", "bd")
