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
from typing import Type, Pattern, ClassVar, Sequence, Optional, Tuple, Iterable, Iterator, Union, List, Mapping

from hun_law.utils import \
    IndentedLine, EMPTY_LINE, text_to_int_hun, text_to_int_roman, \
    is_uppercase_hun, iterate_with_quote_level, quote_level_diff
from hun_law.structure import \
    Act, Article, QuotedBlock, BlockAmendment,\
    StructuralElement, Subtitle, Chapter, Title, Part, Book,\
    SubArticleElement, Paragraph, AlphabeticSubpoint, NumericSubpoint, NumericPoint, AlphabeticPoint, \
    BlockAmendmentMetadata, \
    SubArticleChildType, ActChildType

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
    def __init__(self, message: str, parser_class: Optional[Type] = None, identifier: Optional[str] = None):
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
    PARSED_TYPE: ClassVar[Type[StructuralElement]]
    strict: bool

    def __init__(self, strict: bool = True) -> None:
        self.expected_number = 1
        self.strict = strict

    @abstractmethod
    def extract_number(self, line: IndentedLine) -> Optional[int]:
        pass

    def step_to_next_number(self, line: IndentedLine) -> None:
        extracted = self.extract_number(line)
        if extracted is None:
            self.expected_number = 1
        else:
            self.expected_number = extracted + 1

    def is_header(self, line: IndentedLine, _previous_line: IndentedLine) -> bool:
        number = self.extract_number(line)
        if not self.strict:
            return number is not None
        return number in (1, self.expected_number)

    def parse(self, lines: Sequence[IndentedLine]) -> StructuralElement:
        number = self.extract_number(lines[0])
        title = " ".join(l.content for l in lines[1:] if l != EMPTY_LINE)
        return self.PARSED_TYPE(str(number), title)


class BookParser(StructuralElementParser):
    # 38. §, Könyv
    # Guaranteed to be uppercase
    # Example:
    # NYOLCADIK KÖNYV
    PARSED_TYPE = Book
    HEADER_REGEX = re.compile(r'(.*) KÖNYV$')

    def extract_number(self, line: IndentedLine) -> Optional[int]:
        result = self.HEADER_REGEX.match(line.content)
        if result is None:
            return None
        try:
            return text_to_int_hun(result.group(1))
        except ValueError:
            return None


class PartParser(StructuralElementParser):
    # 39. § Rész
    # Guaranteed to be uppercase
    # Example:
    # MÁSODIK RÉSZ
    # KÜLÖNÖS RÉSZ
    PARSED_TYPE = Part

    # 39. § (5)
    SPECIAL_PARTS = ('ÁLTALÁNOS RÉSZ', 'KÜLÖNÖS RÉSZ', 'ZÁRÓ RÉSZ')

    HEADER_REGEX = re.compile(r'(.*) RÉSZ$')

    def __init__(self, strict: bool = True) -> None:
        super().__init__(strict)
        self.is_special = False

    def extract_number(self, line: IndentedLine) -> Optional[int]:
        if line.content in self.SPECIAL_PARTS:
            return self.SPECIAL_PARTS.index(line.content) + 1

        result = self.HEADER_REGEX.match(line.content)
        if result is None:
            return None
        try:
            return text_to_int_hun(result.group(1))
        except ValueError:
            return None


class TitleParser(StructuralElementParser):
    # "CÍM"
    # Nonconformant structural type, present only in PTK
    # Example:
    # XXI. CÍM
    PARSED_TYPE = Title

    HEADER_REGEX = re.compile(r'(.*)\. CÍM$')

    def extract_number(self, line: IndentedLine) -> Optional[int]:
        result = self.HEADER_REGEX.match(line.content)
        if result is None:
            return None
        try:
            return text_to_int_roman(result.group(1))
        except ValueError:
            return None


class ChapterParser(StructuralElementParser):
    # 40. §,  fejezet
    # Example:
    # II. FEJEZET
    # IV. Fejezet
    # XXIII. fejezet  <=  not conformant, but present in e.g. PTK
    PARSED_TYPE = Chapter

    HEADER_REGEX = re.compile(r'(.*)\. fejezet$', flags=re.IGNORECASE)

    def extract_number(self, line: IndentedLine) -> Optional[int]:
        result = self.HEADER_REGEX.match(line.content)
        if result is None:
            return None
        try:
            return text_to_int_roman(result.group(1))
        except ValueError:
            return None


