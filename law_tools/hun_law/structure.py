# Copyright 2018 Alex Badics <admin@stickman.hu>
#
# This file is part of Law-tools.
#
# Law-tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Law-tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Law-tools.  If not, see <https://www.gnu.org/licenses/>.

import re
from abc import ABC, abstractmethod

from . import amendment
from law_tools.utils import IndentedLine, EMPTY_LINE, int_to_text_hun, int_to_text_roman, is_uppercase_hun, indented_line_wrapped_print

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


class StructuralElement(ABC):
    def __init__(self, sibling_before=None, lines=None):
        # TODO: Assert first line is correct with is_line_...
        if sibling_before is None:
            self.number = 1
        else:
            self.number = sibling_before.number + 1
        self.title = " ".join([l.content for l in lines[1:]])

    @classmethod
    @abstractmethod
    def is_line_header_of_first(cls, line):
        pass

    @abstractmethod
    def is_line_header_of_next(self, line):
        pass

    def print_to_console(self):
        name = "{} {}".format(self.__class__.__name__, self.number)
        indented_line_wrapped_print(name)
        if self.title:
            indented_line_wrapped_print(self.title)


class Book (StructuralElement):
    # 38. §, Könyv
    # Guaranteed to be uppercase
    # Example:
    # NYOLCADIK KÖNYV
    def __init__(self, sibling_before=None, lines=None):
        super().__init__(sibling_before, lines)
        self.header_of_next = int_to_text_hun(self.number + 1).upper() + ' KÖNYV'

    @classmethod
    def is_line_header_of_first(cls, line):
        return line.content == 'ELSŐ KÖNYV'

    def is_line_header_of_next(self, line):
        return line.content == self.header_of_next


class Part (StructuralElement):
    # 39. § Rész
    # Guaranteed to be uppercase
    # Example:
    # MÁSODIK RÉSZ
    # KÜLÖNÖS RÉSZ

    # 39. § (5)
    SPECIAL_PARTS = ('ÁLTALÁNOS RÉSZ', 'KÜLÖNÖS RÉSZ', 'ZÁRÓ RÉSZ', None)

    def __init__(self, sibling_before=None, lines=None):
        super().__init__(sibling_before, lines)
        if sibling_before is None:
            self.special = lines == self.SPECIAL_PARTS[0]
        else:
            self.special = sibling_before.special
        if self.special:
            self.header_of_next = self.SPECIAL_PARTS[self.number]  # remember that numbers are indexed from 1
        else:
            self.header_of_next = int_to_text_hun(self.number + 1).upper() + ' RÉSZ'

    @classmethod
    def is_line_header_of_first(cls, line):
        return line.content == 'ELSŐ RÉSZ' or line.content == cls.SPECIAL_PARTS[0]

    def is_line_header_of_next(self, line):
        return line.content == self.header_of_next


class Title (StructuralElement):
    # "CÍM"
    # Nonconformant structural type, present only in PTK
    # Example:
    # XXI. CÍM
    def __init__(self, sibling_before=None, lines=None):
        super().__init__(sibling_before, lines)
        self.header_of_next = int_to_text_roman(self.number + 1) + '. CÍM'

    @classmethod
    def is_line_header_of_first(cls, line):
        return line.content == 'I. CÍM'

    def is_line_header_of_next(self, line):
        return line.content == self.header_of_next


class Chapter(StructuralElement):
    # 40. §,  fejezet
    # Example:
    # II. FEJEZET
    # IV. Fejezet
    # XXIII. fejezet  <=  not conformant, but present in e.g. PTK
    def __init__(self, sibling_before=None, lines=None):
        super().__init__(sibling_before, lines)
        self.header_of_next = int_to_text_roman(self.number + 1) + '. FEJEZET'

    @classmethod
    def is_line_header_of_first(cls, line):
        return line.content.upper() == 'I. FEJEZET'

    def is_line_header_of_next(self, line):
        return line.content.upper() == self.header_of_next


