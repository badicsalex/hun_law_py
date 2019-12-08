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

import re
import attr

from hun_law.structure import Article, QuotedBlock, BlockAmendment, OutgoingReference, BlockAmendmentMetadata
from .structure_parser import BlockAmendmentStructureParser, SubArticleParsingError
from .grammatical_analyzer import GrammaticalAnalyzer


@attr.s(slots=True)
class SemanticParseState:
    analyzer = attr.ib(factory=GrammaticalAnalyzer)
    act_id_abbreviations = attr.ib(factory=list)
    outgoing_references = attr.ib(factory=list)


class ActSemanticsParser:
    INTERESTING_SUBSTRINGS = (")", "§", "törvén")

    @classmethod
    def parse(cls, act):
        # TODO: Rewrite this to be more functional instead of passing
        # a mutable state
        state = SemanticParseState()
        for article in act.articles:
            for paragraph in article.paragraphs:
                cls.recursive_parse(paragraph, article.relative_reference, "", "", state)
        return attr.evolve(
            act,
            act_id_abbreviations=state.act_id_abbreviations,
            outgoing_references=state.outgoing_references
        )

    @classmethod
    def recursive_parse(cls, element, parent_reference, prefix, postfix, state):
        if type(element) in (QuotedBlock, BlockAmendment):
            return
        element_reference = element.relative_reference.relative_to(parent_reference)
        if element.text is not None:
            cls.parse_text(element.text, prefix, postfix, element_reference, state)
            return

        # First parse the intro of this element, because although we will
        # parse the same text when in context of the children, we throw away
        # the intro part of the result there.

        # TODO: Not using the children and postfix here is a huge hack. This code is reached for
        # Points and SubPoints, so most of the time these are partial sentences,
        # e.g
        # From now on
        #     a) things will change
        #     b) everything will be better.
        #
        # In this case, we hope that the string "From now on" can be parsed without
        # the second part of the sentence.
        cls.parse_text(element.intro, prefix, '', element_reference, state)

        # TODO: Parse the wrap up of "this element"

        if element.intro is not None:
            prefix = prefix + element.intro + " "

        postfix = postfix
        if element.wrap_up is not None:
            postfix = " " + element.wrap_up + postfix

        for child in element.children:
            cls.recursive_parse(child, element_reference, prefix, postfix, state)

    @classmethod
    def parse_text(cls, middle, prefix, postfix, element_reference, state):
        text = prefix + middle + postfix
        if len(text) > 10000:
            return None
        if not any(s in text for s in cls.INTERESTING_SUBSTRINGS):
            return None

        analysis_result = state.analyzer.analyze(text)

        state.act_id_abbreviations.extend(analysis_result.act_id_abbreviations)

        state.outgoing_references.extend(cls.convert_parsed_references(
            analysis_result.all_references,
            element_reference,
            len(prefix), len(text) - len(postfix),
            state
        ))
        # TODO: parse block amendments, and return interesting results
        return None

    @classmethod
    def convert_parsed_references(cls, parsed_references, element_reference, prefixlen, textlen, state):
        result = []
        abbreviations_map = {a.abbreviation: a.act for a in state.act_id_abbreviations}
        for in_text_reference in parsed_references:
            # The end of the parsed reference is inside the target string
            # Checking for the end and not the beginning is important, because
            # we also want partial references to work here.
            if in_text_reference.end_pos <= prefixlen or in_text_reference.end_pos > textlen:
                continue

            # Try to resolve abbreviations
            # TODO: We have no way of determining whether the Act ID is an
            # abbreviation or not right now.
            to_reference = in_text_reference.reference
            if to_reference.act is not None:
                if to_reference.act in abbreviations_map:
                    to_reference = attr.evolve(to_reference, act=abbreviations_map[to_reference.act])

            result.append(
                OutgoingReference(
                    from_reference=element_reference,
                    start_pos=max(in_text_reference.start_pos - prefixlen, 0),
                    end_pos=(in_text_reference.end_pos - prefixlen),
                    to_reference=to_reference
                )
            )
        result.sort()
        return result


class ActBlockAmendmentParser:
    @classmethod
    def parse(cls, act):
        new_children = []
        for child in act.children:
            if isinstance(child, Article):
                child = cls.parse_article(child)
            new_children.append(child)
        return attr.evolve(act, children=new_children)

    @classmethod
    def parse_article(cls, article):
        new_children = []
        for paragraph in article.paragraphs:
            new_children.append(cls.parse_paragraph(paragraph))
        return attr.evolve(article, children=new_children)

    @classmethod
    def parse_paragraph(cls, paragraph):
        if paragraph.children_type != QuotedBlock:
            return paragraph
        if len(paragraph.intro) > 10000:
            return paragraph
        # TODO: We don't currently parse structural amendments properly in the
        # structural step.
        # Block amendements have a two-part intro, which we unfortunately merge:
        #    Az Eurt.tv. 9. § (5) bekezdés c) pontja helyébe a következő rendelkezés lép:
        #   (Nem minősül függetlennek az igazgatótanács tagja különösen akkor, ha)
        #   „c) a társaság olyan részvényese, aki közvetve vagy közvetlenül a leadható szavazatok...
        #
        # Also, its sometimes bracketed with [] instead of ()

        matches = re.match(r"^(.*:) ?(\([^\)]*\)|\[[^\]]*\])$", paragraph.intro)
        context_intro = None
        context_outro = None
        if matches is None:
            actual_intro = paragraph.intro
        else:
            actual_intro = matches.group(1)
            context_intro = matches.group(2)[1:-1]
            if paragraph.wrap_up is not None:
                context_outro = paragraph.wrap_up[1:-1]

        # TODO: Maybe cache?
        analysis_result = GrammaticalAnalyzer().analyze(actual_intro).special_expression
        if not isinstance(analysis_result, BlockAmendmentMetadata):
            return paragraph

        assert len(paragraph.children) == 1

        try:
            starting_reference = analysis_result.amended_reference
            if starting_reference is None:
                starting_reference = analysis_result.inserted_reference
            assert starting_reference is not None

            block_amendment = BlockAmendmentStructureParser.parse(
                starting_reference,
                context_intro, context_outro,
                paragraph.quoted_block(0).lines
            )
        except SubArticleParsingError:
            # TODO: There are many unhandled cases right now, but don't stop
            # parsing just because this. Leave the whole thing as a QuotedLines
            # for now
            return paragraph
        return attr.evolve(paragraph, intro=actual_intro, wrap_up="", children=(block_amendment,))