class SubtitleParser(StructuralElementParser):
    # 41. §, Alcím
    # Guaranteed to be uppercase
    # Example:
    # 17. Az alcím
    # For older acts, there is no number, only a text.

    PARSED_TYPE = Subtitle

    HEADER_REGEX = re.compile(r'([0-9]+)\. ')

    def extract_number(self, line: IndentedLine) -> Optional[int]:
        result = self.HEADER_REGEX.match(line.content)
        if result is None:
            return None
        try:
            return int(result.group(1))
        except ValueError:
            return None

    def is_header(self, line: IndentedLine, previous_line: IndentedLine) -> bool:
        if not line.bold:
            return False
        if not self.strict:
            return is_uppercase_hun(line.content[0]) or self.extract_number(line) is not None

        if previous_line == EMPTY_LINE and is_uppercase_hun(line.content[0]):
            return True
        number = self.extract_number(line)
        return number in (1, self.expected_number)

    def parse(self, lines: Sequence[IndentedLine]) -> Subtitle:
        title = " ".join(l.content for l in lines if l != EMPTY_LINE)
        number = self.extract_number(lines[0])
        if number is None:
            return Subtitle("", title)
        title = title.split('. ', 1)[1]
        return Subtitle(str(number), title)


class ArticleStructuralParser:
    # This class is mostly a fake StructuralParser, so that Act and
    # BlockAmendment parsers can use it as structural parser.
    PARSED_TYPE = None

    def __init__(self, strict: bool = True) -> None:
        self.strict = strict
        self.indent: Optional[float] = None

    def step_to_next_number(self, line: IndentedLine) -> None:
        self.indent = line.indent

    def is_header(self, line: IndentedLine, _previous_line: IndentedLine) -> bool:
        if self.indent is not None and not similar_indent(line.indent, self.indent):
            return False
        return ArticleParser.extract_identifier(line) is not None

    @classmethod
    def parse(cls, lines: Sequence[IndentedLine]) -> Article:
        return ArticleParser.parse(lines)


STRUCTURE_ELEMENT_PARSERS: Tuple[Type[Union[StructuralElementParser, ArticleStructuralParser]], ...] = (
    ArticleStructuralParser,
    BookParser,
    PartParser,
    TitleParser,
    ChapterParser,
    SubtitleParser,
)


class SubArticleElementNotFoundError(Exception):
    pass


class NoSubelementsError(Exception):
    pass


class SubArticleParsingError(StructureParsingError):
    pass