class Subtitle(StructuralElement):
    # 41. §, Alcím
    # Guaranteed to be uppercase
    # Example:
    # 17. Az alcím

    def __init__(self, sibling_before=None, lines=None):
        super().__init__(sibling_before, lines)
        prefix_of_current = '{}. '.format(self.number)
        full_title = " ".join([l.content for l in lines])
        self.title = full_title.split(prefix_of_current, maxsplit=1)[1]
        self.prefix_of_next = '{}. '.format(self.number + 1)

    @classmethod
    def is_line_correct(cls, prefix, line):
        if len(line.content) < len(prefix) + 1:
            return False
        if not line.content.startswith(prefix):
            return False
        if not is_uppercase_hun(line.content[len(prefix)]):
            return False
        return True

    @classmethod
    def is_line_header_of_first(cls, line):
        return cls.is_line_correct('1. ', line)

    def is_line_header_of_next(self, line):
        return self.is_line_correct(self.prefix_of_next, line)


STRUCTURE_ELEMENT_TYPES = (Subtitle, Chapter, Title, Part, Book)


class SubArticleElementNotFoundError(Exception):
    pass


class SubArticleElement(ABC):
    PARENT_MUST_HAVE_INTRO = False
    PARENT_MUST_HAVE_MULTIPLE_OF_THIS = False
    PARENT_CAN_HAVE_WRAPUP = False

    def __init__(self, text, identifier):
        self.identifier = identifier
        self.text = None
        self.intro = None
        self.children = None
        self.wrap_up = None

        prefix = self.header_prefix(identifier)
        if not text[0].content.startswith(prefix):
            raise ValueError("Invalid {} header ('{}' does not start with '{}'".format(self.__class__.__name__, text[0].content, prefix))

        truncated_first_line = text[0].content[len(prefix):]
        # TODO XXX: This indentation is certainly wrong and WILL come back to haunt us
        indented_first_line = IndentedLine(truncated_first_line, text[0].indent)
        text = [indented_first_line] + text[1:]
        if not self.try_parse_subpoints(text):
            self.text = " ".join([l.content for l in text])

    @classmethod
    @abstractmethod
    def header_prefix(cls, identifier):
        pass

    @classmethod
    @abstractmethod
    def first_identifier(cls):
        pass

    @classmethod
    @abstractmethod
    def next_identifier(cls, identifier):
        pass

    @abstractmethod
    def try_parse_subpoints(self, text):
        pass

    @classmethod
    def is_header(cls, line, identifier):
        prefix = cls.header_prefix(identifier)
        return line.content.startswith(prefix)

    @classmethod
    def extract_multiple_from_text(cls, text):
        elements = []
        intro = None
        wrap_up = None
        current_element_identifier = None
        next_element_identifier = cls.first_identifier()
        current_lines = []
        quote_level = 0
        for line in text:
            if quote_level == 0 and cls.is_header(line, next_element_identifier):
                if current_element_identifier is None:
                    if current_lines:
                        intro = " ".join([l.content for l in current_lines])
                else:
                    element = cls(current_lines, current_element_identifier)
                    elements.append(element)

                current_element_identifier = next_element_identifier
                next_element_identifier = cls.next_identifier(next_element_identifier)
                current_lines = []
            quote_level = quote_level + line.content.count("„") + line.content.count("“") - line.content.count("”")
            current_lines.append(line)

        if quote_level != 0:
            raise ValueError("Malformed quoting. (Quote_level = {})".format(quote_level))

        # There is one element in current_lines, and if no other elements have been found,
        # there is a total of one. That's not valid for a list of points or subpoints
        if len(elements) == 0 and cls.PARENT_MUST_HAVE_MULTIPLE_OF_THIS:
            raise SubArticleElementNotFoundError("Not enough elements of type {} found in text.".format(cls.__name__))

        if intro is None and cls.PARENT_MUST_HAVE_INTRO:
            raise SubArticleElementNotFoundError("No intro found in text.")

        if cls.PARENT_CAN_HAVE_WRAPUP:
            # TODO: This is a stupid heuristic: we hope line-broken points are indented, while
            # the wrapup will be at the same level as the headers.
            header_indent = current_lines[0].indent
            if len(current_lines) > 1 and current_lines[-1].indent == header_indent:
                wrap_up = current_lines.pop().content
                while len(current_lines) > 1 and current_lines[-1].indent == header_indent:
                    wrap_up = current_lines.pop().content + " " + wrap_up

        element = cls(current_lines, current_element_identifier)
        elements.append(element)
        return intro, elements, wrap_up

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
    PARENT_MUST_HAVE_INTRO = True  # 47. § (2)
    PARENT_MUST_HAVE_MULTIPLE_OF_THIS = True
    PARENT_CAN_HAVE_WRAPUP = True

    PREFIX = ''

    @classmethod
    def first_identifier(cls):
        return cls.PREFIX + 'a'

    @classmethod
    def next_identifier(cls, identifier):
        if cls.PREFIX:
            if cls.PREFIX != identifier[0]:
                raise ValueError("Invalid identifier for prefixed subpoint")
            return cls.PREFIX + chr(ord(identifier[1]) + 1)
        else:
            return chr(ord(identifier) + 1)

    @classmethod
    def header_prefix(cls, identifier):
        return "{}) ".format(identifier)

    @classmethod
    def is_header(cls, line, identifier):
        prefix = cls.header_prefix(identifier)
        return line.content.startswith(prefix)

    def try_parse_subpoints(self, text):
        # Subpoints may not have sub-subpoints: 48. § (6)
        return False


