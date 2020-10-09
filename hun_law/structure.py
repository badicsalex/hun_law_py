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
from abc import ABC, abstractmethod
from enum import Enum
from typing import Type, Tuple, ClassVar, Optional, Mapping, Union, Any, Callable, Dict
import gc
import inspect
import sys

import attr

from hun_law.utils import int_to_text_hun, int_to_text_roman, IndentedLine, is_next_letter_hun, Date, identifier_less

# Main act on which all the code was based:
# 61/2009. (XII. 14.) IRM rendelet a jogszabályszerkesztésről

# Structuring levels (36. § (2)), and their Akoma Ntoso counterpart (at least IMO):
# a) az alpont,                         | subpoint
# b) a pont,                            | point
# c) a bekezdés,                        | paragraph
# d) a szakasz, [a.ka. paragrafus]      | article *
# e) az alcím,                          | subtitle
# f) a fejezet,                         | chapter
# g) a rész és                          | part
# h) a könyv.                           | book
#
# Additional levels for non-conformant laws, such as 2013. V (PTK):
#    cím                                | title
#
# * even though we call this level "sections" in hungarian (was "paragrafus")
# similar levels are called "section" in UK and US, but "Article" in EU Acts.

# Numbering is non-intuitive:
# Book 1
#   Part 1
#     Title 1
#       Article 1
#         Paragraph 1
#         Paragraph 2
#     Title 2
#       Article 2
#         Paragraph 1
#           Point a)
#           Point b)
#       Article 3
#         Point a)
#   Part 2
#     Title 3
#       Article 4
#       Article 5
#     Title 4
#       Article 6
# Book 2
#   Part 1
#     Title 1
#       Article 1
# ....

# Sometimes numbering are different, especially for older Acts.
# Also, sometimes a Part has Articles outside Titles (at the beginning)
# See 2013. V, 3:159. §

# For this reason, (and because they are so useless) we only handle structure levels,
# as mere 'titles', and don't use them in the code as actual structural things.

# All classes are immutable by design


@attr.s(slots=True, frozen=True, auto_attribs=True)
class StructuralElement(ABC):
    identifier: str = attr.ib()
    title: str

    @property
    @abstractmethod
    def formatted_identifier(self) -> str:
        pass


@attr.s(slots=True, frozen=True)
class Book(StructuralElement):
    # 38. §, Könyv
    # Example:
    # NYOLCADIK KÖNYV
    @property
    def formatted_identifier(self) -> str:
        return "{} KÖNYV".format(int_to_text_hun(int(self.identifier)).upper())


@attr.s(slots=True, frozen=True)
class Part(StructuralElement):
    # 39. § Rész
    # Example:
    # MÁSODIK RÉSZ
    # KÜLÖNÖS RÉSZ

    # 39. § (5)
    SPECIAL_PARTS = ('ÁLTALÁNOS RÉSZ', 'KÜLÖNÖS RÉSZ', 'ZÁRÓ RÉSZ', None)

    @property
    def formatted_identifier(self) -> str:
        # TODO: special parts
        return "{} RÉSZ".format(int_to_text_hun(int(self.identifier)).upper())


@attr.s(slots=True, frozen=True)
class Title(StructuralElement):
    # "CÍM"
    # Nonconformant structural type, present only in PTK
    # Example:
    # XXI. CÍM
    @property
    def formatted_identifier(self) -> str:
        # TODO: special parts
        return "{}. CÍM".format(int_to_text_roman(int(self.identifier)).upper())


@attr.s(slots=True, frozen=True)
class Chapter(StructuralElement):
    # 40. §,  fejezet
    # Example:
    # II. FEJEZET
    # IV. Fejezet
    # XXIII. fejezet  <=  not conformant, but present in e.g. PTK
    @property
    def formatted_identifier(self) -> str:
        # TODO: special parts
        return "{}. FEJEZET".format(int_to_text_roman(int(self.identifier)).upper())


@attr.s(slots=True, frozen=True)
class Subtitle(StructuralElement):
    # 41. §, Alcím
    # Guaranteed to be uppercase
    # Example:
    # 17. Az alcím
    #
    # For older acts, there is no number, only a text.

    @property
    def formatted_identifier(self) -> str:
        if not self.identifier:
            return ""
        # TODO: special parts
        return "{}.".format(self.identifier)