class SubArticleElementParser(ABC):
    PARSED_TYPE: ClassVar[Type[SubArticleElement]]
    HEADER_REGEX: ClassVar[Pattern]

    PARENT_MUST_HAVE_INTRO: ClassVar[bool] = False
    PARENT_MUST_HAVE_MULTIPLE_OF_THIS: ClassVar[bool] = False
    PARENT_CAN_HAVE_WRAPUP: ClassVar[bool] = False

    @classmethod
    def parse(cls, lines: Sequence[IndentedLine]) -> SubArticleElement:
        text = None
        intro = None
        children = None
        wrap_up = None

        identifier = cls.extract_identifier(lines[0])
        prefix = cls.PARSED_TYPE.header_prefix(identifier)
        assert lines[0].content.startswith(prefix)

        indented_first_line = lines[0].slice(len(prefix))
        lines = (indented_first_line, ) + tuple(lines[1:])
        try:
            intro, children, wrap_up = cls.parse_children_and_wrapup(lines, identifier)
        except NoSubelementsError:
            text = " ".join([l.content for l in lines if l != EMPTY_LINE])
        except Exception as e:
            raise SubArticleParsingError("Error during parsing subpoints: {}".format(e), cls.PARSED_TYPE) from e
        return cls.PARSED_TYPE(identifier, text, intro, children, wrap_up)

    @classmethod
    def parse_children_and_wrapup(cls, lines: Sequence[IndentedLine], parent_identifier: Optional[str]) -> Tuple[Optional[str], Tuple[Union[SubArticleElement, QuotedBlock], ...], Optional[str]]:
        parsers_with_first_header = []
        for parser in cls.get_subelement_parsers(parent_identifier):
            first_header = parser.find_first_header(lines)
            if first_header is None:
                continue
            if first_header == 0 and parser.PARENT_MUST_HAVE_INTRO:
                continue
            parsers_with_first_header.append((first_header, parser))

        parsers_with_first_header.sort()
        for first_header, parser in parsers_with_first_header:
            try:
                if first_header == 0:
                    intro = None
                else:
                    intro = " ".join([l.content for l in lines[:first_header] if l != EMPTY_LINE])
                children, wrapup = parser.extract_multiple_from_text(lines[first_header:])
                return intro, children, wrapup
            except SubArticleElementNotFoundError:
                pass
        raise NoSubelementsError()

    @classmethod
    @abstractmethod
    def first_identifier(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def get_subelement_parsers(cls, parent_identifier: Optional[str]) -> Tuple[Type[Union['SubArticleElementParser', 'QuotedBlockParser']], ...]:
        # Function, since it can be dymnamic
        pass

    @classmethod
    def extract_identifier(cls, line: IndentedLine) -> Optional[str]:
        result = cls.HEADER_REGEX.match(line.content)
        return None if result is None else result.group(1)

    @classmethod
    def find_first_header(cls, lines: Iterable[IndentedLine]) -> Optional[int]:
        return next(cls.find_header_lines(lines), None)

    @classmethod
    def find_header_lines(cls, lines: Iterable[IndentedLine], expected_first_identifier: Optional[str] = None) -> Iterator[int]:
        if expected_first_identifier is None:
            expected_first_identifier = cls.first_identifier()
        last_identifier = None
        header_indentation = None
        for lineno, (quote_level, line) in enumerate(iterate_with_quote_level(lines)):
            if quote_level != 0:
                continue

            # The last and is a must, because e.g. Paragraph headers are not right-justified, but left.
            # i.e.
            #  (9)
            # (10)
            if header_indentation is not None and not similar_indent(header_indentation, line.indent) and line.indent > header_indentation:
                continue

            extracted_identifier = cls.extract_identifier(line)
            if extracted_identifier is None:
                continue
            if last_identifier is None:
                if extracted_identifier != expected_first_identifier:
                    continue
            else:
                if not cls.PARSED_TYPE.is_next_identifier(last_identifier, extracted_identifier):
                    continue

            yield lineno
            last_identifier = extracted_identifier
            header_indentation = line.indent

    @classmethod
    def split_last_item_and_wrapup(cls, lines: Iterable[IndentedLine]) -> Tuple[Tuple[IndentedLine, ...], Optional[str]]:
        wrap_up = None
        if cls.PARENT_CAN_HAVE_WRAPUP:
            lines = list(lines)
            # TODO: This is a stupid heuristic: we hope line-broken points are indented, while
            # the wrapup will be at the same level as the headers.
            header_indent = lines[0].indent
            wrap_up = None
            while len(lines) > 1 and (lines[-1] == EMPTY_LINE or similar_indent(lines[-1].indent, header_indent)):
                line = lines.pop()
                if line == EMPTY_LINE:
                    continue
                if wrap_up is None:
                    wrap_up = line.content
                else:
                    wrap_up = line.content + " " + wrap_up
        return tuple(lines), wrap_up

    @classmethod
    def extract_multiple_from_text(cls, lines: Sequence[IndentedLine]) -> Tuple[Tuple['SubArticleElement', ...], Optional[str]]:
        header_lines = tuple(cls.find_header_lines(lines))
        # The only way this is not true is a programming error,
        # it is the callers job to assure this.
        assert header_lines[0] == 0
        assert cls.extract_identifier(lines[0]) == cls.first_identifier()

        if len(header_lines) < 2 and cls.PARENT_MUST_HAVE_MULTIPLE_OF_THIS:
            raise SubArticleElementNotFoundError("Not enough elements of type {} found in text.".format(cls.__name__))

        elements = []
        for start, stop in zip(header_lines[:-1], header_lines[1:]):
            element = cls.parse(lines[start:stop])
            elements.append(element)

        remaining_lines, wrap_up = cls.split_last_item_and_wrapup(lines[header_lines[-1]:])
        element = cls.parse(remaining_lines)
        elements.append(element)
        return tuple(elements), wrap_up


class AlphabeticSubpointParser(SubArticleElementParser):
    PARSED_TYPE = AlphabeticSubpoint

    PARENT_MUST_HAVE_INTRO = True  # 47. § (2)
    PARENT_MUST_HAVE_MULTIPLE_OF_THIS = True
    PARENT_CAN_HAVE_WRAPUP = True

    PREFIX = ''
    HEADER_REGEX = re.compile(r'([a-z]|ny|sz)\) ')

    @classmethod
    def first_identifier(cls) -> str:
        return cls.PREFIX + 'a'

    @classmethod
    def get_subelement_parsers(cls, parent_identifier: Optional[str]) -> Tuple[Type[Union['SubArticleElementParser', 'QuotedBlockParser']], ...]:
        return ()


def get_prefixed_alphabetic_subpoint_parser(prefix: str) -> Type[AlphabeticSubpointParser]:
    # Soo, this is a great example of functional-oop hybrid things, which i
    # both pretty compact, elegant, and disgusting at the same time.
    # Thank 48. § (3) for this.
    class PrefixedAlphabeticSubpointParser(AlphabeticSubpointParser):
        PREFIX = prefix
        HEADER_REGEX = re.compile(r'({}[a-z]|ny|sz)\) '.format(prefix))
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

    HEADER_REGEX = re.compile(r'([0-9]+(/?[a-z])?)\. ')

    @classmethod
    def first_identifier(cls) -> str:
        return '1'

    @classmethod
    def get_subelement_parsers(cls, parent_identifier: Optional[str]) -> Tuple[Type[Union['SubArticleElementParser', 'QuotedBlockParser']], ...]:
        return (AlphabeticSubpointParser,)


class NumericSubpointParser(SubArticleElementParser):
    PARSED_TYPE = NumericSubpoint

    PARENT_MUST_HAVE_INTRO = True  # 47. § (2)
    PARENT_MUST_HAVE_MULTIPLE_OF_THIS = True
    # No PARENT_CAN_HAVE_WRAPUP, because it looks like numbered lists are usuaally
    # not well-indented, i.e.:
    # 1. Element: blalbalba, lalblblablabl, lbalb
    # blballabalvblbla, lbblaa.
    # 2. Element: saddsadasdsadsa, adsdsadas
    # adsasddas.

    HEADER_REGEX = re.compile(r'([0-9]+(/?[a-z])?)\. ')

    @classmethod
    def first_identifier(cls) -> str:
        return '1'

    @classmethod
    def get_subelement_parsers(cls, parent_identifier: Optional[str]) -> Tuple[Type[Union['SubArticleElementParser', 'QuotedBlockParser']], ...]:
        return ()


class AlphabeticPointParser(SubArticleElementParser):
    PARSED_TYPE = AlphabeticPoint

    PARENT_MUST_HAVE_INTRO = True  # 47. § (2)
    PARENT_MUST_HAVE_MULTIPLE_OF_THIS = True
    PARENT_CAN_HAVE_WRAPUP = True

    HEADER_REGEX = re.compile(r'([a-z]|ny|sz)\) ')

    @classmethod
    def first_identifier(cls) -> str:
        return 'a'

    @classmethod
    def get_subelement_parsers(cls, parent_identifier: Optional[str]) -> Tuple[Type[Union['SubArticleElementParser', 'QuotedBlockParser']], ...]:
        # The parents of course have an ide. What would be the prefix otherwise?
        # Also, only Paragraphs may have None as the ID
        assert parent_identifier is not None
        parser = get_prefixed_alphabetic_subpoint_parser(parent_identifier)
        return (NumericSubpointParser, parser,)


class ParagraphParser(SubArticleElementParser):
    PARSED_TYPE = Paragraph

    HEADER_REGEX = re.compile(r'\(([0-9]+[a-z]?)\) ')

    @classmethod
    def first_identifier(cls) -> str:
        return '1'

    @classmethod
    def get_subelement_parsers(cls, parent_identifier: Optional[str]) -> Tuple[Type[Union['SubArticleElementParser', 'QuotedBlockParser']], ...]:
        return (QuotedBlockParser, AlphabeticPointParser, NumericPointParser)


class QuotedBlockParser:
    ParseStates = Enum('ParseStates', ('START', 'QUOTED_BLOCK', 'WRAP_UP_MAYBE', 'WRAP_UP'))
    PARENT_MUST_HAVE_INTRO = True

    @classmethod
    def find_first_header(cls, lines: Iterable[IndentedLine]) -> Optional[int]:
        for lineno, (quote_level, line) in enumerate(iterate_with_quote_level(lines)):
            if quote_level == 0 and line != EMPTY_LINE and line.content[0] in ("„", "“"):
                return lineno
        return None

    @classmethod
    def extract_multiple_from_text(cls, lines: Iterable[IndentedLine]) -> Tuple[Tuple[QuotedBlock, ...], Optional[str]]:
        # pylint: disable=too-many-branches
        state = cls.ParseStates.START
        blocks = []
        wrap_up = None
        quoted_lines: List[IndentedLine]
        for quote_level, line in iterate_with_quote_level(lines):
            # No if "EMPTY_LINE:continue" here, because QUOTED_BLOCK
            # state needs them to operate correctly.
            if state == cls.ParseStates.START:
                if line != EMPTY_LINE:
                    # This is the job of the caller: only call this function where
                    # "lines" surely starts with the quoted block itself
                    assert line.content[0] in ("„", "“") and quote_level == 0
                    if line.content[-1] == "”":
                        quoted_lines = [line.slice(1, -1)]
                        blocks.append(QuotedBlock(tuple(quoted_lines)))
                        state = cls.ParseStates.WRAP_UP_MAYBE
                    else:
                        quoted_lines = [line.slice(1)]
                        state = cls.ParseStates.QUOTED_BLOCK

            elif state == cls.ParseStates.QUOTED_BLOCK:
                quote_level_at_line_end = quote_level + quote_level_diff(line.content)
                if line != EMPTY_LINE and line.content[-1] == "”" and quote_level_at_line_end == 0:
                    quoted_lines.append(line.slice(0, -1))
                    blocks.append(QuotedBlock(tuple(quoted_lines)))
                    state = cls.ParseStates.WRAP_UP_MAYBE
                # Note that this else also applies to EMPTY_LINEs
                else:
                    quoted_lines.append(line)

            elif state == cls.ParseStates.WRAP_UP_MAYBE:
                if line != EMPTY_LINE:
                    if line.content[0] in ("„", "“") and quote_level == 0:
                        if line.content[-1] == "”":
                            quoted_lines = [line.slice(1, -1)]
                            blocks.append(QuotedBlock(tuple(quoted_lines)))
                        else:
                            quoted_lines = [line.slice(1)]
                            state = cls.ParseStates.QUOTED_BLOCK
                    else:
                        wrap_up = line.content
                        state = cls.ParseStates.WRAP_UP

            elif state == cls.ParseStates.WRAP_UP:
                if line != EMPTY_LINE:
                    assert wrap_up is not None
                    wrap_up = wrap_up + ' ' + line.content

            else:
                raise RuntimeError('Unknown state')

        if state not in (cls.ParseStates.WRAP_UP, cls.ParseStates.WRAP_UP_MAYBE):
            raise SubArticleElementNotFoundError()

        return tuple(blocks), wrap_up


class ArticleParsingError(StructureParsingError):
    pass


class ArticleParser:
    PARSED_TYPE = Article

    HEADER_REGEX = re.compile("^(([0-9]+:)?([0-9]+(/[A-Z])?))\\. ?§ +(.*)$")

    @classmethod
    def parse(cls, lines: Sequence[IndentedLine], extenally_determined_identifier: Optional[str] = None) -> Article:
        identifier = cls.extract_identifier(lines[0])
        if identifier is None:
            raise ArticleParsingError("Article does not have a proper header '{}'".format(lines[0].content))

        if extenally_determined_identifier and extenally_determined_identifier != identifier:
            raise ArticleParsingError(
                "Externally determined identifier wrong: '{}'".format(extenally_determined_identifier),
                Article
            )
        # Space intentionally left after the sign.
        position_of_article_sign = lines[0].content.index('§ ')
        truncated_first_line = lines[0].slice(position_of_article_sign + 2)
        try:
            return cls.parse_body(identifier, (truncated_first_line, ) + tuple(lines[1:]))
        except Exception as e:
            raise ArticleParsingError(str(e), Article, identifier) from e

    @classmethod
    def extract_identifier(cls, line: IndentedLine) -> Optional[str]:
        result = cls.HEADER_REGEX.match(line.content)
        return None if result is None else result.group(1)

    @classmethod
    def parse_body(cls, identifier: str, lines: Sequence[IndentedLine]) -> Article:
        title = None

        if lines[0].content[0] == '[':
            # Nonstandard. However, it is a de facto thing to give titles to Articles
            # In some Acts. Format is something like
            # 3:116. §  [A társaság képviselete. Cégjegyzés]
            if lines[0].content[-1] == ']':
                title = lines[0].content[1:-1]
                lines = lines[1:]
            elif lines[1].content[-1] == ']':
                title = lines[0].content[1:] + " " + lines[1].content[:-1]
                lines = lines[2:]
            elif lines[2].content[-1] == ']':
                title = lines[0].content[1:] + " " + lines[1].content + " " + lines[1].content[:-1]
                lines = lines[3:]
            else:
                # Seriously, we are at 3 at this point.
                raise ValueError("Over-long article titles not supported")

        if lines[0] == EMPTY_LINE:
            # Pathological case where there is an empty line between the article title
            # and the actual content. Very very rare, basically only happens in an
            # amendment in 2013. évi CCLII. törvény 185. § (18)
            # There can only be at most 1 consecutive EMPTY_LINE because of previous
            # preprocessing in the PDF extractor.
            lines = lines[1:]

        if not ParagraphParser.extract_identifier(lines[0]) == ParagraphParser.first_identifier():
            paragraphs: Tuple[SubArticleElement, ...] = (ParagraphParser.parse(lines), )
        else:
            paragraphs, wrap_up = ParagraphParser.extract_multiple_from_text(lines)
            if wrap_up is not None:
                raise ValueError("Junk detected in Article after last Paragraph")

        return Article(identifier, tuple(p for p in paragraphs if isinstance(p, Paragraph)), title)


ActBodyParserType = Union[StructuralElementParser, ArticleStructuralParser]
ActBodyParsersType = Iterable[ActBodyParserType]


class ActBodyParser:
    """ Parse Act and BlockAmendment body """
    @classmethod
    def get_parser_for_header_line(cls, line: IndentedLine, previous_line: IndentedLine, parsers: ActBodyParsersType) \
            -> Optional[ActBodyParserType]:
        for p in parsers:
            if p.is_header(line, previous_line):
                return p
        return None

    @classmethod
    def parse_elements(cls, parsers: ActBodyParsersType, lines: Sequence[IndentedLine]) -> Iterable[ActChildType]:
        elements = []
        current_lines = []
        current_element_parser = None
        previous_line = EMPTY_LINE
        for quote_level, line in iterate_with_quote_level(lines):
            if quote_level != 0:
                current_lines.append(line)
                continue
            new_header_parser = cls.get_parser_for_header_line(line, previous_line, parsers)
            previous_line = line
            if new_header_parser is None:
                current_lines.append(line)
                continue
            if current_element_parser is not None:
                elements.append(current_element_parser.parse(current_lines))
            current_element_parser = new_header_parser
            current_lines = [line]
            current_element_parser.step_to_next_number(current_lines[0])
        assert current_element_parser is not None
        elements.append(current_element_parser.parse(current_lines))
        return elements


class ActParsingError(StructureParsingError):
    pass


class ActStructureParser:
    PARSED_TYPE = Act

    @classmethod
    def parse(cls, identifier: str, subject: str, lines: Sequence[IndentedLine]) -> Act:
        try:
            parsers = cls.create_parsers()
            preamble, lines = cls.parse_preamble(parsers, lines)
            elements = ActBodyParser.parse_elements(parsers, lines)
        except Exception as e:
            raise ActParsingError("Error during parsing body: {}".format(e), Act, identifier) from e

        return Act(identifier, subject, preamble, tuple(elements))

    @classmethod
    def create_parsers(cls) -> ActBodyParsersType:
        return [parser() for parser in STRUCTURE_ELEMENT_PARSERS]

    @classmethod
    def parse_preamble(cls, parsers: ActBodyParsersType, lines: Sequence[IndentedLine]) -> Tuple[str, Sequence[IndentedLine]]:
        parsers = cls.create_parsers()
        split_point = len(lines)

        previous_line = EMPTY_LINE
        # No quote parsing, because we REALLY hope preambles don't
        # contain quoted article or strucutral headers.
        for line_number, line in enumerate(lines):
            if ActBodyParser.get_parser_for_header_line(line, previous_line, parsers) is not None:
                split_point = line_number
                break
            previous_line = line
        preamble = " ".join(l.content for l in lines[:split_point] if l != EMPTY_LINE)
        rest_of_lines = lines[split_point:]
        return preamble, rest_of_lines


class BlockAmendmentStructureParsingError(StructureParsingError):
    pass


class BlockAmendmentStructureParser:
    PARSERS_FOR_TYPE: Mapping[Type, Type[Union[ArticleParser, SubArticleElementParser]]] = {
        Article: ArticleParser,
        Paragraph: ParagraphParser,
        AlphabeticPoint: AlphabeticPointParser,
        NumericPoint: NumericPointParser,
        AlphabeticSubpoint: AlphabeticSubpointParser,  # In the default case at least
        NumericSubpoint: NumericSubpointParser,
    }

    @classmethod
    def parse(
            cls,
            metadata: BlockAmendmentMetadata,
            context_intro: Optional[str],
            context_wrap_up: Optional[str],
            lines: Sequence[IndentedLine]
    ) -> BlockAmendment:

        try:
            children: Tuple[SubArticleChildType, ...]
            if issubclass(metadata.expected_type, StructuralElement):
                parsers = cls.create_parsers()
                children = tuple(ActBodyParser.parse_elements(parsers, lines))
            else:
                parser, expected_id = cls.get_parser_and_id(metadata)
                children = tuple(cls.do_parse_block_by_block(parser, expected_id, lines))

            return BlockAmendment(
                identifier=None,
                text=None,
                intro=context_intro,
                children=children,
                wrap_up=context_wrap_up
            )
        except Exception as e:
            raise BlockAmendmentStructureParsingError("Error parsing block amendment body. Metadata: {}".format(metadata)) from e

    @classmethod
    def create_parsers(cls) -> ActBodyParsersType:
        return [parser(strict=False) for parser in STRUCTURE_ELEMENT_PARSERS]

    @classmethod
    def do_parse_block_by_block(cls, parser: Type[Union[ArticleParser, SubArticleElementParser]], expected_id: str, lines: Sequence[IndentedLine]) -> Iterable[SubArticleChildType]:
        current_lines: List[IndentedLine] = []
        last_identifier = expected_id
        for quote_level, line in iterate_with_quote_level(lines):
            extracted_identifier = parser.extract_identifier(line)
            header_found = (
                current_lines and
                quote_level == 0 and
                extracted_identifier is not None and
                parser.PARSED_TYPE.is_next_identifier(last_identifier, extracted_identifier)
            )
            if header_found:
                yield parser.parse(current_lines)
                assert extracted_identifier is not None
                last_identifier = extracted_identifier
                current_lines = []
            current_lines.append(line)
        yield parser.parse(current_lines)

    @classmethod
    def get_parser_and_id(cls, metadata: BlockAmendmentMetadata) -> Tuple[Type[Union[ArticleParser, SubArticleElementParser]], str]:
        structural_type = metadata.expected_type
        assert metadata.expected_id_range is not None
        expected_id = metadata.expected_id_range[0]
        if structural_type is AlphabeticSubpoint and len(expected_id) != 1:
            # TODO: let's hope it is not a two-letter subpoint like "ny"
            return get_prefixed_alphabetic_subpoint_parser(expected_id[:-1]), expected_id
        return cls.PARSERS_FOR_TYPE[structural_type], expected_id


def similar_indent(a: float, b: float) -> bool:
    # Super scientific
    return abs(a - b) < 1
