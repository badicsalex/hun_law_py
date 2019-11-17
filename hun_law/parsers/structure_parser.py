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

import re
from abc import ABC, abstractmethod
from enum import Enum

from hun_law.utils import \
    IndentedLine, EMPTY_LINE, int_to_text_hun, int_to_text_roman, \
    is_uppercase_hun, iterate_with_quote_level, quote_level_diff
from hun_law.structure import \
    Act, Article, QuotedBlock, BlockAmendment,\
    Subtitle, Chapter, Title, Part, Book,\
    Paragraph, AlphabeticSubpoint, NumericPoint, AlphabeticPoint

# Main act on which all the code was based:
# 61/2009. (XII. 14.) IRM rendelet a jogszabályszerkesztésről

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


class StructureParsingError(ValueError):
    def __init__(self, message, parser_class=None, identifier=None):
        if parser_class is not None:
            super().__init__(
                "Error in {} {}: '{}'".format(
                    parser_class.__name__,
                    identifier,
                    message
                )
            )
        else:
            super().__init__(message)


class StructuralElementParser(ABC):
    PARSED_TYPE = None

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

    def get_parsed_element(self):
        return self.PARSED_TYPE(self.number, self.title)


class BookParser(StructuralElementParser):
    # 38. §, Könyv
    # Guaranteed to be uppercase
    # Example:
    # NYOLCADIK KÖNYV
    PARSED_TYPE = Book

    def __init__(self, sibling_before=None, lines=None):
        super().__init__(sibling_before, lines)
        self.header_of_next = int_to_text_hun(self.number + 1).upper() + ' KÖNYV'

    @classmethod
    def is_line_header_of_first(cls, line):
        return line.content == 'ELSŐ KÖNYV'

    def is_line_header_of_next(self, line):
        return line.content == self.header_of_next


class PartParser(StructuralElementParser):
    # 39. § Rész
    # Guaranteed to be uppercase
    # Example:
    # MÁSODIK RÉSZ
    # KÜLÖNÖS RÉSZ
    PARSED_TYPE = Part

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


class TitleParser(StructuralElementParser):
    # "CÍM"
    # Nonconformant structural type, present only in PTK
    # Example:
    # XXI. CÍM
    PARSED_TYPE = Title

    def __init__(self, sibling_before=None, lines=None):
        super().__init__(sibling_before, lines)
        self.header_of_next = int_to_text_roman(self.number + 1) + '. CÍM'

    @classmethod
    def is_line_header_of_first(cls, line):
        return line.content == 'I. CÍM'

    def is_line_header_of_next(self, line):
        return line.content == self.header_of_next


class ChapterParser(StructuralElementParser):
    # 40. §,  fejezet
    # Example:
    # II. FEJEZET
    # IV. Fejezet
    # XXIII. fejezet  <=  not conformant, but present in e.g. PTK
    PARSED_TYPE = Chapter

    def __init__(self, sibling_before=None, lines=None):
        super().__init__(sibling_before, lines)
        self.header_of_next = int_to_text_roman(self.number + 1) + '. FEJEZET'

    @classmethod
    def is_line_header_of_first(cls, line):
        return line.content.upper() == 'I. FEJEZET'

    def is_line_header_of_next(self, line):
        return line.content.upper() == self.header_of_next


class SubtitleParser(StructuralElementParser):
    # 41. §, Alcím
    # Guaranteed to be uppercase
    # Example:
    # 17. Az alcím
    # For older acts, there is no number, only a text.

    PARSED_TYPE = Subtitle

    def __init__(self, sibling_before=None, lines=None):
        super().__init__(sibling_before, lines)
        prefix_of_current = '{}. '.format(self.number)
        full_title = " ".join([l.content for l in lines])
        if prefix_of_current in full_title:
            self.title = full_title.split(prefix_of_current, maxsplit=1)[1]
            self.no_number = False
        else:
            # We got called most probably because of the "bold" condition
            # in is_line_header... Or something's wrong in the code.
            assert lines[0].bold
            self.title = full_title
            self.no_number = True

        self.prefix_of_next = '{}. '.format(self.number + 1)

    @classmethod
    def is_line_correct(cls, prefix, line):
        # Huge hack: most subtitles are bold.
        # We also depend on only getting called when we are probably a
        # subtitle, i.e. there was an empty line above this one, and probably
        # another one below it.
        # Also see __init__
        if line.bold and is_uppercase_hun(line.content[0]):
            return True

        # Checks for the default, numbered case
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

    def get_parsed_element(self):
        return self.PARSED_TYPE(
            identifier="" if self.no_number else self.number,
            title=self.title
        )