STRUCTURE_ELEMENT_TYPES = (
    Book,
    Part,
    Title,
    Chapter,
    Subtitle,
)


@attr.s(slots=True, frozen=True, auto_attribs=True)
class SemanticData:
    def resolve_abbreviations(self, _abbreviations_map: Mapping[str, str]) -> 'SemanticData':
        return self


@attr.s(slots=True, frozen=True, auto_attribs=True)
class OutgoingReference:
    # Start and end pos are python range, i.e. end_pos is after the last character
    start_pos: int
    end_pos: int
    reference: "Reference"


@attr.s(slots=True, frozen=True, auto_attribs=True)
class QuotedBlock:
    lines: Tuple[IndentedLine, ...]
    identifier: ClassVar = None


SubArticleChildType = Union['Article', 'SubArticleElement', 'QuotedBlock', 'StructuralElement']


@attr.s(slots=True, frozen=True, auto_attribs=True)
class SubArticleElement(ABC):
    ALLOWED_CHILDREN_TYPE: ClassVar[Tuple[Type[SubArticleChildType], ...]] = ()
    ALLOW_DIFFERENTLY_TYPED_CHILDREN: ClassVar[bool] = False
    CAN_BE_SEMANTIC_PARSED: ClassVar[bool] = True

    identifier: Optional[str] = None
    text: Optional[str] = attr.ib(default=None)
    intro: Optional[str] = None
    children: Optional[Tuple[SubArticleChildType, ...]] = attr.ib(default=None)
    wrap_up: Optional[str] = None

    act_id_abbreviations: Optional[Tuple['ActIdAbbreviation', ...]] = None
    outgoing_references: Optional[Tuple[OutgoingReference, ...]] = None
    semantic_data: Optional[Tuple[SemanticData, ...]] = None

    children_type: Optional[Type[SubArticleChildType]] = attr.ib(init=False)
    children_map: Optional[Mapping[Optional[str], SubArticleChildType]] = attr.ib(init=False)

    is_semantic_parsed: bool = attr.ib(init=False)

    @children_type.default
    def _children_type_default(self) -> Optional[Type[SubArticleChildType]]:
        if self.children is None:
            return None
        result = type(self.children[0])
        for c in self.children:
            # We really do want type equality here, not "isintance".
            # pylint: disable=unidiomatic-typecheck
            if type(c) != result:
                if self.ALLOW_DIFFERENTLY_TYPED_CHILDREN:
                    return None
                raise TypeError(
                    "All children  has to be of the  same type ({} is not {})"
                    .format(type(c), result)
                )
        return result

    @children_map.default
    def _children_map_default(self) -> Optional[Mapping[Optional[str], SubArticleChildType]]:
        if self.children is None:
            return None
        return {c.identifier: c for c in self.children}

    @is_semantic_parsed.default
    def _is_semantic_parsed_default(self) -> bool:
        if self.semantic_data is None:
            return False
        if self.children is not None:
            for c in self.children:
                if not isinstance(c, SubArticleElement):
                    break
                if c.CAN_BE_SEMANTIC_PARSED and not c.is_semantic_parsed:
                    return False
        return True

    @text.validator
    def _content_validator_if_text(self, _attribute: Any, text: Optional[str]) -> None:
        if text is not None:
            if self.intro is not None or self.wrap_up is not None or self.children is not None:
                raise ValueError("SAE can contain either text or intro/wrap-up/children")

    @children.validator
    def _content_validator_if_children(self, _attribute: Any, children: Optional[Tuple['SubArticleElement', ...]]) -> None:
        if children is None:
            return
        for c in children:
            # We really do want type equality here, not "isintance".
            # pylint: disable=unidiomatic-typecheck
            if type(c) not in self.ALLOWED_CHILDREN_TYPE:
                raise TypeError("Children of {} can only be {} (got {})".format(type(self), self.ALLOWED_CHILDREN_TYPE, self.children_type))

    def child(self, child_id: str) -> SubArticleChildType:
        if self.children_map is None:
            raise KeyError("There are no children of this element")
        return self.children_map[child_id]

    @classmethod
    @abstractmethod
    def header_prefix(cls, identifier: Optional[str]) -> str:
        pass

    @classmethod
    @abstractmethod
    def is_next_identifier(cls, identifier: str, next_identifier: str) -> bool:
        pass

    @property
    @abstractmethod
    def relative_reference(self) -> 'Reference':
        pass

    @abstractmethod
    def at_reference(self, reference: 'Reference') -> 'SubArticleElement':
        pass

    def map_recursive(
        self,
        parent_reference: 'Reference',
        modifier: Callable[['Reference', 'SubArticleElement'], 'SubArticleElement'],
        filter_for_reference: Optional['Reference'] = None
    ) -> 'SubArticleElement':
        try:
            reference = self.relative_reference.relative_to(parent_reference)
        except TypeError:
            # We are in an unreferrable SAE, stop processing
            return self

        if filter_for_reference is not None \
                and not reference.contains(filter_for_reference) \
                and not filter_for_reference.contains(reference):
            # No need to run, no intersection between the filtered reference and any children
            return self

        result = self
        if filter_for_reference is None or filter_for_reference.contains(reference):
            # Only call the callback if we are actually in the filter, and not just
            # here for the children
            result = modifier(reference, self)

        if result.children:
            new_children = []
            children_changed = False
            for child in result.children:
                if isinstance(child, SubArticleElement):
                    new_child = child.map_recursive(reference, modifier, filter_for_reference)
                    if new_child is not child:
                        child = new_child
                        children_changed = True
                new_children.append(child)
            if children_changed:
                result = attr.evolve(result, children=tuple(new_children))
        return result


