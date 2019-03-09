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

from hun_law.structure import Reference, ActSemanticData, QuotedBlock, InTextSemanticData
from .grammatical_analyzer import GrammaticalAnalyzer


class ActSemanticDataParser:
    INTERESTING_SUBSTRINGS = (")", "§", "törvén")

    def __init__(self):
        self.grammatical_analyzer = GrammaticalAnalyzer()

    def parse(self, act):
        result = {}
        abbreviations = []
        for article in act.articles:
            for paragraph in article.paragraphs:
                parse_result = self.parse_sub_article_element(
                    paragraph,
                    "",
                    "",
                    Reference(article=article.identifier),
                    abbreviations
                )
                for reference, itsd in parse_result:
                    result[reference] = itsd
        return ActSemanticData(result)

    def parse_sub_article_element(self, sub_article_element, prefix, postfix, parent_ref, abbreviations):
        current_ref = sub_article_element.relative_reference.relative_to(parent_ref)
        if sub_article_element.text is not None:
            parse_result = self.parse_text(sub_article_element.text, prefix, postfix, current_ref, abbreviations)
            if parse_result:
                yield current_ref, parse_result
        else:
            if sub_article_element.children_type == QuotedBlock:
                # QuotedBlocks can only appear within Paragraphs, which are always children of
                # Articles, which never have intros.
                assert prefix == ''
                text = sub_article_element.intro
                parse_result = self.parse_text(text, '', '', current_ref, abbreviations)
                if parse_result:
                    yield current_ref, parse_result
            else:
                # TODO: Not using the children and postfix here is a huge hack. This code is reached for
                # Points and SubPoints, so most of the time these are partial sentences,
                # e.g
                # From now on
                #     a) things will change
                #     b) everything will be better.
                #
                # In this case, we hope that the string "From now on" can be parsed without
                # the second part of the sentence.
                parse_result = self.parse_text(sub_article_element.intro, prefix, '', current_ref, abbreviations)
                if parse_result:
                    yield current_ref, parse_result

                children_prefix = prefix
                if sub_article_element.intro is not None:
                    children_prefix = children_prefix + sub_article_element.intro + " "

                children_postfix = postfix
                if sub_article_element.wrap_up is not None:
                    children_postfix = " " + sub_article_element.wrap_up + children_postfix

                for child in sub_article_element.children:
                    yield from self.parse_sub_article_element(
                        child,
                        children_prefix,
                        children_postfix,
                        current_ref,
                        abbreviations
                    )

    def parse_text(self, middle, prefix, postfix, current_ref, abbreviations):
        text = prefix + middle + postfix
        if len(text) > 10000:
            return
        if not any(s in text for s in self.INTERESTING_SUBSTRINGS):
            return

        analysis_result = self.grammatical_analyzer.analyze_simple(text)
        abbreviations.extend(analysis_result.get_new_abbreviations())

        result = []
        for itsd in analysis_result.get_references(abbreviations):
            # The end of the parsed reference is inside the target string
            # Checking for the end and not the beginning is important, because
            # we also want partial references to work here.
            if itsd.end_pos > len(prefix) and itsd.end_pos <= len(text) - len(postfix):
                if itsd.data.is_relative():
                    absolute_ref = itsd.data.relative_to(current_ref)
                else:
                    absolute_ref = itsd.data
                result.append(
                    InTextSemanticData(
                        max(itsd.start_pos - len(prefix), 0),
                        itsd.end_pos - len(prefix),
                        absolute_ref
                    )
                )
        result.sort()
        return tuple(result)
