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
from typing import Type, List
import pytest
import attr

from hun_law.structure import \
    Act, Book, \
    Article, Paragraph, AlphabeticPoint, NumericPoint, NumericSubpoint, AlphabeticSubpoint, SubArticleElement,\
    Reference

from hun_law.utils import Date

TEST_STRUCTURE = Act(
    identifier="2345. évi XD. törvény",
    publication_date=Date(2345, 6, 7),
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


@pytest.mark.parametrize("numeric_cls", (Paragraph, NumericPoint, NumericSubpoint))
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

    assert numeric_cls.is_next_identifier("2", "2/a")
    assert numeric_cls.is_next_identifier("2/b", "2/c")
    assert numeric_cls.is_next_identifier("2/b", "3")

    assert not numeric_cls.is_next_identifier("2/c", "2/c")
    assert not numeric_cls.is_next_identifier("2/c", "2/b")
    assert not numeric_cls.is_next_identifier("2/b", "2")
    assert not numeric_cls.is_next_identifier("2/b", "1")
    assert not numeric_cls.is_next_identifier("2/b", "2/d")
    assert not numeric_cls.is_next_identifier("3", "2/a")


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


def test_reference_parent() -> None:
    r = Reference("2345. évi XD. törvény", "1:2", "2", "b", "bb")
    r = r.parent()
    assert r == Reference("2345. évi XD. törvény", "1:2", "2", "b")
    r = r.parent()
    assert r == Reference("2345. évi XD. törvény", "1:2", "2")
    r = r.parent()
    assert r == Reference("2345. évi XD. törvény", "1:2")
    r = r.parent()
    assert r == Reference("2345. évi XD. törvény")
    r = r.parent()
    assert r == Reference()


def test_reference_is_parent_of() -> None:
    r = Reference("2345. évi XD. törvény", "1:2", "2", "b", "bb")
    references: List[Reference] = []
    while r != Reference():
        references.insert(0, r)
        r = r.parent()

    for ref1_index, ref1 in enumerate(references):
        for ref2_index, ref2 in enumerate(references):
            assert ref1.is_parent_of(ref2) == (ref1_index < ref2_index)


def test_reference_is_parent_of_different_subtree() -> None:
    assert not Reference("2345. évi XD. törvény", "1:2", "2", "b", "ba").is_parent_of(Reference("2345. évi XD. törvény", "1:2", "2", "b", "bb"))
    assert not Reference("2345. évi XD. törvény", "1:2", "2", "a",).is_parent_of(Reference("2345. évi XD. törvény", "1:2", "2", "b", "bb"))
    assert not Reference("2345. évi XD. törvény", "1:2", "3",).is_parent_of(Reference("2345. évi XD. törvény", "1:2", "2", "b", "bb"))
    assert not Reference("2345. évi XD. törvény", "1:1").is_parent_of(Reference("2345. évi XD. törvény", "1:2", "2", "b", "bb"))
    assert not Reference("2346. évi XD. törvény").is_parent_of(Reference("2345. évi XD. törvény", "1:2", "2", "b", "bb"))

    assert not Reference(None, "1:2", "2", "b", "ba").is_parent_of(Reference(None, "1:2", "2", "b", "bb"))
    assert not Reference(None, "1:2", "2", "a",).is_parent_of(Reference(None, "1:2", "2", "b", "bb"))
    assert not Reference(None, "1:2", "3",).is_parent_of(Reference(None, "1:2", "2", "b", "bb"))
    assert not Reference(None, "1:1").is_parent_of(Reference(None, "1:2", "2", "b", "bb"))


REFERENCE_ORDERING_CASES = (
    (
        (Reference(None, '1'), '=', Reference(None, '1')),
        (Reference(None, '1', None, 'a', '2'), '=', Reference(None, '1', None, 'a', '2')),
        (Reference(None, '1', '1', 'a', '2'), '=', Reference(None, '1', '1', 'a', '2')),

        (Reference(None, '1'), '<', Reference(None, '2')),
        (Reference(None, '1/A'), '<', Reference(None, '2')),
        (Reference(None, '1/A'), '<', Reference(None, '1/B')),
        (Reference(None, '1'), '<', Reference(None, '1/A')),

        (Reference(None, '1'), '<', Reference(None, '1', '1')),
        (Reference(None, '1'), '<', Reference(None, '1', None, 'a')),
        (Reference(None, '1', None, 'a'), '<', Reference(None, '1', None, 'b')),

        (Reference(None, '1', '1', 'c'), '<', Reference(None, '1', '2', 'a')),

        # TODO: Roman number parsing in 'lt'
        (Reference('2345. évi XD. törvény', '1'), '=', Reference('2345. évi XD. törvény', '1')),
        (Reference('2345. évi XD. törvény', '1'), '<', Reference('2345. évi XD. törvény', '2')),
        (Reference('2345. évi XD. törvény', '2'), '<', Reference('2346. évi XD. törvény', '1')),
    )
)


@pytest.mark.parametrize("ref1, operator, ref2", REFERENCE_ORDERING_CASES)
def test_reference_ordering(ref1: Reference, ref2: Reference, operator: str) -> None:
    assert (ref1 == ref2) == (operator == '=')
    assert (ref1 < ref2) == (operator == '<')
    assert (ref1 > ref2) == (operator == '>')
    assert (ref1 <= ref2) == (operator in ('<', '='))
    assert (ref1 >= ref2) == (operator in ('>', '='))

    assert (ref2 > ref1) == (operator == '<')
    assert (ref2 < ref1) == (operator == '>')
    assert (ref2 >= ref1) == (operator in ('<', '='))
    assert (ref2 <= ref1) == (operator in ('>', '='))


def test_reference_contains() -> None:
    assert Reference(None, ('1', '2')).contains(Reference(None, '1'))
    assert Reference(None, ('1', '2')).contains(Reference(None, '2'))
    assert Reference(None, ('1', '2')).contains(Reference(None, '1/A'))
    assert not Reference(None, ('1', '2')).contains(Reference(None, '3'))
    assert not Reference(None, ('1', '2')).contains(Reference(None, '2/A'))
    assert not Reference(None, ('2', '10')).contains(Reference(None, '1'))

    assert Reference(None, "2", "2", ('3', '4')).contains(Reference(None, '2', '2', '3'))
    assert Reference(None, "2", "2", ('3', '4')).contains(Reference(None, '2', '2', '4'))
    assert not Reference(None, "2", "2", ('3', '4')).contains(Reference(None, '2', '2', '1'))
    assert not Reference(None, "2", "2", ('3', '4')).contains(Reference(None, '2', '2', '5'))
    assert not Reference(None, "2", "2", ('3', '4')).contains(Reference(None, '2'))
    assert not Reference(None, "2", "2", ('3', '4')).contains(Reference(None, '2', '2'))
    assert not Reference(None, "2", "2", ('3', '4')).contains(Reference(None, '2', '3', '3'))
    assert not Reference(None, "2", "2", ('3', '4')).contains(Reference(None, '2', None, '3'))

    assert Reference(None, "2", "2", "2", ('3', '4')).contains(Reference(None, '2', '2', '2', '3'))
    assert Reference(None, "2", "2", "2", ('3', '4')).contains(Reference(None, '2', '2', '2', '4'))
    assert not Reference(None, "2", "2", "2", ('3', '4')).contains(Reference(None, '2', '2', '2', '2'))
    assert not Reference(None, "2", "2", "2", ('3', '4')).contains(Reference(None, '2', '2', '2', '5'))

    assert not Reference(None, ('3', '8')).contains(Reference(None, '30'))

    assert Reference(None, '3').contains(Reference(None, '3'))
    assert Reference(None, '3').contains(Reference(None, '3', '2'))

    assert not Reference(None, '3', '8').contains(Reference(None, '3'))
    assert not Reference(None, '3', '8').contains(Reference(None, '3', '9'))

    assert Reference(None, '3').contains(Reference(None, '3'))
    assert Reference(None, '3').contains(Reference(None, '3', None, '2'))
    assert not Reference(None, '3', None, '8').contains(Reference(None, '3'))
    assert not Reference(None, '3', None, '8').contains(Reference(None, '3', None, '9'))

    assert Reference(None, '3', None, 'a').contains(Reference(None, '3', None, 'a'))
    assert Reference(None, '3', None, 'a').contains(Reference(None, '3', None, 'a', 'ab'))
    assert not Reference(None, '3', None, 'a', 'ab').contains(Reference(None, '3', None, 'a'))
    assert not Reference(None, '3', None, 'a', 'ab').contains(Reference(None, '3', None, 'a', 'ac'))

    # TODO: Hard to implement invalid cases
    # assert not Reference(None, '3', None, '8').contains(Reference(None, '3', '1', '8'))
    # assert not Reference(None, '3', None, ('8', '9')).contains(Reference(None, '3', '1', '8'))

    assert Reference(None, ('3', '4')).contains(Reference(None, '3', '11'))
    assert Reference(None, '3', '8').contains(Reference(None, '3', '8', ('9', '10')))
    assert not Reference(None, '3', '8').contains(Reference(None, '3', ('8', '9')))

    assert Reference(None, ('1', '2')).contains(Reference(None, ('1', '2')))
    assert Reference(None, ('1', '3')).contains(Reference(None, ('1', '2')))
    assert Reference(None, ('1', '3')).contains(Reference(None, ('2', '3')))
    assert Reference(None, ('1', '5')).contains(Reference(None, ('2', '3')))

    assert Reference(None, ('1', '2')).contains(Reference(None, '1', ('5', '6')))
    assert Reference(None, ('1', '2')).contains(Reference(None, '2', ('5', '6')))
    assert not Reference(None, ('1', '2')).contains(Reference(None, '3', ('5', '6')))

    assert not Reference(None, ('1', '3')).contains(Reference(None, ('2', '4')))


def test_at_reference() -> None:
    assert TEST_STRUCTURE.at_reference(Reference(
        article="1:1"
    )) == (TEST_STRUCTURE.article("1:1"),)

    assert TEST_STRUCTURE.article("1:1").at_reference(Reference()) == \
        (TEST_STRUCTURE.article("1:1").paragraph(),)

    assert TEST_STRUCTURE.at_reference(Reference(
        article="1:2",
        paragraph="1"
    )) == (TEST_STRUCTURE.article("1:2").paragraph("1"),)

    assert TEST_STRUCTURE.at_reference(Reference(
        article="1:2",
        paragraph="2",
    )) == (TEST_STRUCTURE.article("1:2").paragraph("2"),)

    assert TEST_STRUCTURE.at_reference(Reference(
        article="1:2",
        paragraph="2",
        point="a",
    )) == (TEST_STRUCTURE.article("1:2").paragraph("2").point("a"),)

    assert TEST_STRUCTURE.at_reference(Reference(
        article="1:2",
        paragraph="2",
        point="b",
        subpoint="bb",
    )) == (TEST_STRUCTURE.article("1:2").paragraph("2").point("b").subpoint("bb"),)

    assert TEST_STRUCTURE.at_reference(Reference(
        article="2:2",
        paragraph="1",
        point="1a",
    )) == (TEST_STRUCTURE.article("2:2").paragraph("1").point("1a"),)


def test_at_reference_range() -> None:
    assert TEST_STRUCTURE.at_reference(Reference(
        article=("1:1", "2:1")
    )) == (
        TEST_STRUCTURE.article("1:1"),
        TEST_STRUCTURE.article("1:2"),
        TEST_STRUCTURE.article("2:1"),
    )

    assert TEST_STRUCTURE.at_reference(Reference(
        article=("1:1/A", "2:1/B")
    )) == (
        TEST_STRUCTURE.article("1:2"),
        TEST_STRUCTURE.article("2:1"),
        TEST_STRUCTURE.article("2:1/A"),
    )

    assert TEST_STRUCTURE.at_reference(Reference(
        article="1:2",
        paragraph=("1", "2")
    )) == (
        TEST_STRUCTURE.article("1:2").paragraph("1"),
        TEST_STRUCTURE.article("1:2").paragraph("2"),
    )

    assert TEST_STRUCTURE.at_reference(Reference(
        article="1:2",
        paragraph=("1/A", "3")
    )) == (
        TEST_STRUCTURE.article("1:2").paragraph("2"),
    )

    assert TEST_STRUCTURE.at_reference(Reference(
        article="2:2",
        paragraph="1",
        point=("1a", "2")
    )) == (
        TEST_STRUCTURE.article("2:2").paragraph("1").point("1a"),
        TEST_STRUCTURE.article("2:2").paragraph("1").point("2"),
    )


def test_at_reference_invalid() -> None:
    with pytest.raises(KeyError):
        TEST_STRUCTURE.at_reference(Reference(None, "5"))
    with pytest.raises(KeyError):
        TEST_STRUCTURE.at_reference(Reference(None, "."))
    with pytest.raises(KeyError):
        TEST_STRUCTURE.at_reference(Reference(None, "1:1", "2"))
    with pytest.raises(KeyError):
        TEST_STRUCTURE.at_reference(Reference(None, "1:1", None, ("2", "3")))
    with pytest.raises(KeyError):
        TEST_STRUCTURE.at_reference(Reference(None, "2:2", "1", "2", "a"))
    with pytest.raises(KeyError):
        TEST_STRUCTURE.at_reference(Reference(None, "2:2", "1", "2", ("a", "f")))


def test_map_articles() -> None:
    times_called = 0

    def article_modifier(r: Reference, a: Article) -> Article:
        assert r.article == a.identifier
        if a.identifier != '2:1/A':
            return a
        nonlocal times_called
        times_called = times_called + 1
        return attr.evolve(a, title="Modified")

    modified_act = TEST_STRUCTURE.map_articles(article_modifier)
    assert times_called == 1
    assert modified_act.article("2:1") is TEST_STRUCTURE.article("2:1")
    assert modified_act.article("2:2") is TEST_STRUCTURE.article("2:2")
    assert modified_act.article("2:1/A").title == "Modified"


def test_map_articles_with_filter() -> None:
    times_called = 0

    def article_modifier(_r: Reference, a: Article) -> Article:
        nonlocal times_called
        times_called = times_called + 1
        return attr.evolve(a, title="Modified")

    modified_act = TEST_STRUCTURE.map_articles(article_modifier, Reference('2345. évi XD. törvény', ('2:1', '2:1/A')))
    assert times_called == 2
    assert modified_act.article("2:2") is TEST_STRUCTURE.article("2:2")
    assert modified_act.article("2:1").title == "Modified"
    assert modified_act.article("2:1/A").title == "Modified"


def test_map_saes() -> None:
    times_called = 0
    times_matched = 0

    def text_modifier(r: Reference, sae: SubArticleElement) -> SubArticleElement:
        print(r, sae.identifier, sae.__class__.__name__)
        nonlocal times_matched, times_called
        times_called = times_called + 1
        if r != Reference('2345. évi XD. törvény', '1:2', '2', 'b', 'ba'):
            return sae
        times_matched = times_matched + 1
        return attr.evolve(sae, text="Modified")

    modified_act = TEST_STRUCTURE.map_saes(text_modifier)
    assert times_matched == 1
    assert times_called == 13
    assert modified_act.article("2:1") is TEST_STRUCTURE.article("2:1")
    assert modified_act.article("2:2") is TEST_STRUCTURE.article("2:2")
    assert modified_act.article("1:2").paragraph("2").point("b").subpoint("bb") is \
        TEST_STRUCTURE.article("1:2").paragraph("2").point("b").subpoint("bb")
    assert modified_act.article("1:2").paragraph("2").point("b").subpoint("ba").text == "Modified"


def test_map_saes_with_filter() -> None:
    times_called = 0
    times_matched = 0

    def text_modifier(r: Reference, sae: SubArticleElement) -> SubArticleElement:
        print(r, sae.identifier, sae.__class__.__name__)
        nonlocal times_matched, times_called
        times_called = times_called + 1
        if r != Reference('2345. évi XD. törvény', '1:2', '2', 'b', 'ba'):
            return sae
        times_matched = times_matched + 1
        return attr.evolve(sae, text="Modified")

    modified_act = TEST_STRUCTURE.map_saes(text_modifier, Reference('2345. évi XD. törvény', '1:2', '2', 'b'))
    assert times_called == 3
    assert times_matched == 1
    assert modified_act.article("2:1") is TEST_STRUCTURE.article("2:1")
    assert modified_act.article("2:2") is TEST_STRUCTURE.article("2:2")
    assert modified_act.article("1:2").paragraph("2").point("b").subpoint("bb") is \
        TEST_STRUCTURE.article("1:2").paragraph("2").point("b").subpoint("bb")
    assert modified_act.article("1:2").paragraph("2").point("b").subpoint("ba").text == "Modified"


def test_map_saes_children_first() -> None:
    def text_modifier(r: Reference, sae: SubArticleElement) -> SubArticleElement:
        print(r, sae.identifier, sae.__class__.__name__)
        if r == Reference('2345. évi XD. törvény', '1:2', '2', 'b', 'ba'):
            return attr.evolve(sae, text="Modified")
        if r == Reference('2345. évi XD. törvény', '1:2', '2', 'b'):
            assert isinstance(sae, AlphabeticPoint)
            assert sae.subpoint('ba').text == "Modified"
        return sae

    modified_act = TEST_STRUCTURE.map_saes(text_modifier, children_first=True)
    assert modified_act.article("1:2").paragraph("2").point("b").subpoint("ba").text == "Modified"


RELATIVE_ID_CASES = (
    Reference(None, "1:2", "2/b", "b", "bb"),
    Reference(None, "1:2", "2", "b"),
    Reference(None, "1:2", "2"),
    Reference(None, "1:2", None, "b", "bb"),
    Reference(None, "1:2", None, "b"),
    Reference(None, "1:2/A"),
    Reference(None, "1:2", "2/b", "b", ("bb", "bc")),
    Reference(None, "1:2", "2", ("b", "d")),
    Reference(None, "1:2", ("2", "2/B")),
    Reference(None, "1:2", None, "b", ("bb", "bd")),
    Reference(None, "1:2", None, ("b", "d")),
    Reference(None, "1:2/A"),
    Reference(None),
)


@pytest.mark.parametrize("ref", RELATIVE_ID_CASES)
def test_relative_id_string(ref: Reference) -> None:
    relative_str = ref.relative_id_string
    assert Reference.from_relative_id_string(relative_str) == ref
