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
        self.__identifier = identifier
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
        return "{} KÖNYV".format(int_to_text_hun(self.identifier).upper())


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
        return "{} RÉSZ".format(int_to_text_hun(self.identifier).upper())


class Title(StructuralElement):
    # "CÍM"
    # Nonconformant structural type, present only in PTK
    # Example:
    # XXI. CÍM
    @property
    def formatted_identifier(self):
        # TODO: special parts
        return "{}. CÍM".format(int_to_text_roman(self.identifier).upper())


class Chapter(StructuralElement):
    # 40. §,  fejezet
    # Example:
    # II. FEJEZET
    # IV. Fejezet
    # XXIII. fejezet  <=  not conformant, but present in e.g. PTK
    @property
    def formatted_identifier(self):
        # TODO: special parts
        return "{}. FEJEZET".format(int_to_text_roman(self.identifier).upper())


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


class SubArticleElement(ABC):
    def __init__(self, identifier, text, intro, children, wrap_up):
        # TODO: make sure parameters are correct type (str or None)
        # TODO: make sure either text or intro+children+wrap_up are present
        self.__identifier = identifier
        self.__text = text
        self.__intro = intro
        self.__children = None
        if children is not None:
            self.__children = tuple(children)
        self.__wrap_up = wrap_up

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

    @property
    def wrap_up(self):
        return self.__wrap_up

    @classmethod
    @abstractmethod
    def header_prefix(cls, identifier):
        return "{}. ".format(identifier)


class AlphabeticSubpoint(SubArticleElement):
    @classmethod
    def header_prefix(cls, identifier):
        return "{}) ".format(identifier)


class NumericPoint(SubArticleElement):
    @classmethod
    def header_prefix(cls, identifier):
        return "{}. ".format(identifier)


class AlphabeticPoint(SubArticleElement):
    @classmethod
    def header_prefix(cls, identifier):
        return "{}) ".format(identifier)


class Paragraph(SubArticleElement):
    @classmethod
    def header_prefix(cls, identifier):
        if identifier is None:
            # Happens in special cases when no header was found, e.g.
            # Came from an article with a single paragraph.
            return ''
        return "({}) ".format(identifier)


class QuotedBlock:
    def __init__(self, lines):
        self.__lines = tuple(lines)

    @property
    def lines(self):
        return self.__lines


class Article:
    def __init__(self, identifier, title, children):
        self.__identifier = str(identifier)
        if title is None:
            self.__title = None
        else:
            self.__title = str(title)
        self.__children = tuple(children)

    @property
    def identifier(self):
        return self.__identifier

    @property
    def title(self):
        return self.__title

    @property
    def children(self):
        return self.__children


class Act:
    def __init__(self, identifier, subject, preamble, children):
        self.__identifier = str(identifier)
        self.__subject = str(subject)
        self.__preamble = str(preamble)
        self.__children = tuple(children)

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