@attr.s(slots=True, frozen=True)
class AlphabeticSubpoint(SubArticleElement):
    @classmethod
    def header_prefix(cls, identifier: Optional[str]) -> str:
        return "{}) ".format(identifier)

    @classmethod
    def is_next_identifier(cls, identifier: str, next_identifier: str) -> bool:
        if len(identifier) == 1:
            return is_next_letter_hun(identifier, next_identifier)
        if len(identifier) == 2:
            return identifier[0] == next_identifier[0] and is_next_letter_hun(identifier[1], next_identifier[1])
        raise ValueError("Invalid identifier for subpoint '{}'".format(identifier))

    @property
    def relative_reference(self) -> 'Reference':
        return Reference(subpoint=self.identifier)

    def at_reference(self, reference: 'Reference') -> SubArticleElement:
        raise ValueError("Alphabetic subpoints never have children")


@attr.s(slots=True, frozen=True)
class NumericSubpoint(SubArticleElement):
    @classmethod
    def header_prefix(cls, identifier: Optional[str]) -> str:
        return "{}. ".format(identifier)

    @classmethod
    def is_next_identifier(cls, identifier: str, next_identifier: str) -> bool:
        return NumericPoint.is_next_identifier(identifier, next_identifier)

    @property
    def relative_reference(self) -> 'Reference':
        return Reference(subpoint=self.identifier)

    def at_reference(self, reference: 'Reference') -> SubArticleElement:
        raise ValueError("Alphabetic subpoints never have children")


@attr.s(slots=True, frozen=True)
class NumericPoint(SubArticleElement):
    ALLOWED_CHILDREN_TYPE = (AlphabeticSubpoint, )

    @classmethod
    def header_prefix(cls, identifier: Optional[str]) -> str:
        return "{}. ".format(identifier)

    def subpoint(self, sp_id: str) -> AlphabeticSubpoint:
        result = self.child(sp_id)
        assert isinstance(result, AlphabeticSubpoint)
        return result

    @classmethod
    def is_next_identifier(cls, identifier: str, next_identifier: str) -> bool:
        identifier = identifier.replace('/', '')
        next_identifier = next_identifier.replace('/', '')
        if identifier.isdigit():
            if next_identifier.isdigit():
                # "1" and "2"
                return int(identifier) + 1 == int(next_identifier)
            # "1" and "1a"
            return identifier + 'a' == next_identifier
        if next_identifier.isdigit():
            # "1a" and "2"
            # TODO: lets hope for no "1sz" or similar
            return int(identifier[:-1]) + 1 == int(next_identifier)
        # "1a" and "1b"
        return identifier[:-1] == next_identifier[:-1] and is_next_letter_hun(identifier[-1], next_identifier[-1])

    @property
    def relative_reference(self) -> 'Reference':
        return Reference(point=self.identifier)

    def at_reference(self, reference: 'Reference') -> SubArticleElement:
        assert isinstance(reference.subpoint, str)
        return self.subpoint(reference.subpoint)


