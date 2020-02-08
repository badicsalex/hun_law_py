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
from abc import ABC, abstractmethod
from typing import Dict, Union, Type, Any, Optional, Iterable, Tuple, ClassVar

import attr
import tatsu
import tatsu.model

from hun_law.structure import Reference, ActIdAbbreviation, InTextReference, BlockAmendmentMetadata, SemanticData, \
    Article, Paragraph, AlphabeticPoint, NumericPoint, AlphabeticSubpoint, \
    Act, SubArticleElement, \
    ReferencePartType, \
    StructuralReference, SubtitleReferenceArticleRelative, RelativePosition, Subtitle

from .grammar import model
from .grammar.parser import ActGrammarParser  # type: ignore


def get_subtree_start_and_end_pos(subtree: model.ModelBase) -> Tuple[int, int]:
    return subtree.parseinfo.pos, subtree.parseinfo.endpos


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


ConversionResultType = Union[InTextReference, ActIdAbbreviation, SemanticData]


class ModelConverter(ABC):
    # TODO: This used to not have a value, but pylint seems to complain
    # about usages then. I don't know why.
    CONVERTED_TYPE: ClassVar[Type[model.ModelBase]] = model.ModelBase

    @classmethod
    @abstractmethod
    def convert(cls, tree_element: model.ModelBase) -> Iterable[ConversionResultType]:
        """ Convert a model element to any number of structure elements """


class ReferenceConversionHelper:
    """ Method namespace to convert model.Reference to structure.InTextReference

    Not an actual ModelConverter, just a helper class, because most references will
    have an Act Id as context, so we only want to be called from the appropriate
    complex converters"""

    @classmethod
    def _fill_reference_collector(cls, parsed_ref: model.Reference, reference_collector: ReferenceCollector) -> None:
        assert isinstance(parsed_ref, model.Reference), parsed_ref
        for ref_part in parsed_ref.children():
            assert isinstance(ref_part, model.ReferencePart), ref_part
            ref_type_name = ref_part.__class__.__name__[:-len('ReferencePart')].lower()
            for ref_list_item in ref_part.singles:
                start_pos, end_pos = get_subtree_start_and_end_pos(ref_list_item)
                id_as_string = "".join(ref_list_item.id.id)
                reference_collector.add_item(ref_type_name, id_as_string, start_pos, end_pos)
            for ref_list_item in ref_part.ranges:
                start_pos, end_pos = get_subtree_start_and_end_pos(ref_list_item)
                start_id_as_string = "".join(ref_list_item.start.id)
                end_id_as_string = "".join(ref_list_item.end.id)
                reference_collector.add_item(ref_type_name, (start_id_as_string, end_id_as_string), start_pos, end_pos)

    @classmethod
    def convert_single_reference(cls, act_id: Optional[str], parsed_ref: model.Reference) -> Iterable[InTextReference]:
        reference_collector = ReferenceCollector()
        if act_id is not None:
            reference_collector.act = act_id

        cls._fill_reference_collector(parsed_ref, reference_collector)
        full_start_pos, full_end_pos = get_subtree_start_and_end_pos(parsed_ref)
        yield from reference_collector.iter(full_start_pos, full_end_pos)


class ActReferenceConversionHelper:
    """ Method namespace to help converting model.ActReferences """

    @classmethod
    def get_act_id_from_parse_result(cls, act_ref: model.ActReference) -> str:
        if act_ref.act_id is not None:
            return "{}. évi {}. törvény".format(act_ref.act_id.year, act_ref.act_id.number)
        if act_ref.abbreviation is not None:
            return act_ref.abbreviation.s
        raise ValueError('Neither abbreviation, nor act_id in act_ref')

    @classmethod
    def get_act_id_pos_from_parse_result(cls, act_ref: model.ActReference) -> Tuple[int, int]:
        if act_ref.abbreviation is not None:
            return get_subtree_start_and_end_pos(act_ref.abbreviation)
        if act_ref.act_id is not None:
            return get_subtree_start_and_end_pos(act_ref.act_id)
        raise ValueError('Neither abbreviation, nor act_id in act_ref')


