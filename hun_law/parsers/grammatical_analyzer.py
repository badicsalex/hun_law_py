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

from typing import Dict, Union, List, Type, Any, Optional, Iterable, Tuple

import attr
import tatsu
import tatsu.model

from hun_law.structure import Reference, ActIdAbbreviation, InTextReference, BlockAmendmentMetadata, \
    Article, Paragraph, AlphabeticPoint, NumericPoint, AlphabeticSubpoint, \
    SubArticleElement, \
    ReferencePartType

from .grammar import model
from .grammar.parser import ActGrammarParser  # type: ignore


def iterate_depth_first(node: Any, filter_class: Optional[Type] = None) -> Iterable[Any]:
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


@attr.s(slots=True, auto_attribs=True)
class ReferenceCollectorDeferredItem:
    ref_type: str
    ref_data: ReferencePartType
    start_pos: int
    end_pos: int


class ReferenceCollector:
    NAME_TO_STRUCTURE: Dict[str, Type[Union[SubArticleElement, Article]]] = {
        'article': Article,
        'paragraph': Paragraph,
        'alphabeticpoint': AlphabeticPoint,
        'numericpoint': NumericPoint,
        'alphabeticsubpoint': AlphabeticSubpoint,
    }

    def __init__(self) -> None:
        self.act: Optional[str] = None
        self.articles = [(None, 0, 0)]
        self.paragraphs = [(None, 0, 0)]
        self.points = [(None, 0, 0)]
        self.alphabeticpoints = self.points  # alias
        self.numericpoints = self.points  # alias
        self.subpoints = [(None, 0, 0)]
        self.alphabeticsubpoints = self.subpoints  # alias
        self.numericsubpoints = self.subpoints  # alias
        self.deferred_item: Optional[ReferenceCollectorDeferredItem] = None

    def add_item(self, ref_type: str, ref_data: ReferencePartType, start_pos: int, end_pos: int) -> None:
        if self.mergeable_into_deferred(ref_type, ref_data):
            assert isinstance(ref_data, str)
            self.merge_to_deferred(ref_data, end_pos)
            self.commit_deferred_item()
        else:
            self.commit_deferred_item()
            self.deferred_item = ReferenceCollectorDeferredItem(ref_type, ref_data, start_pos, end_pos)

    def mergeable_into_deferred(self, ref_type: str, ref_data: ReferencePartType) -> bool:
        if self.deferred_item is None:
            return False
        if self.deferred_item.ref_type != ref_type:
            return False
        if isinstance(ref_data, tuple) or isinstance(self.deferred_item.ref_data, tuple):
            return False
        if ref_type not in self.NAME_TO_STRUCTURE:
            return False
        assert self.deferred_item.ref_data is not None
        assert ref_data is not None
        return self.NAME_TO_STRUCTURE[ref_type].is_next_identifier(self.deferred_item.ref_data, ref_data)

    def merge_to_deferred(self, ref_data: str, end_pos: int) -> None:
        assert self.deferred_item is not None
        assert isinstance(self.deferred_item.ref_data, str)
        self.deferred_item.ref_data = (self.deferred_item.ref_data, ref_data)
        self.deferred_item.end_pos = end_pos

    def commit_deferred_item(self) -> None:
        if self.deferred_item is None:
            return
        ref_list = getattr(self, self.deferred_item.ref_type + 's')
        item_to_add = (
            self.deferred_item.ref_data,
            self.deferred_item.start_pos,
            self.deferred_item.end_pos,
        )
        if ref_list[0][0] is None:
            ref_list[0] = item_to_add
        else:
            ref_list.append(item_to_add)
        self.deferred_item = None

    def iter(self, start_override: Optional[int], end_override: int) -> Iterable[InTextReference]:
        self.commit_deferred_item()
        ref_args = [self.act, None, None, None, None]
        levels = ("articles", "paragraphs", "points", "subpoints")
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
        assert start_override is not None
        yield InTextReference(start_override, end_override, Reference(*ref_args))