@attr.s(slots=True, frozen=True)
class AlphabeticPoint(SubArticleElement):
    ALLOWED_CHILDREN_TYPE = (AlphabeticSubpoint, NumericSubpoint, )

    @classmethod
    def header_prefix(cls, identifier: Optional[str]) -> str:
        return "{}) ".format(identifier)

    def subpoint(self, sp_id: str) -> Union[AlphabeticSubpoint, NumericSubpoint]:
        result = self.child(sp_id)
        assert isinstance(result, (AlphabeticSubpoint, NumericSubpoint))
        return result

    @classmethod
    def is_next_identifier(cls, identifier: str, next_identifier: str) -> bool:
        return is_next_letter_hun(identifier, next_identifier)

    @property
    def relative_reference(self) -> 'Reference':
        return Reference(point=self.identifier)

    def at_reference(self, reference: 'Reference') -> SubArticleElement:
        assert isinstance(reference.subpoint, str)
        return self.subpoint(reference.subpoint)


@attr.s(slots=True, frozen=True)
class BlockAmendmentContainer(SubArticleElement):
    ALLOWED_CHILDREN_TYPE: ClassVar[Tuple[Type[SubArticleChildType], ...]] = ()  # Will be defined later in this file, since it uses classes defined later.
    ALLOW_DIFFERENTLY_TYPED_CHILDREN = True
    CAN_BE_SEMANTIC_PARSED = False

    @classmethod
    def header_prefix(cls, identifier: Optional[str]) -> str:
        raise TypeError("Block Amendments do not have header")

    @classmethod
    def is_next_identifier(cls, identifier: str, next_identifier: str) -> bool:
        raise TypeError("Block Amendments do not have identifiers")

    @property
    def relative_reference(self) -> 'Reference':
        raise TypeError("Block Amendments cannot be referred to.")

    def at_reference(self, reference: 'Reference') -> SubArticleElement:
        raise ValueError("Children of BlockAmendments cannotbe reached with at_reference")


@attr.s(slots=True, frozen=True)
class Paragraph(SubArticleElement):
    ALLOWED_CHILDREN_TYPE = (AlphabeticPoint, NumericPoint, QuotedBlock, BlockAmendmentContainer)

    @classmethod
    def header_prefix(cls, identifier: Optional[str]) -> str:
        if identifier is None:
            # Happens in special cases when no header was found, e.g.
            # Came from an article with a single paragraph.
            return ''
        return "({}) ".format(identifier)

    def point(self, point_id: str) -> Union[AlphabeticPoint, NumericPoint]:
        result = self.child(point_id)
        if not isinstance(result, (AlphabeticPoint, NumericPoint)):
            raise KeyError("Selected child is not a Point")
        return result

    def quoted_block(self, block_num: int) -> QuotedBlock:
        if self.children is None:
            raise KeyError("There are no children")
        result = self.children[block_num]
        if not isinstance(result, QuotedBlock):
            raise KeyError("Selected child is not a QuotedBlock")
        return result

    def block_amendment(self) -> BlockAmendmentContainer:
        if self.children is None or len(self.children) == 0:
            raise KeyError("There are no children")
        result = self.children[0]
        if not isinstance(result, BlockAmendmentContainer):
            raise KeyError("Selected child is not a BlockAmendmentContainer")
        assert len(self.children) == 1, "There should be exactly one block amendment per paragraph"
        return result

    @classmethod
    def is_next_identifier(cls, identifier: str, next_identifier: str) -> bool:
        return NumericPoint.is_next_identifier(identifier, next_identifier)

    @property
    def relative_reference(self) -> 'Reference':
        return Reference(paragraph=self.identifier)

    def at_reference(self, reference: 'Reference') -> SubArticleElement:
        assert isinstance(reference.point, str)
        point = self.point(reference.point)
        if reference.subpoint is None:
            return point
        return point.at_reference(Reference(subpoint=reference.subpoint))