class NumericPoint(SubArticleElement):
    PARENT_MUST_HAVE_INTRO = True  # 47. § (2)
    PARENT_MUST_HAVE_MULTIPLE_OF_THIS = True
    # No PARENT_CAN_HAVE_WRAPUP, because it looks like numbered lists are usuaally
    # not well-indented, i.e.:
    # 1. Element: blalbalba, lalblblablabl, lbalb
    # blballabalvblbla, lbblaa.
    # 2. Element: saddsadasdsadsa, adsdsadas
    # adsasddas.

    @classmethod
    def first_identifier(cls):
        return '1'

    @classmethod
    def next_identifier(cls, identifier):
        return str(int(identifier) + 1)

    @classmethod
    def header_prefix(cls, identifier):
        return "{}. ".format(identifier)

    def try_parse_subpoints(self, text):
        # Numbered points may only have alphabetic subpoints.
        try:
            self.intro, self.children, self.wrap_up = AlphabeticSubpoint.extract_multiple_from_text(text)
            return True
        except SubArticleElementNotFoundError:
            pass

        return False


class AlphabeticPoint(SubArticleElement):
    PARENT_MUST_HAVE_INTRO = True  # 47. § (2)
    PARENT_MUST_HAVE_MULTIPLE_OF_THIS = True
    PARENT_CAN_HAVE_WRAPUP = True

    @classmethod
    def first_identifier(cls):
        return 'a'

    @classmethod
    def next_identifier(cls, identifier):
        return chr(ord(identifier) + 1)

    @classmethod
    def header_prefix(cls, identifier):
        return "{}) ".format(identifier)

    def try_parse_subpoints(self, text):
        # Soo, this is a great example of functional-oop hybrid things, which i
        # both pretty compact, elegant, and disgusting at the same time.
        # Thank 48. § (3) for this.
        my_letter = self.identifier

        class PrefixedAlphabeticSubpoint(AlphabeticSubpoint):
            PREFIX = my_letter

        # Numbered points may only have alphabetic subpoints.
        try:
            self.intro, self.children, self.wrap_up = PrefixedAlphabeticSubpoint.extract_multiple_from_text(text)
            return True
        except SubArticleElementNotFoundError:
            pass

        return False


class Paragraph(SubArticleElement):
    @classmethod
    def first_identifier(cls):
        return '1'

    @classmethod
    def next_identifier(cls, identifier):
        return str(int(identifier) + 1)

    @classmethod
    def header_prefix(cls, identifier):
        if identifier is None:
            # Happens in special cases when no header was found, e.g.
            # Came from an article with a single paragraph.
            return ''
        return "({}) ".format(identifier)

    def try_parse_subpoints(self, text):
        # We look for amendments in paragraphs only, because of "115. § (2)",
        # "Articles and below may only be amended in Paragraphs", and because
        # we always parse Articles into a single Paragraph, even without a
        # paragraph header.
        try:
            self.children = [amendment.StructuredAmendment(text)]
            return True
        except amendment.NotAmendmentError as e:
            pass

        try:
            self.intro, self.children, self.wrap_up = NumericPoint.extract_multiple_from_text(text)
            return True
        except SubArticleElementNotFoundError:
            pass

        try:
            self.intro, self.children, self.wrap_up = AlphabeticPoint.extract_multiple_from_text(text)
            return True
        except SubArticleElementNotFoundError:
            pass

        return False


