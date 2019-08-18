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

import attr
from collections import namedtuple

from hun_law.structure import QuotedBlock, OutgoingReference
from .grammatical_analyzer import GrammaticalAnalyzer, GrammaticalAnalysisType


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
        if isinstance(element, QuotedBlock):
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

        # TODO: Parse the outro of "this element"

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

        analysis_result = state.analyzer.analyze(text, GrammaticalAnalysisType.SIMPLE)

        state.act_id_abbreviations.extend(analysis_result.get_new_abbreviations())

        state.outgoing_references.extend(cls.convert_parsed_references(
            analysis_result.get_references(state.act_id_abbreviations),
            element_reference,
            len(prefix), len(text) - len(postfix)
        ))
        # TODO: parse block amendments, and return interesting results
        return None

    @classmethod
    def convert_parsed_references(cls, parsed_references, element_reference, prefixlen, textlen):
        result = []
        for in_text_reference in parsed_references:
            # The end of the parsed reference is inside the target string
            # Checking for the end and not the beginning is important, because
            # we also want partial references to work here.
            if in_text_reference.end_pos > prefixlen and in_text_reference.end_pos <= textlen:
                result.append(
                    OutgoingReference(
                        from_reference=element_reference,
                        start_pos=max(in_text_reference.start_pos - prefixlen, 0),
                        end_pos=(in_text_reference.end_pos - prefixlen),
                        to_reference=in_text_reference.reference
                    )
                )
        result.sort()
        return result
