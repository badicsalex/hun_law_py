# Copyright 2018-2019 Alex Badics <admin@stickman.hu>
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
import os
import collections
import tatsu
import tatsu.model
from enum import Enum

from .grammar import model
from .grammar.parser import ActGrammarParser

from hun_law.structure import Reference, ActIdAbbreviation, InTextReference, BlockAmendmentMetadata


def iterate_depth_first(node, filter_class=None):
    if isinstance(node, tatsu.model.Node):
        to_iter = node.ast
    else:
        to_iter = node
    if isinstance(to_iter, dict):
        for k, v in to_iter.items():
            if k == 'parseinfo':
                continue
            yield from iterate_depth_first(v, filter_class)
    elif isinstance(to_iter, list):
        for v in to_iter:
            yield from iterate_depth_first(v, filter_class)
    if filter_class is None or isinstance(node, filter_class):
        yield node


class ReferenceCollector:
    def __init__(self):
        self.act = None
        self.articles = [(None, 0, 0)]
        self.paragraphs = [(None, 0, 0)]
        self.points = [(None, 0, 0)]
        self.alphabeticpoints = self.points  # alias
        self.numericpoints = self.points  # alias
        self.subpoints = [(None, 0, 0)]
        self.alphabeticsubpoints = self.subpoints  # alias
        self.numericsubpoints = self.subpoints  # alias

    def add_item(self, ref_type, ref_data, start_pos, end_pos):
        ref_list = getattr(self, ref_type + 's')
        if ref_list[0][0] is None:
            ref_list[0] = (ref_data, start_pos, end_pos)
        else:
            ref_list.append((ref_data, start_pos, end_pos))

    def iter(self, start_override, end_override):
        ref_args = [self.act, None, None, None, None]
        levels = ("articles", "paragraphs", "points", "subpoints")
        last_end = 0
        for arg_pos, level in enumerate(levels, start=1):
            level_vals = getattr(self, level)
            if len(level_vals) == 1:
                ref_args[arg_pos] = level_vals[0][0]
            else:
                level_vals.sort(key=lambda x: x[1])
                for level_val, start, end in level_vals[:-1]:
                    if start_override is not None:
                        start = start_override
                        start_override = None
                    ref_args[arg_pos] = level_val
                    yield InTextReference(start, end, Reference(*ref_args))
                ref_args[arg_pos] = level_vals[-1][0]
            if start_override is None:
                start_override = level_vals[-1][1]
        yield InTextReference(start_override, end_override, Reference(*ref_args))