STRUCTURE_ELEMENT_PARSERS = (
    BookParser,
    PartParser,
    TitleParser,
    ChapterParser,
    SubtitleParser,
)


class SubArticleElementNotFoundError(Exception):
    pass


class NoSubpointsError(Exception):
    pass


class SubArticleParsingError(StructureParsingError):
    pass


class SubArticleElementParser(ABC):
    PARSED_TYPE = None

    PARENT_MUST_HAVE_INTRO = False
    PARENT_MUST_HAVE_MULTIPLE_OF_THIS = False
    PARENT_CAN_HAVE_WRAPUP = False

    @classmethod
    def parse(cls, lines, identifier):
        text = None
        intro = None
        children = None
        wrap_up = None

        prefix = cls.PARSED_TYPE.header_prefix(identifier)
        if not lines[0].content.startswith(prefix):
            raise SubArticleParsingError("Invalid header ('{}' does not start with '{}'".format(lines[0].content, prefix), cls.PARSED_TYPE)

        truncated_first_line = lines[0].content[len(prefix):]
        indented_first_line = lines[0].slice(len(prefix))
        lines = [indented_first_line] + lines[1:]
        try:
            intro, children, wrap_up = cls.try_parse_subpoints(lines, identifier)
        except NoSubpointsError:
            text = " ".join([l.content for l in lines if l != EMPTY_LINE])
        except Exception as e:
            raise SubArticleParsingError("Error during parsing subpoints: {}".format(e), cls.PARSED_TYPE) from e
        return cls.PARSED_TYPE(identifier, text, intro, children, wrap_up)

    @classmethod
    @abstractmethod
    def first_identifier(cls):
        pass

    @classmethod
    @abstractmethod
    def try_parse_subpoints(cls, lines, parent_identifier):
        pass

    @classmethod
    def is_header(cls, line, identifier):
        prefix = cls.PARSED_TYPE.header_prefix(identifier)
        return line.content.startswith(prefix)

    @classmethod
    def extract_multiple_from_text(cls, lines):
        elements = []
        intro = None
        wrap_up = None
        current_element_identifier = None
        next_element_identifier = cls.first_identifier()
        current_lines = []
        header_indentation = None
        for quote_level, line in iterate_with_quote_level(lines):
            if (
                quote_level == 0 and
                # The last or is a must, because e.g. Paragraph headers are not right-justified, but left.
                # i.e.
                #  (9)
                # (10)
                (header_indentation is None or similar_indent(header_indentation, line.indent) or line.indent < header_indentation) and
                cls.is_header(line, next_element_identifier)
            ):
                if current_element_identifier is None:
                    if current_lines:
                        intro = " ".join([l.content for l in current_lines])
                else:
                    element = cls.parse(current_lines, current_element_identifier)
                    elements.append(element)

                header_indentation = line.indent
                current_element_identifier = next_element_identifier
                next_element_identifier = cls.PARSED_TYPE.next_identifier(next_element_identifier)
                current_lines = []
            current_lines.append(line)

        # There is one element in current_lines, and if no other elements have been found,
        # there is a total of one. That's not valid for a list of points or subpoints
        if not elements and cls.PARENT_MUST_HAVE_MULTIPLE_OF_THIS:
            raise SubArticleElementNotFoundError("Not enough elements of type {} found in text.".format(cls.__name__))

        if intro is None and cls.PARENT_MUST_HAVE_INTRO:
            raise SubArticleElementNotFoundError("No intro found in text.")

        if cls.PARENT_CAN_HAVE_WRAPUP:
            # TODO: This is a stupid heuristic: we hope line-broken points are indented, while
            # the wrapup will be at the same level as the headers.
            header_indent = current_lines[0].indent
            if len(current_lines) > 1 and similar_indent(current_lines[-1].indent, header_indent):
                wrap_up = current_lines.pop().content
                while len(current_lines) > 1 and similar_indent(current_lines[-1].indent, header_indent):
                    wrap_up = current_lines.pop().content + " " + wrap_up

        element = cls.parse(current_lines, current_element_identifier)
        elements.append(element)
        return intro, elements, wrap_up


class AlphabeticSubpointParser(SubArticleElementParser):
    PARSED_TYPE = AlphabeticSubpoint

    PARENT_MUST_HAVE_INTRO = True  # 47. § (2)
    PARENT_MUST_HAVE_MULTIPLE_OF_THIS = True
    PARENT_CAN_HAVE_WRAPUP = True

    PREFIX = ''

    @classmethod
    def first_identifier(cls):
        return cls.PREFIX + 'a'

    @classmethod
    def is_header(cls, line, identifier):
        prefix = cls.PARSED_TYPE.header_prefix(identifier)
        return line.content.startswith(prefix)

    @classmethod
    def try_parse_subpoints(cls, lines, parent_identifier):
        # Subpoints may not have sub-subpoints: 48. § (6)
        raise NoSubpointsError()