class CompoundReferenceToInTextReference(ModelConverter):
    CONVERTED_TYPE = model.CompoundReference
    @classmethod
    def convert(cls, tree_element: model.CompoundReference) -> Iterable[InTextReference]:
        act_id = None
        if tree_element.act_reference is not None:
            act_id = ActReferenceConversionHelper.get_act_id_from_parse_result(tree_element.act_reference)
            start_pos, end_pos = ActReferenceConversionHelper.get_act_id_pos_from_parse_result(tree_element.act_reference)
            yield InTextReference(start_pos, end_pos, Reference(act=act_id))

        if tree_element.references:
            for reference in tree_element.references:
                assert isinstance(reference, model.Reference)
                yield from ReferenceConversionHelper.convert_single_reference(act_id, reference)


class ActReferenceToActIdAbbreviation(ModelConverter):
    CONVERTED_TYPE = model.ActReference
    @classmethod
    def convert(cls, tree_element: model.ActReference) -> Iterable[ActIdAbbreviation]:
        if tree_element.from_now_on is None:
            return ()

        return (
            ActIdAbbreviation(
                str(tree_element.from_now_on.abbreviation.s),
                ActReferenceConversionHelper.get_act_id_from_parse_result(tree_element)
            ),
        )


class BlockAmendmentToInTextReference(ModelConverter):
    CONVERTED_TYPE = model.BlockAmendment

    @classmethod
    def convert_potential_reference(cls, act_id: str, reference: Optional[model.Reference]) -> Optional[InTextReference]:
        if not reference:
            return None
        converted_references = tuple(
            ReferenceConversionHelper.convert_single_reference(act_id, reference),
        )
        # Block amendments may only be contigous ranges, not actual lists.
        if len(converted_references) != 1:
            # Most likely a misparse, so don't fail horribly in this case, just pretend
            # we did not find anything.
            return None
        return converted_references[0]

    @classmethod
    def convert(cls, tree_element: model.BlockAmendment) -> Iterable[InTextReference]:
        assert isinstance(tree_element.act_reference, model.ActReference)
        act_id = ActReferenceConversionHelper.get_act_id_from_parse_result(tree_element.act_reference)
        act_start_pos, act_end_pos = ActReferenceConversionHelper.get_act_id_pos_from_parse_result(tree_element.act_reference)
        yield InTextReference(act_start_pos, act_end_pos, Reference(act=act_id))

        amended_reference = cls.convert_potential_reference(act_id, tree_element.amended_reference)
        inserted_reference = cls.convert_potential_reference(act_id, tree_element.inserted_reference)

        if amended_reference is not None and inserted_reference is not None:
            # Act has to be cut off first, because otherwise relative_to does not do anything.
            fixed_ref = attr.evolve(inserted_reference.reference, act=None).relative_to(amended_reference.reference)
            inserted_reference = attr.evolve(inserted_reference, reference=fixed_ref)

        if amended_reference:
            yield amended_reference
        if inserted_reference:
            yield inserted_reference


