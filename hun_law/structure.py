# Copyright 2018 Alex Badics <admin@stickman.hu>
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


class StructuralElement(ABC):
    def __init__(self, identifier, title):
        self.__identifier = str(identifier)
        self.__title = str(title)

    @property
    def identifier(self):
        return self.__identifier

    @property
    @abstractmethod
    def formatted_identifier(self):
        pass

    @property
    def title(self):
        return self.__title


class Book(StructuralElement):
    # 38. §, Könyv
    # Example:
    # NYOLCADIK KÖNYV
    @property
    def formatted_identifier(self):
        return "{} KÖNYV".format(int_to_text_hun(int(self.identifier)).upper())


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


class Title(StructuralElement):
    # "CÍM"
    # Nonconformant structural type, present only in PTK
    # Example:
    # XXI. CÍM
    @property
    def formatted_identifier(self):
        # TODO: special parts
        return "{}. CÍM".format(int_to_text_roman(int(self.identifier)).upper())


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


class QuotedBlock:
    def __init__(self, lines):
        self.__lines = tuple(lines)

    @property
    def lines(self):
        return self.__lines

    @property
    def identifier(self):
        return None


class SubArticleElement(ABC):
    ALLOWED_CHILDREN_TYPE = ()

    def __init__(self, identifier, text, intro, children, wrap_up):
        self.__identifier = str(identifier) if identifier is not None else None
        if text is not None:
            if intro is not None or wrap_up is not None or children is not None:
                raise ValueError("SAE can contain either text or intro/wrap-up/children")
            self.__children = None
            self.__children_type = None
            self.__text = str(text)
            self.__intro = None
            self.__wrap_up = None
        else:
            if text is not None:
                raise ValueError("SAE can contain either text or intro/wrap-up/children")
            self.__text = None
            self.__intro = str(intro) if intro is not None else None
            self.__wrap_up = str(wrap_up) if wrap_up is not None else None
            self.__children = tuple(children)
            self.__children_type = type(children[0])
            if self.__children_type not in self.ALLOWED_CHILDREN_TYPE:
                raise TypeError("Children of {} can only be {} (got {})".format(type(self), self.ALLOWED_CHILDREN_TYPE, self.__children_type))
            for c in children:
                if type(c) != self.__children_type:
                    raise TypeError(
                        "All children  has to be of the  same type ({} is not {})"
                        .format(type(c), self.__children_type)
                    )
            self.__children_map = {c.identifier: c for c in children}

    @property
    def identifier(self):
        return self.__identifier

    @property
    def text(self):
        return self.__text

    @property
    def intro(self):
        return self.__intro

    @property
    def children(self):
        return self.__children

    def child(self, child_id):
        if self.__children is None:
            raise KeyError("There are no children of this element")
        return self.__children_map[str(child_id)]

    @property
    def children_type(self):
        return self.__children_type

    @property
    def wrap_up(self):
        return self.__wrap_up

    @classmethod
    @abstractmethod
    def header_prefix(cls, identifier):
        return "{}. ".format(identifier)

    @property
    @abstractmethod
    def relative_reference(self):
        pass


class AlphabeticSubpoint(SubArticleElement):
    @classmethod
    def header_prefix(cls, identifier):
        return "{}) ".format(identifier)

    @property
    def relative_reference(self):
        return Reference(subpoint=self.identifier)


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


class Article:
    def __init__(self, identifier, title, children):
        self.__identifier = str(identifier)
        self.__title = str(title) if title is not None else None
        for c in children:
            if not isinstance(c, Paragraph):
                # Always wrap everything in Pragraphs, pls.
                raise ValueError("Articles have to have Paragraphs as children")
            if c.identifier is None:
                if len(children) != 1:
                    raise ValueError("Unnamed paragraphs cannot have siblings.")

        self.__children = tuple(children)
        self.__paragraph_map = {p.identifier: p for p in children}

    @property
    def identifier(self):
        return self.__identifier

    @property
    def title(self):
        return self.__title

    @property
    def children(self):
        return self.__children

    @property
    def paragraphs(self):
        # Children are always paragraphs (see constructor)
        return self.children

    def paragraph(self, paragraph_id=None):
        if paragraph_id is not None:
            return self.__paragraph_map[str(paragraph_id)]
        else:
            return self.__paragraph_map[None]

    @property
    def relative_reference(self):
        return Reference(article=self.identifier)


class Act:
    def __init__(self, identifier, subject, preamble, children):
        self.__identifier = str(identifier)
        self.__subject = str(subject)
        self.__preamble = str(preamble)
        self.__children = tuple(children)
        self.__articles = tuple(c for c in children if isinstance(c, Article))
        self.__articles_map = {c.identifier: c for c in self.__articles}

    @property
    def identifier(self):
        return self.__identifier

    @property
    def subject(self):
        return self.__subject

    @property
    def preamble(self):
        return self.__preamble

    @property
    def children(self):
        return self.__children

    @property
    def articles(self):
        return self.__articles

    def article(self, article_id):
        return self.__articles_map[str(article_id)]


class Reference:
    def __init__(self, act=None, article=None, paragraph=None, point=None, subpoint=None):
        self.__act = act
        self.__article = article
        self.__paragraph = paragraph
        self.__point = point
        self.__subpoint = subpoint

    @property
    def act(self):
        return self.__act

    @property
    def article(self):
        return self.__article

    @property
    def paragraph(self):
        return self.__paragraph

    @property
    def point(self):
        return self.__point

    @property
    def subpoint(self):
        return self.__subpoint

    def __repr__(self):
        return "<Reference act:{!r}, article:{!r}, paragraph:{!r}, point:{!r}, subpoint:{!r}>".format(
            self.act, self.article, self.paragraph, self.point, self.subpoint
        )

    def __eq__(self, other):
        return (
            self.__act == other.act and
            self.__article == other.article and
            self.__paragraph == other.paragraph and
            self.__point == other.point and
            self.__subpoint == other.subpoint
        )

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