def get_prefixed_alphabetic_subpoint_parser(prefix):
    # Soo, this is a great example of functional-oop hybrid things, which i
    # both pretty compact, elegant, and disgusting at the same time.
    # Thank 48. § (3) for this.
    class PrefixedAlphabeticSubpointParser(AlphabeticSubpointParser):
        PREFIX = prefix
    return PrefixedAlphabeticSubpointParser


class NumericPointParser(SubArticleElementParser):
    PARSED_TYPE = NumericPoint

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
    def try_parse_subpoints(cls, lines, parent_identifier):
        # Numbered points may only have alphabetic subpoints.
        try:
            return AlphabeticSubpointParser.extract_multiple_from_text(lines)
        except SubArticleElementNotFoundError:
            pass

        raise NoSubpointsError()


class AlphabeticPointParser(SubArticleElementParser):
    PARSED_TYPE = AlphabeticPoint

    PARENT_MUST_HAVE_INTRO = True  # 47. § (2)
    PARENT_MUST_HAVE_MULTIPLE_OF_THIS = True
    PARENT_CAN_HAVE_WRAPUP = True

    @classmethod
    def first_identifier(cls):
        return 'a'

    @classmethod
    def try_parse_subpoints(cls, lines, parent_identifier):
        # Numbered points may only have alphabetic subpoints.
        try:
            parser = get_prefixed_alphabetic_subpoint_parser(parent_identifier)
            return parser.extract_multiple_from_text(lines)
        except SubArticleElementNotFoundError:
            pass

        raise NoSubpointsError()


class ParagraphParser(SubArticleElementParser):
    PARSED_TYPE = Paragraph

    @classmethod
    def first_identifier(cls):
        return '1'

    @classmethod
    def try_parse_subpoints(cls, lines, parent_identifier):
        # We look for block quotes in paragraphs only, because both amendments
        # and international agreements only appear in Paragraph and Article
        # level, and we always parse Articles into a single Paragraph.
        try:
            return QuotedBlockParser.extract_multiple_from_text(lines)
        except SubArticleElementNotFoundError:
            pass

        # EMPTY_LINEs are only needed for detecting structural elements.
        # From this point, they only mess up parsing, so let's get rid of them
        # TODO: Large Structured Amendments that replace whole Parts could need
        # empty lines again, so be careful.
        lines = [l for l in lines if l != EMPTY_LINE]

        try:
            return NumericPointParser.extract_multiple_from_text(lines)
        except SubArticleElementNotFoundError:
            pass

        try:
            return AlphabeticPointParser.extract_multiple_from_text(lines)
        except SubArticleElementNotFoundError:
            pass

        raise NoSubpointsError()


class QuotedBlockParser:
    ParseStates = Enum('ParseStates', ('START', 'INTRO', 'QUOTED_BLOCK', 'WRAP_UP_MAYBE', 'WRAP_UP'))

    @classmethod
    def extract_multiple_from_text(cls, lines):
        state = cls.ParseStates.START
        blocks = []
        wrap_up = None
        for quote_level, line in iterate_with_quote_level(lines):
            # No if "EMPTY_LINE:continue" here, because QUOTED_BLOCK
            # state needs them to operate correctly.
            if state == cls.ParseStates.START:
                if line != EMPTY_LINE:
                    intro = line.content
                    state = cls.ParseStates.INTRO

            elif state == cls.ParseStates.INTRO:
                if line != EMPTY_LINE:
                    if line.content[0] == "„" and quote_level == 0:
                        if line.content[-1] == "”":
                            quoted_lines = [line.slice(1, -1)]
                            blocks.append(QuotedBlock(quoted_lines))
                            quoted_lines = None
                            state = cls.ParseStates.WRAP_UP_MAYBE
                        else:
                            quoted_lines = [line.slice(1)]
                            state = cls.ParseStates.QUOTED_BLOCK
                    else:
                        intro = intro + " " + line.content

            elif state == cls.ParseStates.QUOTED_BLOCK:
                quote_level_at_line_end = quote_level + quote_level_diff(line.content)
                if line != EMPTY_LINE and line.content[-1] == "”" and quote_level_at_line_end == 0:
                    quoted_lines.append(line.slice(0, -1))
                    blocks.append(QuotedBlock(quoted_lines))
                    quoted_lines = None
                    state = cls.ParseStates.WRAP_UP_MAYBE
                # Note that this else also applies to EMPTY_LINEs
                else:
                    quoted_lines.append(line)

            elif state == cls.ParseStates.WRAP_UP_MAYBE:
                if line != EMPTY_LINE:
                    if line.content[0] == "„" and quote_level == 0:
                        if line.content[-1] == "”":
                            quoted_lines = [line.slice(1, -1)]
                            blocks.append(QuotedBlock(quoted_lines))
                            quoted_lines = None
                        else:
                            quoted_lines = [line.slice(1)]
                            state = cls.ParseStates.QUOTED_BLOCK
                    else:
                        wrap_up = line.content
                        state = cls.ParseStates.WRAP_UP

            elif state == cls.ParseStates.WRAP_UP:
                if line != EMPTY_LINE:
                    wrap_up = wrap_up + ' ' + line.content

            else:
                raise RuntimeError('Unknown state')

        if state not in (cls.ParseStates.WRAP_UP, cls.ParseStates.WRAP_UP_MAYBE):
            raise SubArticleElementNotFoundError()

        return intro, blocks, wrap_up