@attr.s(slots=True, frozen=True, auto_attribs=True)
class Article:
    identifier: str
    children: Tuple[Paragraph, ...] = attr.ib()
    title: Optional[str] = None

    paragraph_map: Mapping[Optional[str], Paragraph] = attr.ib(init=False)

    is_semantic_parsed: bool = attr.ib(init=False)

    @children.validator
    def _children_validator(self, _attribute: Any, children: Tuple[Paragraph, ...]) -> None:
        # Attrs validators as decorators are what they are, it cannot be a function.
        # pylint: disable=no-self-use
        for c in children:
            if c.identifier is None:
                if len(children) != 1:
                    raise ValueError("Unnamed paragraphs cannot have siblings.")

    @paragraph_map.default
    def _paragraph_map_default(self) -> Mapping[Optional[str], Paragraph]:
        return {c.identifier: c for c in self.children}

    @is_semantic_parsed.default
    def _is_semantic_parsed_default(self) -> bool:
        return all(p.is_semantic_parsed for p in self.paragraphs)

    @property
    def paragraphs(self) -> Tuple[Paragraph, ...]:
        # Children are always paragraphs (see constructor)
        return self.children

    def paragraph(self, paragraph_id: Optional[str] = None) -> Paragraph:
        if paragraph_id is not None:
            return self.paragraph_map[paragraph_id]
        return self.paragraph_map[None]

    @classmethod
    def is_next_identifier(cls, identifier: str, next_identifier: str) -> bool:
        # pylint: disable=too-many-return-statements
        if (":" in identifier) != (":" in next_identifier):
            return False

        if ":" in identifier:
            book, identifier = identifier.split(":")
            next_book, next_identifier = next_identifier.split(":")
            if book != next_book:
                if int(book) + 1 == int(next_book) and next_identifier == '1':
                    return True
                return False

        if "/" not in identifier:
            if "/" not in next_identifier:
                # "1" and "2"
                return int(identifier) + 1 == int(next_identifier)
            # "1" and "1/A"
            return identifier + '/A' == next_identifier

        id1, postfix1 = identifier.split("/")
        if "/" not in next_identifier:
            # "1/A" and "2"
            return int(id1) + 1 == int(next_identifier)

        id2, postfix2 = next_identifier.split("/")
        return id1 == id2 and is_next_letter_hun(postfix1, postfix2)

    @property
    def relative_reference(self) -> 'Reference':
        return Reference(article=self.identifier)

    def at_reference(self, reference: 'Reference') -> SubArticleElement:
        assert not isinstance(reference.paragraph, tuple)
        paragraph = self.paragraph_map[reference.paragraph]
        if reference.point is None:
            return paragraph
        return paragraph.at_reference(
            Reference(
                point=reference.point,
                subpoint=reference.subpoint
            )
        )

    def map_recursive(
        self,
        parent_reference: 'Reference',
        modifier: Callable[['Reference', 'SubArticleElement'], 'SubArticleElement'],
        filter_for_reference: Optional['Reference'] = None
    ) -> 'Article':
        reference = self.relative_reference.relative_to(parent_reference)

        if filter_for_reference is not None \
                and not reference.contains(filter_for_reference) \
                and not filter_for_reference.contains(reference):
            # No need to run, no intersection between the filtered reference and any children
            return self
        new_children = []
        children_changed = False
        for child in self.children:
            new_child = child.map_recursive(reference, modifier, filter_for_reference)
            assert isinstance(new_child, Paragraph)
            if new_child is not child:
                child = new_child
                children_changed = True
            new_children.append(child)
        if not children_changed:
            return self
        return attr.evolve(self, children=tuple(new_children))


BlockAmendmentContainer.ALLOWED_CHILDREN_TYPE = (
    Article,
    Paragraph,
    AlphabeticPoint,
    NumericPoint,
    AlphabeticSubpoint,
    NumericSubpoint,
) + STRUCTURE_ELEMENT_TYPES

