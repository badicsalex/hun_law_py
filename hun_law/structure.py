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
import attr
from abc import ABC, abstractmethod

from hun_law.utils import int_to_text_hun, int_to_text_roman

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


@attr.s(slots=True, frozen=True)
class StructuralElement(ABC):
    identifier = attr.ib(converter=str)
    title = attr.ib(converter=str)

    @property
    @abstractmethod
    def formatted_identifier(self):
        pass


@attr.s(slots=True, frozen=True)
class Book(StructuralElement):
    # 38. §, Könyv
    # Example:
    # NYOLCADIK KÖNYV
    @property
    def formatted_identifier(self):
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
    def formatted_identifier(self):
        # TODO: special parts
        return "{} RÉSZ".format(int_to_text_hun(int(self.identifier)).upper())


@attr.s(slots=True, frozen=True)
class Title(StructuralElement):
    # "CÍM"
    # Nonconformant structural type, present only in PTK
    # Example:
    # XXI. CÍM
    @property
    def formatted_identifier(self):
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
    def formatted_identifier(self):
        # TODO: special parts
        return "{}. FEJEZET".format(int_to_text_roman(int(self.identifier)).upper())


@attr.s(slots=True, frozen=True)
class Subtitle(StructuralElement):
    # 41. §, Alcím
    # Guaranteed to be uppercase
    # Example:
    # 17. Az alcím
    @property
    def formatted_identifier(self):
        # TODO: special parts
        return "{}.".format(self.identifier)


STRUCTURE_ELEMENT_TYPES = (Subtitle, Chapter, Title, Part, Book)


@attr.s(slots=True, frozen=True)
class OutgoingReference:
    # Start and end pos are python range, i.e. end_pos is after the last character
    start_pos = attr.ib(converter=int)
    end_pos = attr.ib(converter=int)
    reference = attr.ib()


@attr.s(slots=True, frozen=True)
class QuotedBlock:
    lines = attr.ib(converter=tuple)

    identifier = attr.ib(default=None, init=False)


@attr.s(slots=True, frozen=True)
class SubArticleElement(ABC):
    ALLOWED_CHILDREN_TYPE = ()

    identifier = attr.ib(converter=attr.converters.optional(str))
    text = attr.ib(converter=attr.converters.optional(str))
    intro = attr.ib(converter=attr.converters.optional(str))
    children = attr.ib(converter=attr.converters.optional(tuple))
    wrap_up = attr.ib(converter=attr.converters.optional(str))
    outgoing_references = attr.ib(default=None, converter=attr.converters.default_if_none(factory=tuple))

    children_type = attr.ib(init=False)
    children_map = attr.ib(init=False)

    @children_type.default
    def _children_type_default(self):
        if self.children is None:
            return None
        return type(self.children[0])

    @children_map.default
    def _children_map_default(self):
        if self.children is None:
            return None
        return {c.identifier: c for c in self.children}

    @text.validator
    def _content_validator_if_text(self, attribute, text):
        if text is not None:
            if self.intro is not None or self.wrap_up is not None or self.children is not None:
                raise ValueError("SAE can contain either text or intro/wrap-up/children")

    @children.validator
    def _content_validator_if_children(self, attribute, children):
        if self.children_type is None:
            return
        if self.children_type not in self.ALLOWED_CHILDREN_TYPE:
            raise TypeError("Children of {} can only be {} (got {})".format(type(self), self.ALLOWED_CHILDREN_TYPE, self.children_type))
        for c in children:
            if type(c) != self.children_type:
                raise TypeError(
                    "All children  has to be of the  same type ({} is not {})"
                    .format(type(c), self.children_type)
                )

    def child(self, child_id):
        if self.children is None:
            raise KeyError("There are no children of this element")
        return self.children_map[str(child_id)]

    @classmethod
    @abstractmethod
    def header_prefix(cls, identifier):
        return "{}. ".format(identifier)

    @property
    @abstractmethod
    def relative_reference(self):
        pass


@attr.s(slots=True, frozen=True)
class AlphabeticSubpoint(SubArticleElement):
    @classmethod
    def header_prefix(cls, identifier):
        return "{}) ".format(identifier)

    @property
    def relative_reference(self):
        return Reference(subpoint=self.identifier)


@attr.s(slots=True, frozen=True)
class NumericPoint(SubArticleElement):
    ALLOWED_CHILDREN_TYPE = (AlphabeticSubpoint, )

    @classmethod
    def header_prefix(cls, identifier):
        return "{}. ".format(identifier)

    def subpoint(self, sp_id):
        return self.child(sp_id)

    @property
    def relative_reference(self):
        return Reference(point=self.identifier)


@attr.s(slots=True, frozen=True)
class AlphabeticPoint(SubArticleElement):
    ALLOWED_CHILDREN_TYPE = (AlphabeticSubpoint, )

    @classmethod
    def header_prefix(cls, identifier):
        return "{}) ".format(identifier)

    def subpoint(self, sp_id):
        return self.child(sp_id)

    @property
    def relative_reference(self):
        return Reference(point=self.identifier)