class ArticleParsingError(StructureParsingError):
    pass


class ArticleParser:
    PARSED_TYPE = Article

    HEADER_RE = re.compile("^([0-9]+:)?([0-9]+(/[A-Z])?)\\. ?§ *(.*)$")

    @classmethod
    def parse(cls, lines, extenally_determined_identifier=None):
        # lines parameter includes the line with the '§'
        header_matches = cls.HEADER_RE.match(lines[0].content)
        if header_matches.group(1):
            # group(1) already has the ":"
            identifier = header_matches.group(1) + header_matches.group(2)
        else:
            identifier = header_matches.group(2)

        if extenally_determined_identifier and extenally_determined_identifier != identifier:
            raise ArticleParsingError(
                "Externally determined identifier wrong: '{}'".format(extenally_determined_identifier),
                Article
            )

        truncated_first_line = lines[0].slice(header_matches.start(4), header_matches.end(4))
        try:
            return cls.parse_body(identifier, [truncated_first_line] + lines[1:])
        except Exception as e:
            raise ArticleParsingError(str(e), Article, identifier) from e

    @classmethod
    def is_header(cls, line, extenally_determined_identifier=None):
        # TODO: check indentation
        if extenally_determined_identifier is None:
            return cls.HEADER_RE.match(line.content)
        else:
            prefix1 = extenally_determined_identifier + '. §'
            prefix2 = extenally_determined_identifier + '.§'
            return line.content.startswith(prefix1) or line.content.startswith(prefix2)

    @classmethod
    def parse_body(cls, identifier, lines):
        title = None
        paragraphs = []

        if lines[0].content[0] == '[':
            # Nonstandard. However, it is a de facto thing to give titles to Articles
            # In some Acts. Format is something like
            # 3:116. §  [A társaság képviselete. Cégjegyzés]
            # Let's hope for no multiline titles for now
            if lines[0].content[-1] == ']':
                title = lines[0].content[1:-1]
                lines = lines[1:]
            elif lines[1].content[-1] == ']':
                title = lines[0].content[1:] + " " + lines[1].content[:-1]
                lines = lines[2:]
            else:
                raise ValueError("Multiline article titles not supported")

        if lines[0] == EMPTY_LINE:
            # Pathological case where there is an empty line between the article title
            # and the actual content. Very very rare, basically only happens in an
            # amendment in 2013. évi CCLII. törvény 185. § (18)
            # There can only be at most 1 consecutive EMPTY_LINE because of previous
            # preprocessing in the PDF extractor.
            lines = lines[1:]

        if not ParagraphParser.is_header(lines[0], ParagraphParser.first_identifier()):
            paragraphs = [ParagraphParser.parse(lines, None)]
        else:
            intro, paragraphs, wrap_up = ParagraphParser.extract_multiple_from_text(lines)
            if intro is not None:
                # Should LITERALLY never happen
                raise ValueError("Junk detected in Article before first Paragraph")
            if wrap_up is not None:
                raise ValueError("Junk detected in Article after last Paragraph")
        return Article(identifier, paragraphs, title)


class ActParsingError(StructureParsingError):
    pass