ActChildType = Union['StructuralElement', 'Article']


@attr.s(slots=True, frozen=True, auto_attribs=True)
class Act:
    identifier: str
    publication_date: Date
    subject: str
    preamble: str
    children: Tuple[ActChildType, ...]

    articles: Tuple[Article, ...] = attr.ib(init=False)
    articles_map: Mapping[str, Article] = attr.ib(init=False)

    is_semantic_parsed: bool = attr.ib(init=False)

    @articles.default
    def _articles_default(self) -> Tuple[Article, ...]:
        return tuple(c for c in self.children if isinstance(c, Article))

    @articles_map.default
    def _articles_map_default(self) -> Mapping[str, Article]:
        return {c.identifier: c for c in self.articles}

    @is_semantic_parsed.default
    def _is_semantic_parsed_default(self) -> bool:
        return all(p.is_semantic_parsed for p in self.articles)

    def article(self, article_id: str) -> Article:
        assert self.articles_map[str(article_id)].identifier == str(article_id)
        return self.articles_map[str(article_id)]

    def at_reference(self, reference: 'Reference') -> SubArticleElement:
        assert reference.act is None or reference.act == self.identifier
        assert isinstance(reference.article, str)
        return self.articles_map[reference.article].at_reference(
            Reference(
                paragraph=reference.paragraph,
                point=reference.point,
                subpoint=reference.subpoint
            )
        )

    def map_articles(
        self,
        modifier: Callable[['Reference', 'Article'], 'Article'],
        filter_for_reference: Optional['Reference'] = None,
    ) -> 'Act':
        new_children = []
        children_changed = False
        for child in self.children:
            if isinstance(child, Article):
                article_reference = Reference(self.identifier, child.identifier)
                if filter_for_reference is None or filter_for_reference.contains(article_reference):
                    new_child = modifier(article_reference, child)
                    if new_child is not child:
                        child = new_child
                        children_changed = True
            new_children.append(child)
        if not children_changed:
            return self
        return attr.evolve(self, children=tuple(new_children))

    def map_saes(
        self,
        modifier: Callable[['Reference', 'SubArticleElement'], 'SubArticleElement'],
        filter_for_reference: Optional['Reference'] = None
    ) -> 'Act':
        def article_modifier(_reference: Reference, article: Article) -> Article:
            return article.map_recursive(Reference(self.identifier), modifier, filter_for_reference)
        return self.map_articles(article_modifier)


ReferencePartType = Union[None, str, Tuple[str, str]]


