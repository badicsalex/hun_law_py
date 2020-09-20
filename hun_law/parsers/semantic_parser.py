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
from typing import List, Iterable, Tuple, Mapping

import attr

from hun_law.structure import \
    Act, Article, Paragraph, QuotedBlock, SemanticData, \
    OutgoingReference, \
    BlockAmendmentMetadata, \
    ActIdAbbreviation, SubArticleElement
from .structure_parser import BlockAmendmentStructureParser, SubArticleParsingError
from .grammatical_analyzer import GrammaticalAnalyzer


@attr.s(slots=True)
class SemanticParseState:
    analyzer: GrammaticalAnalyzer = attr.ib(factory=GrammaticalAnalyzer)
    act_id_abbreviations: List[ActIdAbbreviation] = attr.ib(factory=list)


class ActSemanticsParser:
    INTERESTING_SUBSTRINGS = (")", "§", "törvén")

    @classmethod
    def add_semantics_to_act(cls, act: Act) -> Act:
        # TODO: Rewrite this to be more functional instead of passing
        # a mutable state
        state = SemanticParseState()
        new_children = []
        for child in act.children:
            if isinstance(child, Article):
                child = cls.add_semantics_to_article(child, state)
            new_children.append(child)
        return attr.evolve(
            act,
            children=tuple(new_children),
            act_id_abbreviations=tuple(state.act_id_abbreviations)
        )

    @classmethod
    def add_semantics_to_article(cls, article: Article, state: SemanticParseState) -> Article:
        new_children = tuple(cls.add_semantics_to_sae(child, '', '', state) for child in article.children)
        return attr.evolve(
            article,
            children=new_children
        )

    @classmethod
    def add_semantics_to_sae(
            cls,
            element: SubArticleElement,
            prefix: str, postfix: str,
            state: SemanticParseState
    ) -> SubArticleElement:
        if element.text is not None:
            outgoing_references, semantic_data = cls.parse_text(element.text, prefix, postfix, state)
            return attr.evolve(
                element,
                outgoing_references=outgoing_references,
                semantic_data=semantic_data
            )

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
        if element.intro is not None:
            outgoing_references, semantic_data = cls.parse_text(element.intro, prefix, '', state)
        else:
            outgoing_references, semantic_data = (), ()

        # TODO: Parse the wrap up of "this element"

        if element.intro is not None:
            prefix = prefix + element.intro + " "

        if element.wrap_up is not None:
            postfix = " " + element.wrap_up + postfix

        assert element.children is not None
        new_children = []
        for child in element.children:
            if isinstance(child, SubArticleElement):
                child = cls.add_semantics_to_sae(child, prefix, postfix, state)
            new_children.append(child)

        return attr.evolve(
            element,
            children=tuple(new_children),
            outgoing_references=outgoing_references,
            semantic_data=semantic_data
        )

    @classmethod
    def fix_list_element_end(cls, text: str, end_sentence: bool) -> str:
        # The order here matters, so as to handle the ", és"-style cases
        for junk_str in (" és", " valamint", " illetve", " vagy", ";", ","):
            if text.endswith(junk_str):
                text = text[:-len(junk_str)]
        if end_sentence and text[-1] not in ('.', ':', '!', '?'):
            text = text + '.'
        return text

    @classmethod
    def parse_text(cls, middle: str, prefix: str, postfix: str, state: SemanticParseState) \
            -> Tuple[Tuple[OutgoingReference, ...], Tuple[SemanticData, ...]]:

        middle = cls.fix_list_element_end(middle, not postfix)
        text = prefix + middle + postfix
        if len(text) > 10000:
            return (), ()
        if not any(s in text for s in cls.INTERESTING_SUBSTRINGS):
            return (), ()

        analysis_result = state.analyzer.analyze(text)

        state.act_id_abbreviations.extend(analysis_result.act_id_abbreviations)

        abbreviations_map = {a.abbreviation: a.act for a in state.act_id_abbreviations}

        outgoing_references = cls.convert_parsed_references(
            analysis_result.all_references,
            len(prefix), len(text) - len(postfix),
            abbreviations_map,
        )

        semantic_data = tuple(s.resolve_abbreviations(abbreviations_map) for s in analysis_result.semantic_data)
        return outgoing_references, semantic_data

    @classmethod
    def convert_parsed_references(
            cls,
            parsed_references: Iterable[OutgoingReference],
            prefixlen: int,
            textlen: int,
            abbreviations_map: Mapping[str, str],
    ) -> Tuple[OutgoingReference, ...]:
        # TODO: pylint is right here, should refactor.
        # pylint: disable=too-many-arguments
        result = []
        for in_text_reference in parsed_references:
            # The end of the parsed reference is inside the target string
            # Checking for the end and not the beginning is important, because
            # we also want partial references to work here.
            if in_text_reference.end_pos <= prefixlen or in_text_reference.end_pos > textlen:
                continue

            result.append(
                OutgoingReference(
                    start_pos=max(in_text_reference.start_pos - prefixlen, 0),
                    end_pos=(in_text_reference.end_pos - prefixlen),
                    reference=in_text_reference.reference.resolve_abbreviations(abbreviations_map)
                )
            )
        result.sort()
        return tuple(result)


class ActBlockAmendmentParser:
    @classmethod
    def parse(cls, act: Act) -> Act:
        new_children = []
        for child in act.children:
            if isinstance(child, Article):
                child = cls.parse_article(child)
            new_children.append(child)
        return attr.evolve(act, children=tuple(new_children))

    @classmethod
    def parse_article(cls, article: Article) -> Article:
        new_children = []
        for paragraph in article.paragraphs:
            new_children.append(cls.parse_paragraph(paragraph))
        return attr.evolve(article, children=tuple(new_children))

    @classmethod
    def parse_paragraph(cls, paragraph: Paragraph) -> Paragraph:
        if paragraph.children_type != QuotedBlock:
            return paragraph
        assert paragraph.children is not None
        assert paragraph.intro is not None
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

        matches = re.match(r"^(.*:) ?(\(.*\)|\[.*\])$", paragraph.intro)
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
        semantic_data = GrammaticalAnalyzer().analyze(actual_intro).semantic_data
        for semantic_data_element in semantic_data:
            if isinstance(semantic_data_element, BlockAmendmentMetadata):
                block_amendment_metadata = semantic_data_element
                break
        else:  # no break: no BlockAmendmentMetadata found
            return paragraph

        assert len(paragraph.children) == 1

        try:
            block_amendment = BlockAmendmentStructureParser.parse(
                block_amendment_metadata,
                context_intro, context_outro,
                paragraph.quoted_block(0).lines
            )
        except SubArticleParsingError:
            # TODO: There are many unhandled cases right now, but don't stop
            # parsing just because this. Leave the whole thing as a QuotedLines
            # for now
            return paragraph
        return attr.evolve(paragraph, intro=actual_intro, wrap_up="", children=(block_amendment,))
