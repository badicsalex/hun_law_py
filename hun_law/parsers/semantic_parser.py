# Copyright 2019 Alex Badics <admin@stickman.hu>
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

from collections import namedtuple

from hun_law.structure import QuotedBlock, Act, Article, OutgoingReference
from .grammatical_analyzer import GrammaticalAnalyzer, GrammaticalAnalysisType


class SemanticActParser:
    ParseResult = namedtuple("ParseResult", ("outgoing_references", ))
    EMPTY_PARSE_RESULT = ParseResult(None)

    INTERESTING_SUBSTRINGS = (")", "§", "törvén")

    @classmethod
    def parse(cls, act):
        abbreviations = []
        new_children = tuple(cls.parse_act_child(child, abbreviations) for child in act.children)
        return Act(act.identifier, act.subject, act.preamble, new_children)

    @classmethod
    def parse_act_child(cls, child, abbreviations):
        if isinstance(child, Article):
            return cls.parse_article(child, abbreviations)
        return child

    @classmethod
    def parse_article(cls, article, abbreviations):
        new_article_children = tuple(
            cls.parse_element(paragraph, "", "", abbreviations) for paragraph in article.children
        )
        return Article(article.identifier, article.title, new_article_children)

    @classmethod
    def parse_element(cls, element, prefix, postfix, abbreviations):
        if element.text is not None:
            parse_result = cls.parse_text(element.text, prefix, postfix, GrammaticalAnalysisType.SIMPLE, abbreviations)
            return cls.enhanced_element(element, outgoing_references=parse_result.outgoing_references)
        else:
            if element.children_type == QuotedBlock:
                # QuotedBlocks can only appear within Paragraphs, which are always children of
                # Articles, which never have intros.
                assert prefix == ''
                text = element.intro
                parse_result = cls.parse_text(text, '', '', GrammaticalAnalysisType.SIMPLE, abbreviations)
                return cls.enhanced_element(element, outgoing_references=parse_result.outgoing_references)
            else:
                return cls.parse_element_with_children(element, prefix, postfix, abbreviations)

    @classmethod
    def parse_element_with_children(cls, element, prefix, postfix, abbreviations):
        # TODO: Not using the children and postfix here is a huge hack. This code is reached for
        # Points and SubPoints, so most of the time these are partial sentences,
        # e.g
        # From now on
        #     a) things will change
        #     b) everything will be better.
        #
        # In this case, we hope that the string "From now on" can be parsed without
        # the second part of the sentence.
        parse_result = cls.parse_text(element.intro, prefix, '', GrammaticalAnalysisType.SIMPLE, abbreviations)

        children_prefix = prefix
        if element.intro is not None:
            children_prefix = children_prefix + element.intro + " "

        children_postfix = postfix
        if element.wrap_up is not None:
            children_postfix = " " + element.wrap_up + children_postfix

        new_children = tuple(
            cls.parse_element(
                child,
                children_prefix,
                children_postfix,
                abbreviations
            ) for child in element.children
        )

        return cls.enhanced_element(element, outgoing_references=parse_result.outgoing_references, new_children=new_children)

    @classmethod
    def parse_text(cls, middle, prefix, postfix, analysis_type, abbreviations):
        text = prefix + middle + postfix
        if len(text) > 10000:
            return cls.EMPTY_PARSE_RESULT
        if not any(s in text for s in cls.INTERESTING_SUBSTRINGS):
            return cls.EMPTY_PARSE_RESULT

        analysis_result = GrammaticalAnalyzer().analyze(text, analysis_type)
        abbreviations.extend(analysis_result.get_new_abbreviations())

        return cls.ParseResult(
            cls.convert_parsed_references(
                analysis_result.get_references(abbreviations),
                len(prefix), len(text) - len(postfix)
            ),
        )

    @classmethod
    def convert_parsed_references(cls, parsed_references, prefixlen, textlen):
        result = []
        for outgoing_reference in parsed_references:
            # The end of the parsed reference is inside the target string
            # Checking for the end and not the beginning is important, because
            # we also want partial references to work here.
            if outgoing_reference.end_pos > prefixlen and outgoing_reference.end_pos <= textlen:
                result.append(
                    OutgoingReference(
                        max(outgoing_reference.start_pos - prefixlen, 0),
                        outgoing_reference.end_pos - prefixlen,
                        outgoing_reference.reference
                    )
                )
        result.sort()
        return tuple(result)

    @classmethod
    def enhanced_element(cls, element, *, outgoing_references=None, new_children=None):
        return element.__class__(
            element.identifier,
            element.text,
            element.intro,
            element.children if new_children is None else new_children,
            element.wrap_up,
            outgoing_references
        )