class ActStructureParser:
    PARSED_TYPE = Act

    @classmethod
    def parse(cls, identifier, subject, lines):
        try:
            preamble, elements = cls.parse_text(lines)
        except Exception as e:
            raise ActParsingError("Error during parsing body: {}".format(e), Act, identifier) from e

        return Act(identifier, subject, preamble, elements)

    @classmethod
    def parse_text(cls, lines):
        current_lines = []
        article_header_indent = None
        preamble = None
        elements = []
        last_structural_element_parser = {}
        for quote_level, line in iterate_with_quote_level(lines):
            if quote_level == 0 and ArticleParser.is_header(line):
                # TODO: Let's hope article numbers are always left-justified
                if article_header_indent is None:
                    article_header_indent = line.indent
                if similar_indent(line.indent, article_header_indent):
                    preamble, new_elements = cls.parse_text_block(current_lines, preamble, last_structural_element_parser)
                    elements.extend(new_elements)
                    current_lines = []
            current_lines.append(line)
        preamble, new_elements = cls.parse_text_block(current_lines, preamble, last_structural_element_parser)
        elements.extend(new_elements)
        return preamble, elements

    @classmethod
    def parse_text_block(cls, lines, preamble, last_structural_element_parser):
        lines, elements_to_append = cls.parse_structural_elements(lines, last_structural_element_parser)
        if preamble is None:
            preamble = " ".join([l.content for l in lines if l != EMPTY_LINE])
        else:
            elements_to_append.insert(0, ArticleParser.parse(lines))
        return preamble, elements_to_append

    @classmethod
    def parse_structural_elements(cls, lines, last_structural_element_parser):
        result = []
        while lines and lines[-1] == EMPTY_LINE:
            lines.pop()
            if EMPTY_LINE not in lines:
                break
            possible_title_index = len(lines) - lines[::-1].index(EMPTY_LINE)
            possible_text = " ".join([l.content for l in lines[possible_title_index:]])
            if quote_level_diff(possible_text):
                # There is some unclosed quoting, most probably we would parse into
                # a quoted text. Don't to anything.
                # E.g.
                # ...
                # 5. Some title in aquoted text
                # 6. Some other thing"
                break
            element_parser = cls.parse_single_structural_element(lines[possible_title_index:], last_structural_element_parser)
            if not element_parser:
                break
            result.insert(0, element_parser.get_parsed_element())
            last_structural_element_parser[element_parser.__class__] = element_parser
            lines = lines[:possible_title_index]
        return lines, result

    @classmethod
    def parse_single_structural_element(cls, lines, last_structural_element_parser):
        for se_type in STRUCTURE_ELEMENT_PARSERS:
            # TODO: we do not impose ANY rules about restarting numbering here
            # this is by design for now, as many laws are pretty much malformed.
            if se_type.is_line_header_of_first(lines[0]):
                return se_type(None, lines)
            if se_type in last_structural_element_parser:
                last_se = last_structural_element_parser[se_type]
                if last_se.is_line_header_of_next(lines[0]):
                    return se_type(last_se, lines)
        return None


class BlockAmendmentStructureParser:
    PARSERS_FOR_TYPE = {
        Article: ArticleParser,
        Paragraph: ParagraphParser,
        AlphabeticPoint: AlphabeticPointParser,
        NumericPoint: NumericPointParser,
        AlphabeticSubpoint: AlphabeticSubpointParser,  # In the default case at least
    }

    @classmethod
    def parse(cls, expected_reference, context_intro, context_wrap_up, lines):
        parser, expected_id = cls.get_parser_and_id(expected_reference)
        children = tuple(cls.do_parse_block_by_block(parser, expected_id, lines))
        return BlockAmendment(
            identifier=None,
            text=None,
            intro=context_intro,
            children=children,
            wrap_up=context_wrap_up
        )

    @classmethod
    def do_parse_block_by_block(cls, parser, expected_id, lines):
        current_lines = []
        next_id = parser.PARSED_TYPE.next_identifier(expected_id)
        for quote_level, line in iterate_with_quote_level(lines):
            if current_lines and quote_level == 0 and parser.is_header(line, next_id):
                yield parser.parse(current_lines, expected_id)
                expected_id = next_id
                next_id = parser.PARSED_TYPE.next_identifier(expected_id)
                current_lines = []
            current_lines.append(line)
        yield parser.parse(current_lines, expected_id)

    @classmethod
    def get_parser_and_id(cls, expected_reference):
        expected_id, structural_type = expected_reference.last_component_with_type()
        if isinstance(expected_id, tuple):
            # In case of reference range, get start of range.
            # TODO: check for end of range too
            expected_id = expected_id[0]

        if structural_type is AlphabeticSubpoint and len(expected_id) != 1:
            # TODO: let's hope it is not a two-letter subpoint like "ny"
            return get_prefixed_alphabetic_subpoint_parser(expected_id[:-1]), expected_id
        return cls.PARSERS_FOR_TYPE[structural_type], expected_id


def similar_indent(a, b):
    # Super scientific
    return abs(a - b) < 1