class BlockAmendmentToBlockAmendmentMetadata(ModelConverter):
    CONVERTED_TYPE = model.BlockAmendment

    @classmethod
    def convert_potential_reference(cls, act_id: str, reference: Optional[model.Reference]) -> Optional[Reference]:
        if not reference:
            return None
        converted_references = tuple(
            ReferenceConversionHelper.convert_single_reference(act_id, reference),
        )
        # Block amendments may only be contigous ranges, not actual lists.
        if len(converted_references) != 1:
            # Most likely a misparse, so don't fail horribly in this case, just pretend
            # we did not find anything.
            return None
        return converted_references[0].reference

    @classmethod
    def convert_structural_reference(cls, act_id: str, reference: Optional[model.StructuralReference]) -> StructuralReference:
        if isinstance(reference, model.BeforeArticle):
            assert reference.id is not None
            return StructuralReference(act_id, subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "".join(reference.id)))

        if isinstance(reference, model.AfterArticle):
            assert reference.id is not None
            return StructuralReference(act_id, subtitle=SubtitleReferenceArticleRelative(RelativePosition.AFTER, "".join(reference.id)))

        return StructuralReference(act_id)

    @classmethod
    def get_reference_range_and_type(cls, reference: Reference) -> Tuple[Tuple[str, str], Type[Union[SubArticleElement, Article]]]:
        expected_id_range, expected_type = reference.last_component_with_type()

        assert expected_type is not None
        assert not issubclass(expected_type, Act)

        assert expected_id_range is not None
        if isinstance(expected_id_range, str):
            expected_id_range = (expected_id_range, expected_id_range)
        return expected_id_range, expected_type

    @classmethod
    def sae_amendment_only(cls, amended_reference: Reference) -> BlockAmendmentMetadata:
        expected_id_range, expected_type = cls.get_reference_range_and_type(amended_reference)
        return BlockAmendmentMetadata(
            expected_type=expected_type,
            expected_id_range=expected_id_range,
            position=amended_reference.first_in_range(),
            replaces=(amended_reference,),
        )

    @classmethod
    def sae_insertion_only(cls, inserted_reference: Reference) -> BlockAmendmentMetadata:
        expected_id_range, expected_type = cls.get_reference_range_and_type(inserted_reference)
        return BlockAmendmentMetadata(
            expected_type=expected_type,
            expected_id_range=expected_id_range,
            position=inserted_reference.first_in_range(),
        )

    @classmethod
    def sae_amendment_and_insertion(cls, amended_reference: Reference, inserted_reference: Reference) -> BlockAmendmentMetadata:
        amended_range, amended_type = cls.get_reference_range_and_type(amended_reference)
        inserted_range, inserted_type = cls.get_reference_range_and_type(inserted_reference)
        assert amended_type == inserted_type
        assert amended_type.is_next_identifier(amended_range[1], inserted_range[0])
        expected_id_range = (amended_range[0], inserted_range[1])
        return BlockAmendmentMetadata(
            expected_type=amended_type,
            expected_id_range=expected_id_range,
            position=amended_reference.first_in_range(),
            replaces=(amended_reference,),
        )

    @classmethod
    def convert_simple_case(cls, act_id: str, tree_element: model.BlockAmendment) -> Iterable[BlockAmendmentMetadata]:
        amended_reference = cls.convert_potential_reference(act_id, tree_element.amended_reference)
        inserted_reference = cls.convert_potential_reference(act_id, tree_element.inserted_reference)
        if amended_reference is not None:
            if inserted_reference:
                yield cls.sae_amendment_and_insertion(amended_reference, inserted_reference)
            else:
                yield cls.sae_amendment_only(amended_reference)
        elif inserted_reference is not None:
            yield cls.sae_insertion_only(inserted_reference)
        else:
            # One or both references were misparsed probably, or grammar is wrong
            # Don't fail horribly in this case, as the rest of the text is probably
            # okay, and we can salvage the situation.
            # TODO: Maybe we really should fail here.
            pass

    @classmethod
    def convert_id_range_for_subtitle_case(cls, reference: Optional[Reference]) -> Optional[Tuple[str, str]]:
        if reference is None or reference.article is None:
            return None
        if isinstance(reference.article, str):
            return (reference.article, reference.article)
        return reference.article

    @classmethod
    def subtitle_amendment_only(cls, structural_reference: StructuralReference, amended_reference: Reference) -> BlockAmendmentMetadata:
        expected_id_range = cls.convert_id_range_for_subtitle_case(amended_reference)
        if structural_reference.subtitle is None:
            assert isinstance(amended_reference.article, str)
            structural_reference = StructuralReference(
                amended_reference.act,
                subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, amended_reference.article)
            )

        replaces: Tuple[Union[Reference, StructuralReference], ...] = (structural_reference, )
        if amended_reference.article is not None:
            replaces = replaces + (amended_reference, )
        return BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=expected_id_range,
            position=structural_reference,
            replaces=replaces,
        )

    @classmethod
    def subtitle_insertion_only(cls, structural_reference: StructuralReference, inserted_reference: Optional[Reference]) -> BlockAmendmentMetadata:
        expected_id_range = cls.convert_id_range_for_subtitle_case(inserted_reference)
        return BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=expected_id_range,
            position=structural_reference,
        )

    @classmethod
    def convert_subtitle_case(cls, act_id: str, tree_element: model.BlockAmendment) -> Iterable[BlockAmendmentMetadata]:
        assert isinstance(tree_element.act_reference, model.ActReference)
        act_id = ActReferenceConversionHelper.get_act_id_from_parse_result(tree_element.act_reference)

        structural_reference = cls.convert_structural_reference(act_id, tree_element.structural_reference)
        amended_reference = cls.convert_potential_reference(act_id, tree_element.amended_reference)
        inserted_reference = cls.convert_potential_reference(act_id, tree_element.inserted_reference)
        if amended_reference is not None:
            if inserted_reference:
                # TODO. Not even part of the grammar currently either.
                raise ValueError("Simultaneous insertion and amendments with Subtitles not yet supported")
            yield cls.subtitle_amendment_only(structural_reference, amended_reference)
        else:
            yield cls.subtitle_insertion_only(structural_reference, inserted_reference)

    @classmethod
    def convert(cls, tree_element: model.BlockAmendment) -> Iterable[BlockAmendmentMetadata]:
        assert isinstance(tree_element.act_reference, model.ActReference)
        act_id = ActReferenceConversionHelper.get_act_id_from_parse_result(tree_element.act_reference)

        if (
                isinstance(tree_element.amended_reference, model.ReferenceWithSubtitle) or
                isinstance(tree_element.inserted_reference, model.ReferenceWithSubtitle)
        ):
            return cls.convert_subtitle_case(act_id, tree_element)
        return cls.convert_simple_case(act_id, tree_element)


