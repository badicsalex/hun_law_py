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

from hun_law.utils import indented_line_wrapped_print, EMPTY_LINE

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


class StructuralElement:
    def __init__(self, identifier, title):
        self.__identifier = identifier
        self.__title = str(title)

    @property
    def identifier(self):
        return self.__identifier

    @property
    def title(self):
        return self.__title

    def print_to_console(self):
        name = "{} {}".format(self.__class__.__name__, self.identifier)
        indented_line_wrapped_print(name)
        if self.title:
            indented_line_wrapped_print(self.title)


class Book(StructuralElement):
    # 38. §, Könyv
    # Example:
    # NYOLCADIK KÖNYV
    pass


class Part(StructuralElement):
    # 39. § Rész
    # Example:
    # MÁSODIK RÉSZ
    # KÜLÖNÖS RÉSZ

    # 39. § (5)
    SPECIAL_PARTS = ('ÁLTALÁNOS RÉSZ', 'KÜLÖNÖS RÉSZ', 'ZÁRÓ RÉSZ', None)


class Title(StructuralElement):
    # "CÍM"
    # Nonconformant structural type, present only in PTK
    # Example:
    # XXI. CÍM
    pass


class Chapter(StructuralElement):
    # 40. §,  fejezet
    # Example:
    # II. FEJEZET
    # IV. Fejezet
    # XXIII. fejezet  <=  not conformant, but present in e.g. PTK
    pass


class Subtitle(StructuralElement):
    # 41. §, Alcím
    # Guaranteed to be uppercase
    # Example:
    # 17. Az alcím
    pass


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

    # TODO: identifier intro, wrapup, children
    def print_to_console(self, indent):
        if self.identifier:
            indent = indent + "{:<5}".format(self.header_prefix(self.identifier))
        else:
            indent = indent + " " * 5
        if self.text:
            indented_line_wrapped_print(self.text, indent)
        else:
            if self.intro:
                indented_line_wrapped_print(self.intro, indent)
                indent = " " * len(indent)
            for p in self.children:
                p.print_to_console(indent)
                indent = " " * len(indent)
            if self.wrap_up:
                indented_line_wrapped_print(self.wrap_up, indent)
                indent = " " * len(indent)


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

    def print_to_console(self, indent=''):
        print(indent + '„')
        indent = " " * len(indent)
        base_indent_of_quote = min(l.indent for l in self.__lines if l != EMPTY_LINE)
        for l in self.__lines:
            indent_of_quote = ' ' * int((l.indent - base_indent_of_quote)*0.2)
            print(indent + ' ' * 5 + indent_of_quote + l.content)
        print(indent + '”')


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

    def print_to_console(self, indent=''):
        indent = indent + "{:<10}".format(self.identifier + ". §")
        if self.title:
            indented_line_wrapped_print("     [{}]".format(self.title), indent)
            indent = " " * len(indent)

        for l in self.children:
            l.print_to_console(indent)
            indent = " " * len(indent)


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

    def print_to_console(self):
        indented_line_wrapped_print(self.preamble)
        print()
        for a in self.children:
            a.print_to_console()
            print()