@attr.s(slots=True, frozen=True, auto_attribs=True, order=False)
class Reference:
    # TODO: There is some weird pylint bug with tuples.
    # Something like https://github.com/PyCQA/pylint/issues/3139
    # pylint: disable=unsubscriptable-object

    act: Optional[str] = None
    article: ReferencePartType = None
    paragraph: ReferencePartType = None
    point: ReferencePartType = None
    subpoint: ReferencePartType = None

    def __lt_gt(self, other: 'Reference', lt: bool) -> bool:
        # We have to do this, because MyPy doesn't support @total_ordering:
        # https://github.com/python/mypy/issues/4610
        if not isinstance(other, Reference):
            return NotImplemented
        for component_name in 'act', 'article', 'paragraph', 'point', 'subpoint':
            self_component = getattr(self, component_name)
            other_component = getattr(other, component_name)
            if isinstance(self_component, tuple) or isinstance(other_component, tuple):
                raise ValueError("Cannot compare reference ranges", (self, other))
            if self_component != other_component:
                if self_component is None:
                    # TODO: check other self components
                    return lt
                if other_component is None:
                    return not lt
                if lt:
                    return identifier_less(self_component, other_component)
                return identifier_less(other_component, self_component)

        return False

    def __lt__(self, other: 'Reference') -> bool:
        return self.__lt_gt(other, True)

    def __gt__(self, other: 'Reference') -> bool:
        return self.__lt_gt(other, False)

    def __le__(self, other: 'Reference') -> bool:
        return self == other or self.__lt_gt(other, True)

    def __ge__(self, other: 'Reference') -> bool:
        return self == other or self.__lt_gt(other, False)

    def is_relative(self) -> bool:
        return self.act is None

    def is_range(self) -> bool:
        return (
            isinstance(self.article, tuple) or
            isinstance(self.paragraph, tuple) or
            isinstance(self.point, tuple) or
            isinstance(self.subpoint, tuple)
        )

    def relative_to(self, other: 'Reference') -> 'Reference':
        params = []
        my_part = False
        for key in ("act", "article", "paragraph", "point", "subpoint"):
            if getattr(self, key) is not None:
                my_part = True
            params.append(getattr(self if my_part else other, key))
        return Reference(*params)

    @property
    def relative_id_string(self) -> str:
        result = "ref"
        for key, id_key in (("article", "a"), ("paragraph", "p"), ("point", "pt"), ("subpoint", "sp")):
            val = getattr(self, key)
            if val is not None:
                if isinstance(val, tuple):
                    val = val[0]
                result = "{}_{}{}".format(result, id_key, val)
        return result

    def first_in_range(self) -> 'Reference':
        result = self
        if isinstance(result.article, tuple):
            result = attr.evolve(result, article=result.article[0])
        if isinstance(result.paragraph, tuple):
            result = attr.evolve(result, paragraph=result.paragraph[0])
        if isinstance(result.point, tuple):
            result = attr.evolve(result, point=result.point[0])
        if isinstance(result.subpoint, tuple):
            result = attr.evolve(result, subpoint=result.subpoint[0])
        return result

    def last_in_range(self) -> 'Reference':
        result = self
        if isinstance(result.article, tuple):
            result = attr.evolve(result, article=result.article[1])
        if isinstance(result.paragraph, tuple):
            result = attr.evolve(result, paragraph=result.paragraph[1])
        if isinstance(result.point, tuple):
            result = attr.evolve(result, point=result.point[1])
        if isinstance(result.subpoint, tuple):
            result = attr.evolve(result, subpoint=result.subpoint[1])
        return result

    @classmethod
    def make_range(cls, first: 'Reference', last: 'Reference') -> 'Reference':
        args: Dict[str, ReferencePartType] = {}
        for k in ('article', 'paragraph', 'point', 'subpoint'):
            field_first = getattr(first, k)
            field_last = getattr(last, k)
            if field_first is None:
                assert field_last is None
                args[k] = None
            else:
                assert field_last is not None
                if field_first != field_last:
                    assert identifier_less(field_first, field_last)
                    args[k] = (field_first, field_last)
                else:
                    args[k] = field_first
        act = first.act or last.act  # This is not a bool!
        return cls(act=act, **args)

    def parent(self) -> 'Reference':
        if self.subpoint is not None:
            return attr.evolve(self, subpoint=None)
        if self.point is not None:
            return attr.evolve(self, point=None)
        if self.paragraph is not None:
            return attr.evolve(self, paragraph=None)
        if self.article is not None:
            return attr.evolve(self, article=None)
        return Reference()

    def is_parent_of(self, other: 'Reference') -> bool:
        for component_name in 'act', 'article', 'paragraph', 'point', 'subpoint':
            self_component = getattr(self, component_name)
            other_component = getattr(other, component_name)
            # MAYBE TODO: Assert for not being a range
            if self_component != other_component:
                return self_component is None
        return False

    def last_component_with_type(self) -> Tuple[ReferencePartType, Optional[Type[Union[SubArticleElement, Article, Act]]]]:
        # Thanks pylint, but this is the simplest form of this function.
        # pylint: disable=too-many-return-statements
        if self.subpoint is not None:
            first_subpoint_id = self.subpoint[0] if isinstance(self.subpoint, tuple) else self.subpoint
            if first_subpoint_id[0].isdigit():
                # Both 1, 12, and 3a are NumericSubpoints.
                return self.subpoint, NumericSubpoint
            return self.subpoint, AlphabeticSubpoint
        if self.point is not None:
            first_point_id = self.point[0] if isinstance(self.point, tuple) else self.point
            if first_point_id[0].isdigit():
                # Both 1, 12, and 3a are NumericPoints.
                return self.point, NumericPoint
            return self.point, AlphabeticPoint
        if self.paragraph is not None:
            return self.paragraph, Paragraph
        if self.article is not None:
            return self.article, Article
        if self.act is not None:
            return self.act, Act
        return None, None

    def resolve_abbreviations(self, abbreviations_map: Mapping[str, str]) -> 'Reference':
        if self.act is None:
            return self
        if self.act not in abbreviations_map:
            return self
        # TODO: We have no way of determining whether the Act ID is an
        # abbreviation or not right now.
        return attr.evolve(self, act=abbreviations_map[self.act])

    def contains(self, other: 'Reference') -> bool:
        self_first = self.first_in_range()
        self_last = self.last_in_range()
        other_first = other.first_in_range()
        other_last = other.last_in_range()
        return (
            (
                (self_first <= other_first) or
                (self_first.is_parent_of(other_first))
            ) and
            (
                (self_last >= other_last) or
                (self_last.is_parent_of(other_last))
            )
        )