class Article:
    HEADER_RE = re.compile("^([0-9]+:)?([0-9]+)\\. ?§ *(.*)$")

    def __init__(self, text, extenally_determined_identifier=None):
        # text parameter includes the line with the '§'
        header_matches = self.HEADER_RE.match(text[0].content)
        if header_matches.group(1):
            # group(1) already has the ":"
            self.identifier = header_matches.group(1) + header_matches.group(2)
        else:
            self.identifier = header_matches.group(2)

        if extenally_determined_identifier and extenally_determined_identifier != self.identifier:
            raise ValueError(
                "Parsed identifier != got identifier: '{}'!='{}'"
                .format(identifier, self.extenally_determined_identifier)
            )

        self.title = ""
        self.paragraphs = []

        truncated_first_line = header_matches.group(3)
        # TODO XXX: This indentation is certainly wrong and WILL come back to haunt us
        indented_first_line = IndentedLine(truncated_first_line, text[0].indent)
        self.parse_body([indented_first_line] + text[1:])

    @classmethod
    def is_header(cls, line):
        # TODO: check numbering of previous Article
        # TODO: check indentation
        return cls.HEADER_RE.match(line.content)

    def parse_body(self, text):
        if text[0].content[0] == '[':
            # Nonstandard. However, it is a de facto thing to give titles to Articles
            # In some Acts. Format is something like
            # 3:116. §  [A társaság képviselete. Cégjegyzés]
            # Let's hope for no multiline titles for now
            if text[0].content[-1] != ']':
                raise ValueError("Multiline article titles not supported")
            self.title = text[0].content[1:-1]
            # TODO: Optimize this, if needed
            text = text[1:]

        intro, self.paragraphs, wrap_up = Paragraph.extract_multiple_from_text(text)
        if intro is not None:
            raise ValueError("Junk detected in Article before first Paragraph")
        if wrap_up is not None:
            raise ValueError("Junk detected in Article after last Paragraph")

    def print_to_console(self, indent=''):
        indent = indent + "{:<10}".format(self.identifier + ". §")
        if self.title:
            indented_line_wrapped_print("     [{}]".format(self.title), indent)
            indent = " " * len(indent)

        for l in self.paragraphs:
            l.print_to_console(indent)
            indent = " " * len(indent)


class Act:
    def __init__(self, identifier, subject, text):
        self.identifier = identifier
        self.subject = subject
        self.preamble = None
        self.elements = []
        self.last_structural_element_per_class = {}
        self.parse_text(text)

    def parse_text(self, text):
        current_lines = []
        article_header_indent = None
        for line in text:
            if Article.is_header(line):
                # TODO: Let's hope article numbers are always left-justified
                if article_header_indent is None:
                    article_header_indent = line.indent
                if abs(line.indent-article_header_indent) < 1:
                    self.parse_text_block(current_lines)
                    current_lines = []
            current_lines.append(line)
        self.parse_text_block(current_lines)

    def parse_text_block(self, lines):
        lines, elements_to_append = self.parse_structural_elements(lines)
        # EMPTY_LINEs are only needed for detecting structural elements.
        # From this point, they only mess up parsing, so let's get rid of them
        # TODO: Large Structured Amendments that replace whole Parts could need
        # empty lines again, so be careful.
        lines = [l for l in lines if l != EMPTY_LINE]
        if self.preamble is None:
            self.preamble = " ".join([l.content for l in lines])
        else:
            self.elements.append(Article(lines))
        self.elements.extend(elements_to_append)

    def parse_structural_elements(self, lines):
        result = []
        while lines[-1] == EMPTY_LINE:
            lines.pop()
            if EMPTY_LINE not in lines:
                break
            possible_title_index = len(lines) - lines[::-1].index(EMPTY_LINE)
            element = self.parse_single_structural_element(lines[possible_title_index:])
            if not element:
                break
            result.insert(0, element)
            self.last_structural_element_per_class[element.__class__] = element
            lines = lines[:possible_title_index]
        return lines, result

    def parse_single_structural_element(self, lines):
        for se_type in STRUCTURE_ELEMENT_TYPES:
            # TODO: we do not impose ANY rules about restarting numbering here
            # this is by design for now, as many laws are pretty much malformed.
            if se_type.is_line_header_of_first(lines[0]):
                return se_type(None, lines)
            if se_type in self.last_structural_element_per_class:
                last_se = self.last_structural_element_per_class[se_type]
                if last_se.is_line_header_of_next(lines[0]):
                    return se_type(last_se, lines)
        return None

    def print_to_console(self):
        indented_line_wrapped_print(self.preamble)
        print()
        for a in self.elements:
            a.print_to_console()
            print()