@attr.s(slots=True, frozen=True)
class GrammaticalAnalysisResult:
    tree = attr.ib()

    act_references = attr.ib(init=False)
    element_references = attr.ib(init=False)
    act_id_abbreviations = attr.ib(init=False)
    special_expression = attr.ib(init=False)

    @property
    def all_references(self):
        return self.act_references + self.element_references

    @element_references.default
    def _element_references_default(self):
        refs_to_parse = []
        refs_found = set()
        # Collect references where we might have Act Id
        for ref_container in iterate_depth_first(self.tree, model.CompoundReference):
            if not ref_container.references:
                continue
            act_id = None
            if ref_container.act_reference is not None:
                act_id = self._get_act_id_from_parse_result(ref_container.act_reference)
            for reference in ref_container.references:
                refs_to_parse.append((act_id, reference))
                refs_found.add(reference)

        # Collect all other refs scattered elsewhere
        for ref in iterate_depth_first(self.tree, model.Reference):
            if ref in refs_found:
                continue
            refs_to_parse.append((None, ref))

        result = []
        for act_id, parsed_ref in refs_to_parse:
            result.extend(self._convert_single_reference(act_id, parsed_ref))
        return tuple(result)

    @classmethod
    def _convert_single_reference(cls, act_id, parsed_ref):
        reference_collector = ReferenceCollector()
        if act_id is not None:
            reference_collector.act = act_id

        cls._fill_reference_collector(parsed_ref, reference_collector)
        full_start_pos, full_end_pos = cls._get_subtree_start_and_end_pos(parsed_ref)
        yield from reference_collector.iter(full_start_pos, full_end_pos)

    @classmethod
    def _fill_reference_collector(cls, parsed_ref, reference_collector):
        assert isinstance(parsed_ref, model.Reference), parsed_ref
        for ref_part in parsed_ref.children():
            assert isinstance(ref_part, model.ReferencePart), ref_part
            ref_type_name = ref_part.__class__.__name__[:-len('ReferencePart')].lower()
            for ref_list_item in ref_part.singles:
                start_pos, end_pos = cls._get_subtree_start_and_end_pos(ref_list_item)
                id_as_string = "".join(ref_list_item.id.id)
                reference_collector.add_item(ref_type_name, id_as_string, start_pos, end_pos)
            for ref_list_item in ref_part.ranges:
                start_pos, end_pos = cls._get_subtree_start_and_end_pos(ref_list_item)
                start_id_as_string = "".join(ref_list_item.start.id)
                end_id_as_string = "".join(ref_list_item.end.id)
                reference_collector.add_item(ref_type_name, (start_id_as_string, end_id_as_string), start_pos, end_pos)

    @act_references.default
    def _act_references_default(self):
        result = []
        for act_ref in iterate_depth_first(self.tree, model.ActReference):
            if act_ref.abbreviation is not None:
                start_pos, end_pos = self._get_subtree_start_and_end_pos(act_ref.abbreviation)
            elif act_ref.act_id is not None:
                start_pos, end_pos = self._get_subtree_start_and_end_pos(act_ref.act_id)
            else:
                raise ValueError('Neither abbreviation, nor act_id in act_ref')
            act_str = self._get_act_id_from_parse_result(act_ref)
            result.append(
                InTextReference(
                    start_pos, end_pos,
                    Reference(act=act_str)
                )
            )
        return tuple(result)

    @classmethod
    def _get_act_id_from_parse_result(cls, act_ref):
        if act_ref.act_id is not None:
            return "{}. évi {}. törvény".format(act_ref.act_id.year, act_ref.act_id.number)
        if act_ref.abbreviation is not None:
            return act_ref.abbreviation.s
        raise ValueError('Neither abbreviation, nor act_id in act_ref')

    @classmethod
    def _get_subtree_start_and_end_pos(cls, subtree):
        return subtree.parseinfo.pos, subtree.parseinfo.endpos

    @act_id_abbreviations.default
    def _act_id_abbreviations_default(self):
        result = []
        for act_ref in iterate_depth_first(self.tree, model.ActReference):
            if act_ref.from_now_on is None:
                continue
            result.append(
                ActIdAbbreviation(
                    str(act_ref.from_now_on.abbreviation.s),
                    self._get_act_id_from_parse_result(act_ref)
                )
            )
        return tuple(result)

    @special_expression.default
    def _special_expression_default(self):
        if isinstance(self.tree, model.BlockAmendment):
            return self._convert_block_amendment()
        return None

    def _convert_block_amendment(self):
        if not isinstance(self.tree, model.BlockAmendment):
            return None
        amendment_position = self.tree.amendment_position
        act_id = self._get_act_id_from_parse_result(amendment_position.act_reference)

        # "References" can only be a tuple, if there are multiple reference types
        # in the single compound reference, i.e. an article reference and an
        # article + paragraph reference (see grammar analysis tests for examples)
        # This cannot happen with Block Amendments, so check for this case
        # TODO: We may catch this in grammar phase by not using CompoundReference,
        # but then ref collecting in _element_references_default needs to be updated
        if len(amendment_position.references) != 1:
            # Don't fail horribly in this case, just report that this as not a block amendment.
            # Same as failing in grammar phase.
            return None


        amended_references = tuple(r.reference for r in self._convert_single_reference(act_id, amendment_position.references[0]))
        # Block amendments may only be contigous ranges, not lists.
        # TODO: contigous pairs are usually not noted as a range, but as a list of the
        # two ids with "és", but they should be parsed as ranges, really. Or converted
        # here the latest.
        if len(amended_references) != 1:
            # Don't fail horribly in this case, just report that this as not a block amendment.
            # Same as failing in grammar phase.
            return None

        return BlockAmendmentMetadata(
            amended_reference=amended_references[0]
        )

    @classmethod
    def _indented_print(cls, node=None, indent=''):
        if isinstance(node, tatsu.model.Node):
            print('<Node:{}>'.format(node.__class__.__name__), end='')
            node = node.ast
        if isinstance(node, dict):
            print('<Dict>')
            for k, v in node.items():
                if k == 'parseinfo':
                    continue
                print("{}  {}: ".format(indent, k), end='')
                cls._indented_print(v, indent + '    ')
        elif isinstance(node, list):
            print('<List>')
            for v in node:
                print("{}  - ".format(indent), end='')
                cls._indented_print(v, indent + '    ')
        else:
            print(node)

    def indented_print(self, indent=''):
        self._indented_print(self.tree, indent)


class GrammaticalAnalyzer:
    def __init__(self):
        self.parser = ActGrammarParser(
            semantics=model.ActGrammarModelBuilderSemantics(),
            parseinfo=True
        )

    def analyze(self, s, *, debug=False):
        parse_result = self.parser.parse(
            s,
            rule_name='start_default',
            trace=debug, colorize=debug,
        )
        return GrammaticalAnalysisResult(parse_result)