class SubtitleArticleComboType(Enum):
    BEFORE_WITH_ARTICLE = 1
    BEFORE_WITHOUT_ARTICLE = 2
    AFTER_WITHOUT_ARTICLE = 3


@attr.s(slots=True, frozen=True, auto_attribs=True)
class SubtitleArticleCombo:
    position: SubtitleArticleComboType
    article_id: str


@attr.s(slots=True, frozen=True, auto_attribs=True)
class StructuralReference:
    act: Optional[str] = None
    book: Optional[str] = None
    part: Optional[str] = None
    title: Optional[str] = None
    chapter: Optional[str] = None
    subtitle: Union[str, SubtitleArticleCombo, None] = None

    def resolve_abbreviations(self, abbreviations_map: Mapping[str, str]) -> 'StructuralReference':
        if self.act is None:
            return self
        if self.act not in abbreviations_map:
            return self
        # TODO: We have no way of determining whether the Act ID is an
        # abbreviation or not right now.
        return attr.evolve(self, act=abbreviations_map[self.act])


@attr.s(slots=True, frozen=True, auto_attribs=True)
class ActIdAbbreviation:
    abbreviation: str
    act: str


@attr.s(slots=True, frozen=True, auto_attribs=True, kw_only=True)
class BlockAmendment(SemanticData):
    position: Union[Reference, StructuralReference]

    def resolve_abbreviations(self, abbreviations_map: Mapping[str, str]) -> 'BlockAmendment':
        position = self.position.resolve_abbreviations(abbreviations_map)
        return attr.evolve(self, position=position)


@attr.s(slots=True, frozen=True, auto_attribs=True)
class DayInMonthAfterPublication:
    day: int
    months: int = 1


@attr.s(slots=True, frozen=True, auto_attribs=True)
class DaysAfterPublication:
    days: int = 1


@attr.s(slots=True, frozen=True, auto_attribs=True)
class SpecialEnforcementDate:
    description: str


EnforcementDateTypes = Union[Date, DaysAfterPublication, DayInMonthAfterPublication, SpecialEnforcementDate]


@attr.s(slots=True, frozen=True, auto_attribs=True, kw_only=True)
class EnforcementDate(SemanticData):
    position: Optional[Reference]
    date: EnforcementDateTypes
    repeal_date: Optional[Date] = None


@attr.s(slots=True, frozen=True, auto_attribs=True, kw_only=True)
class TextAmendment(SemanticData):
    position: Reference
    original_text: str
    replacement_text: str

    def resolve_abbreviations(self, abbreviations_map: Mapping[str, str]) -> 'TextAmendment':
        position = self.position.resolve_abbreviations(abbreviations_map)
        return attr.evolve(self, position=position)


@attr.s(slots=True, frozen=True, auto_attribs=True, kw_only=True)
class Repeal(SemanticData):
    position: Reference
    text: Optional[str] = None

    def resolve_abbreviations(self, abbreviations_map: Mapping[str, str]) -> 'Repeal':
        position = self.position.resolve_abbreviations(abbreviations_map)
        return attr.evolve(self, position=position)


def __do_post_processing() -> None:
    for _, cls in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        if attr.has(cls):
            attr.resolve_types(cls)

    # Needed for attr.s(slots=True), and __subclasses__ to work correctly.
    gc.collect()


__do_post_processing()