@attr.s(slots=True, frozen=True)
class GrammarResultContainer:
    CONVERTER_CLASSES: Tuple[Type[ModelConverter], ...] = (
        CompoundReferenceToInTextReference,
        ActReferenceToActIdAbbreviation,
        BlockAmendmentToBlockAmendmentMetadata,
        BlockAmendmentToInTextReference,
    )

    tree: Any = attr.ib()
    results: Tuple[ConversionResultType, ...] = attr.ib(init=False)

    @classmethod
    def convert_single_node(cls, node: model.ModelBase) -> Iterable[ConversionResultType]:
        for converter in cls.CONVERTER_CLASSES:
            if isinstance(node, converter.CONVERTED_TYPE):
                yield from converter.convert(node)

    @classmethod
    def convert_depth_first(cls, node: model.ModelBase) -> Iterable[ConversionResultType]:
        if isinstance(node, tatsu.model.Node):
            to_iter = node.ast
        else:
            to_iter = node
        if isinstance(to_iter, dict):
            for k, v in to_iter.items():
                if k == 'parseinfo':
                    continue
                yield from cls.convert_depth_first(v)
        elif isinstance(to_iter, list):
            for v in to_iter:
                yield from cls.convert_depth_first(v)
        yield from cls.convert_single_node(node)

    @results.default
    def _results_default(self) -> Tuple[ConversionResultType, ...]:
        return tuple(self.convert_depth_first(self.tree))

    @property
    def all_references(self) -> Tuple[InTextReference, ...]:
        return tuple(r for r in self.results if isinstance(r, InTextReference))

    @property
    def act_references(self) -> Tuple[InTextReference, ...]:
        return tuple(r for r in self.all_references if r.reference.last_component_with_type()[1] is Act)

    @property
    def element_references(self) -> Tuple[InTextReference, ...]:
        return tuple(r for r in self.all_references if r.reference.last_component_with_type()[1] is not Act)

    @property
    def act_id_abbreviations(self) -> Tuple[ActIdAbbreviation, ...]:
        return tuple(r for r in self.results if isinstance(r, ActIdAbbreviation))

    @property
    def semantic_data(self) -> Tuple[SemanticData, ...]:
        return tuple(r for r in self.results if isinstance(r, SemanticData))


class GrammaticalAnalyzer:
    def __init__(self) -> None:
        self.parser = ActGrammarParser(
            semantics=model.ActGrammarModelBuilderSemantics(),  # type: ignore
            parseinfo=True
        )

    def analyze(self, s: str, *, debug: bool = False, print_result: bool = False) -> GrammarResultContainer:
        parse_result = self.parser.parse(
            s,
            rule_name='start_default',
            trace=debug, colorize=debug,
        )
        if print_result:
            self._indented_print(parse_result)
        return GrammarResultContainer(parse_result)

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