@attr.s(slots=True, frozen=True)
class Paragraph(SubArticleElement):
    ALLOWED_CHILDREN_TYPE = (AlphabeticPoint, NumericPoint, QuotedBlock)

    @classmethod
    def header_prefix(cls, identifier):
        if identifier is None:
            # Happens in special cases when no header was found, e.g.
            # Came from an article with a single paragraph.
            return ''
        return "({}) ".format(identifier)

    def point(self, point_id):
        if self.children_type not in (AlphabeticPoint, NumericPoint):
            raise KeyError("There are no points in this paragraph")
        return self.child(point_id)

    def quoted_block(self, block_num):
        if self.children_type not in (QuotedBlock,):
            raise KeyError("There are no quoted blocks in this paragraph")
        return self.children[block_num]

    @property
    def relative_reference(self):
        return Reference(paragraph=self.identifier)


@attr.s(slots=True, frozen=True)
class Article:
    identifier = attr.ib(converter=str)
    title = attr.ib(converter=attr.converters.optional(str))
    children = attr.ib(converter=tuple)

    paragraph_map = attr.ib(init=False)

    @children.validator
    def _children_validator(self, attribute, children):
        for c in children:
            if not isinstance(c, Paragraph):
                # Always wrap everything in Pragraphs, pls.
                raise ValueError("Articles have to have Paragraphs as children")
            if c.identifier is None:
                if len(children) != 1:
                    raise ValueError("Unnamed paragraphs cannot have siblings.")

    @paragraph_map.default
    def _paragraph_map_default(self):
        return {c.identifier: c for c in self.children}

    @property
    def paragraphs(self):
        # Children are always paragraphs (see constructor)
        return self.children

    def paragraph(self, paragraph_id=None):
        if paragraph_id is not None:
            return self.paragraph_map[str(paragraph_id)]
        else:
            return self.paragraph_map[None]

    @property
    def relative_reference(self):
        return Reference(article=self.identifier)


@attr.s(slots=True, frozen=True)
class Act:
    identifier = attr.ib(converter=str)
    subject = attr.ib(converter=str)
    preamble = attr.ib(converter=str)
    children = attr.ib(converter=tuple)

    articles = attr.ib(init=False)
    articles_map = attr.ib(init=False)

    @articles.default
    def _articles_default(self):
        return tuple(c for c in self.children if isinstance(c, Article))

    @articles_map.default
    def _articles_map_default(self):
        return {c.identifier: c for c in self.articles}

    def article(self, article_id):
        assert self.articles_map[str(article_id)].identifier == str(article_id)
        return self.articles_map[str(article_id)]

    def iter_all_outgoing_references(self):
        for article in self.articles:
            for paragraph in article.paragraphs:
                yield from self.__iter_all_outgoing_references_recursive(
                    paragraph,
                    Reference(article=article.identifier, paragraph=paragraph.identifier)
                )

    @classmethod
    def __iter_all_outgoing_references_recursive(cls, element, parent_ref):
        if not isinstance(element, SubArticleElement):
            return
        current_ref = element.relative_reference.relative_to(parent_ref)
        for outgoing_ref in element.outgoing_references:
            yield current_ref, outgoing_ref.reference.relative_to(parent_ref)
        if element.children:
            for child in element.children:
                yield from cls.__iter_all_outgoing_references_recursive(child, current_ref)


@attr.s(slots=True, frozen=True)
class Reference:
    act = attr.ib(default=None)
    article = attr.ib(default=None)
    paragraph = attr.ib(default=None)
    point = attr.ib(default=None)
    subpoint = attr.ib(default=None)

    def is_relative(self):
        return self.act is None

    def is_range(self):
        return (
            isinstance(self.article, tuple) or
            isinstance(self.paragraph, tuple) or
            isinstance(self.point, tuple) or
            isinstance(self.subpoint, tuple)
        )

    def relative_to(self, other):
        params = []
        my_part = False
        for key in ("act", "article", "paragraph", "point", "subpoint"):
            if getattr(self, key) is not None:
                my_part = True
            params.append(getattr(self if my_part else other, key))
        return Reference(*params)

    @property
    def relative_id_string(self):
        result = "ref"
        for key, id_key in (("article", "a"), ("paragraph", "p"), ("point", "pt"), ("subpoint", "sp")):
            val = getattr(self, key)
            if val is not None:
                if isinstance(val, tuple):
                    val = val[0]
                result = "{}_{}{}".format(result, id_key, val)
        return result


@attr.s(slots=True, frozen=True)
class ActIdAbbreviation:
    abbreviation = attr.ib(converter=str)
    act = attr.ib(converter=str)


@attr.s(slots=True, frozen=True)
class BlockAmendmentMetadata:
    amended_reference = attr.ib(converter=str)