@attr.s(slots=True, frozen=True)
class GrammaticalAnalysisResult:
    tree: Any = attr.ib()

    act_references: Tuple[InTextReference, ...] = attr.ib(init=False)
    element_references: Tuple[InTextReference, ...] = attr.ib(init=False)
    act_id_abbreviations: Tuple[ActIdAbbreviation, ...] = attr.ib(init=False)
    special_expression: Union[None, BlockAmendmentMetadata] = attr.ib(init=False)

    @property
    def all_references(self) -> Tuple[InTextReference, ...]:
        return self.act_references + self.element_references

    @element_references.default
    def _element_references_default(self) -> Tuple[InTextReference, ...]:
        if isinstance(self.tree, model.BlockAmendment):
            refs_to_parse = list(self._iterate_references_in_block_amendment())
        else:
            refs_to_parse = list(self._iterate_references_in_compound_references())

        refs_found = set(reference for act_id, reference in refs_to_parse)

        # Collect all other refs scattered elsewhere
        for ref in iterate_depth_first(self.tree, model.Reference):
            if ref in refs_found:
                continue
            refs_to_parse.append((None, ref))

        result: List[InTextReference] = []
        for act_id, parsed_ref in refs_to_parse:
            result.extend(self._convert_single_reference(act_id, parsed_ref))
        return tuple(result)

    def _iterate_references_in_compound_references(self) -> Iterable[Tuple[Optional[str], model.Reference]]:
        for ref_container in iterate_depth_first(self.tree, model.CompoundReference):
            if not ref_container.references:
                continue
            act_id = None
            if ref_container.act_reference is not None:
                act_id = self._get_act_id_from_parse_result(ref_container.act_reference)
            for reference in ref_container.references:
                assert isinstance(reference, model.Reference)
                yield act_id, reference

    def _iterate_references_in_block_amendment(self) -> Iterable[Tuple[Optional[str], model.Reference]]:
        act_id = self._get_act_id_from_parse_result(self.tree.act_reference)
        if self.tree.amended_reference:
            assert isinstance(self.tree.amended_reference, model.Reference)
            yield act_id, self.tree.amended_reference
        if self.tree.inserted_reference:
            assert isinstance(self.tree.inserted_reference, model.Reference)
            yield act_id, self.tree.inserted_reference

    @classmethod
    def _convert_single_reference(cls, act_id: Optional[str], parsed_ref: model.Reference) -> Iterable[InTextReference]:
        reference_collector = ReferenceCollector()
        if act_id is not None:
            reference_collector.act = act_id

        cls._fill_reference_collector(parsed_ref, reference_collector)
        full_start_pos, full_end_pos = cls._get_subtree_start_and_end_pos(parsed_ref)
        yield from reference_collector.iter(full_start_pos, full_end_pos)

    @classmethod
    def _fill_reference_collector(cls, parsed_ref: model.Reference, reference_collector: ReferenceCollector) -> None:
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
    def _act_references_default(self) -> Tuple[InTextReference, ...]:
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
    def _get_act_id_from_parse_result(cls, act_ref: model.ActReference) -> str:
        if act_ref.act_id is not None:
            return "{}. évi {}. törvény".format(act_ref.act_id.year, act_ref.act_id.number)
        if act_ref.abbreviation is not None:
            return act_ref.abbreviation.s
        raise ValueError('Neither abbreviation, nor act_id in act_ref')

    @classmethod
    def _get_subtree_start_and_end_pos(cls, subtree: model.ModelBase) -> Tuple[int, int]:
        return subtree.parseinfo.pos, subtree.parseinfo.endpos

    @act_id_abbreviations.default
    def _act_id_abbreviations_default(self) -> Tuple[ActIdAbbreviation, ...]:
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
    def _special_expression_default(self) -> Union[None, BlockAmendmentMetadata]:
        if isinstance(self.tree, model.BlockAmendment):
            return self._convert_block_amendment()
        return None

    def _convert_block_amendment(self) -> Optional[BlockAmendmentMetadata]:
        if not isinstance(self.tree, model.BlockAmendment):
            return None
        assert isinstance(self.tree.act_reference, model.ActReference)
        act_id = self._get_act_id_from_parse_result(self.tree.act_reference)

        amended_reference = None
        if self.tree.amended_reference:
            amended_references = tuple(
                r.reference for r in self._convert_single_reference(act_id, self.tree.amended_reference)
            )
            # Block amendments may only be contigous ranges, not lists.
            if len(amended_references) != 1:
                # Most likely a misparse, so don't fail horribly in this case, just report
                # that this as not a block amendment. Same as failing in grammar phase.
                return None
            amended_reference = amended_references[0]

        inserted_reference = None
        if self.tree.inserted_reference:
            inserted_references = tuple(
                r.reference for r in self._convert_single_reference(act_id, self.tree.inserted_reference)
            )
            # Block amendments may only be contigous ranges, not lists.
            if len(inserted_references) != 1:
                # Most likely a misparse, so don't fail horribly in this case, just report
                # that this as not a block amendment. Same as failing in grammar phase.
                return None
            inserted_reference = inserted_references[0]

        if amended_reference is not None and inserted_reference is not None:
            # Act has to be cut off first, because otherwise relative_to does not do anything.
            inserted_reference = attr.evolve(inserted_reference, act=None)
            inserted_reference = inserted_reference.relative_to(amended_reference)
        return BlockAmendmentMetadata(
            amended_reference=amended_reference,
            inserted_reference=inserted_reference,
        )

    @classmethod
    def _indented_print(cls, node: Any = None, indent: str = '') -> None:
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

    def indented_print(self, indent: str = '') -> None:
        self._indented_print(self.tree, indent)


class GrammaticalAnalyzer:
    def __init__(self) -> None:
        self.parser = ActGrammarParser(
            semantics=model.ActGrammarModelBuilderSemantics(),  # type: ignore
            parseinfo=True
        )

    def analyze(self, s: str, *, debug: bool = False) -> GrammaticalAnalysisResult:
        parse_result = self.parser.parse(
            s,
            rule_name='start_default',
            trace=debug, colorize=debug,
        )
        return GrammaticalAnalysisResult(parse_result)
