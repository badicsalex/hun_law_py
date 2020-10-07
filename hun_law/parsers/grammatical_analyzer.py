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

from hun_law.structure import Reference, \
    Article, Paragraph, AlphabeticPoint, NumericPoint, AlphabeticSubpoint, \
    Act, SubArticleElement, \
    ReferencePartType, \
    StructuralReference, SubtitleArticleCombo, SubtitleArticleComboType,\
    ActIdAbbreviation, OutgoingReference, BlockAmendment, SemanticData, \
    EnforcementDate, DaysAfterPublication, DayInMonthAfterPublication, \
    TextAmendment, Repeal

from hun_law.utils import text_to_month_hun, text_to_int_hun, Date, flatten

from .grammar import model
from .grammar.parser import ActGrammarParser  # type: ignore


def get_subtree_start_and_end_pos(subtree: model.ModelBase) -> Tuple[int, int]:
    return subtree.parseinfo.pos, subtree.parseinfo.endpos


def convert_quote_to_string(quote: Any) -> str:
    assert quote[0] == "„"
    assert quote[-1] == "”"
    return "".join(flatten(quote[1:-1])).strip()


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

    def iter(self, start_override: Optional[int], end_override: int) -> Iterable[OutgoingReference]:
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
                    yield OutgoingReference(start, end, Reference(*ref_args))
                ref_args[arg_pos] = level_vals[-1][0]
            if start_override is None:
                start_override = level_vals[-1][1]
        assert start_override is not None
        yield OutgoingReference(start_override, end_override, Reference(*ref_args))


ConversionResultType = Union[OutgoingReference, ActIdAbbreviation, SemanticData]


class ModelConverter(ABC):
    # TODO: This used to not have a value, but pylint seems to complain
    # about usages then. I don't know why.
    CONVERTED_TYPE: ClassVar[Type[model.ModelBase]] = model.ModelBase

    @classmethod
    @abstractmethod
    def convert(cls, tree_element: model.ModelBase) -> Iterable[ConversionResultType]:
        """ Convert a model element to any number of structure elements """


class ReferenceConversionHelper:
    """ Method namespace to convert model.Reference to structure.OutgoingReference

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
    def convert_single_in_text_reference(cls, act_id: Optional[str], parsed_ref: model.Reference) -> Iterable[OutgoingReference]:
        reference_collector = ReferenceCollector()
        if act_id is not None:
            reference_collector.act = act_id

        cls._fill_reference_collector(parsed_ref, reference_collector)
        full_start_pos, full_end_pos = get_subtree_start_and_end_pos(parsed_ref)
        yield from reference_collector.iter(full_start_pos, full_end_pos)

    @classmethod
    def convert_multiple_in_text_references(cls, act_id: Optional[str], references: Iterable[model.Reference]) -> Iterable[OutgoingReference]:
        # Some references will be relative to the previous ones.
        # This may be considered a mistake in parsing the reference lists, but
        # this 'relativization' can only be done in the context of the whole sentence.
        # As an example, see:
        # "... az 1. § (2) bekezdése, és az (5) bekezdés ..."
        # This can be:
        # "Az 1. § (2) bekezdése, és az (5) bekezdése a kihirdetést követő napon lép hatályba"
        # Or:
        # "Fontos kivétel 1. § (2) bekezdése, és az (5) bekezdés szerinti definíció"
        last_reference = Reference(act=act_id)
        for reference in references:
            for converted_reference in ReferenceConversionHelper.convert_single_in_text_reference(None, reference):
                fixed_reference = converted_reference.reference.relative_to(last_reference)
                yield attr.evolve(converted_reference, reference=fixed_reference)
                last_reference = fixed_reference

    @classmethod
    def convert_potential_in_text_reference(cls, act_id: str, reference: Optional[model.Reference]) -> Optional[OutgoingReference]:
        if not reference:
            return None
        converted_references = tuple(
            cls.convert_single_in_text_reference(act_id, reference),
        )
        # Block amendments may only be contigous ranges, not actual lists.
        if len(converted_references) != 1:
            # Most likely a misparse, so don't fail horribly in this case, just pretend
            # we did not find anything.
            return None
        return converted_references[0]

    @classmethod
    def convert_potential_reference(cls, act_id: str, reference: Optional[model.Reference]) -> Optional[Reference]:
        result = cls.convert_potential_in_text_reference(act_id, reference)
        if result:
            return result.reference
        return None

    @classmethod
    def convert_book_id(cls, book_id: Optional[str]) -> Optional[str]:
        if book_id is None:
            return None
        return str(text_to_int_hun(book_id))

    @classmethod
    def convert_structural_reference(cls, act_id: str, reference: model.StructuralReference) -> StructuralReference:
        assert reference.id is not None
        if isinstance(reference, model.BeforeArticle):
            return StructuralReference(act_id, subtitle=SubtitleArticleCombo(SubtitleArticleComboType.BEFORE_WITHOUT_ARTICLE, "".join(reference.id)))

        if isinstance(reference, model.AfterArticle):
            return StructuralReference(act_id, subtitle=SubtitleArticleCombo(SubtitleArticleComboType.AFTER_WITHOUT_ARTICLE, "".join(reference.id)))

        if isinstance(reference, model.SubtitleNumber):
            return StructuralReference(act_id, subtitle="".join(reference.id))

        if isinstance(reference, model.ChapterNumber):
            return StructuralReference(act_id, chapter="".join(reference.id))

        if isinstance(reference, model.TitleNumber):
            return StructuralReference(
                act_id,
                book=cls.convert_book_id(reference.book_id),
                title="".join(reference.id),
            )

        if isinstance(reference, model.PartNumber):
            return StructuralReference(
                act_id,
                book=cls.convert_book_id(reference.book_id),
                part=str(text_to_int_hun(reference.id)),
            )

        raise TypeError("Unknown Structural Reference type")


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


class CompoundReferenceToOutgoingReference(ModelConverter):
    CONVERTED_TYPE = model.CompoundReference

    @classmethod
    def convert(cls, tree_element: model.CompoundReference) -> Iterable[OutgoingReference]:
        act_id = None
        if tree_element.act_reference is not None:
            act_id = ActReferenceConversionHelper.get_act_id_from_parse_result(tree_element.act_reference)
            start_pos, end_pos = ActReferenceConversionHelper.get_act_id_pos_from_parse_result(tree_element.act_reference)
            yield OutgoingReference(start_pos, end_pos, Reference(act=act_id))

        if tree_element.references:
            for reference in tree_element.references:
                assert isinstance(reference, model.Reference)
                yield from ReferenceConversionHelper.convert_single_in_text_reference(act_id, reference)


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


class BlockAmendmentToOutgoingReference(ModelConverter):
    CONVERTED_TYPE = model.BlockAmendment

    @classmethod
    def convert(cls, tree_element: model.BlockAmendment) -> Iterable[OutgoingReference]:
        assert isinstance(tree_element.act_reference, model.ActReference)
        act_id = ActReferenceConversionHelper.get_act_id_from_parse_result(tree_element.act_reference)
        act_start_pos, act_end_pos = ActReferenceConversionHelper.get_act_id_pos_from_parse_result(tree_element.act_reference)
        yield OutgoingReference(act_start_pos, act_end_pos, Reference(act=act_id))

        amended_reference = ReferenceConversionHelper.convert_potential_in_text_reference(act_id, tree_element.amended_reference)
        inserted_reference = ReferenceConversionHelper.convert_potential_in_text_reference(act_id, tree_element.inserted_reference)

        if amended_reference is not None and inserted_reference is not None:
            # Act has to be cut off first, because otherwise relative_to does not do anything.
            fixed_ref = attr.evolve(inserted_reference.reference, act=None).relative_to(amended_reference.reference)
            inserted_reference = attr.evolve(inserted_reference, reference=fixed_ref)

        if amended_reference:
            yield amended_reference
        if inserted_reference:
            yield inserted_reference


class BlockAmendmentToBlockAmendment(ModelConverter):
    CONVERTED_TYPE = model.BlockAmendment

    @classmethod
    def convert_amendment_and_insertion(cls, amended_reference: Reference, inserted_reference: Reference) -> BlockAmendment:
        # Act has to be cut off first, because otherwise relative_to does not do anything.
        inserted_reference = attr.evolve(inserted_reference, act=None).relative_to(amended_reference)
        if amended_reference.contains(inserted_reference.first_in_range()):
            # The weird case which amends 1-2, and inserts 1a in between
            union_reference = amended_reference
        else:
            union_reference = Reference.make_range(
                amended_reference.first_in_range(),
                inserted_reference.last_in_range()
            )
        return BlockAmendment(
            position=union_reference,
        )

    @classmethod
    def convert(cls, tree_element: model.BlockAmendment) -> Iterable[BlockAmendment]:
        assert isinstance(tree_element.act_reference, model.ActReference)
        act_id = ActReferenceConversionHelper.get_act_id_from_parse_result(tree_element.act_reference)

        amended_reference = ReferenceConversionHelper.convert_potential_reference(act_id, tree_element.amended_reference)
        inserted_reference = ReferenceConversionHelper.convert_potential_reference(act_id, tree_element.inserted_reference)
        if amended_reference is not None:
            if inserted_reference:
                yield cls.convert_amendment_and_insertion(amended_reference, inserted_reference)
            else:
                yield BlockAmendment(position=amended_reference)
        elif inserted_reference is not None:
            yield BlockAmendment(position=inserted_reference)
        else:
            # One or both references were misparsed probably, or grammar is wrong
            # Don't fail horribly in this case, as the rest of the text is probably
            # okay, and we can salvage the situation.
            # TODO: Maybe we really should fail here.
            pass


class BlockAmendmentWithSubtitleToBlockAmendment(ModelConverter):
    CONVERTED_TYPE = model.BlockAmendmentWithSubtitle

    @classmethod
    def convert_one(cls, structural_reference: StructuralReference, reference: Reference) -> BlockAmendment:
        if reference.article is not None:
            article_id = reference.article
            if isinstance(article_id, tuple):
                # Don't bother with ranges for now. MAYBE TODO
                article_id = article_id[0]
            assert article_id is not None
            position = StructuralReference(
                act=reference.act,
                subtitle=SubtitleArticleCombo(
                    SubtitleArticleComboType.BEFORE_WITH_ARTICLE,
                    article_id
                )
            )
        else:
            position = structural_reference
        return BlockAmendment(position=position)

    @classmethod
    def convert(cls, tree_element: model.BlockAmendment) -> Iterable[BlockAmendment]:
        assert isinstance(tree_element.act_reference, model.ActReference)
        act_id = ActReferenceConversionHelper.get_act_id_from_parse_result(tree_element.act_reference)

        if tree_element.structural_reference is not None:
            structural_reference = ReferenceConversionHelper.convert_structural_reference(act_id, tree_element.structural_reference)
        else:
            structural_reference = StructuralReference(act_id)
        amended_reference = ReferenceConversionHelper.convert_potential_reference(act_id, tree_element.amended_reference)
        inserted_reference = ReferenceConversionHelper.convert_potential_reference(act_id, tree_element.inserted_reference)
        if amended_reference is not None:
            if inserted_reference:
                # TODO. Not even part of the grammar currently either.
                raise ValueError("Simultaneous insertion and amendments with Subtitles not yet supported")
            yield cls.convert_one(structural_reference, amended_reference)
        else:
            yield cls.convert_one(structural_reference, inserted_reference)


class BlockAmendmentStructuralToBlockAmendment(ModelConverter):
    CONVERTED_TYPE = model.BlockAmendmentStructural

    @classmethod
    def convert(cls, tree_element: model.BlockAmendment) -> Iterable[BlockAmendment]:
        assert isinstance(tree_element.act_reference, model.ActReference)
        act_id = ActReferenceConversionHelper.get_act_id_from_parse_result(tree_element.act_reference)

        if tree_element.amended_reference is not None:
            if tree_element.inserted_reference is not None:
                # TODO. Not even part of the grammar currently either.
                raise ValueError("Simultaneous insertion and amendments with Structural References not yet supported")

            amended_reference = ReferenceConversionHelper.convert_structural_reference(act_id, tree_element.amended_reference)
            yield BlockAmendment(
                position=amended_reference,
            )
        else:
            assert tree_element.inserted_reference is not None
            inserted_reference = ReferenceConversionHelper.convert_structural_reference(act_id, tree_element.inserted_reference)
            yield BlockAmendment(
                position=inserted_reference,
            )


class EnforcementDateToEnforcementDate(ModelConverter):
    CONVERTED_TYPE = model.EnforcementDate

    @classmethod
    def convert_after_publication_date(cls, after_publication: model.AfterPublication) -> DaysAfterPublication:
        if after_publication.as_number:
            return DaysAfterPublication(int(after_publication.as_number[0]))
        if after_publication.as_text:
            return DaysAfterPublication(text_to_int_hun(after_publication.as_text))
        return DaysAfterPublication()

    @classmethod
    def convert_exact_date(cls, exact_date: model.Date) -> Date:
        assert isinstance(exact_date.year, str)
        assert isinstance(exact_date.month, str)
        assert isinstance(exact_date.day, str)
        return Date(
            int(exact_date.year),
            text_to_month_hun(exact_date.month),
            int(exact_date.day)
        )

    @classmethod
    def convert_day_in_month(cls, day_in_month: model.DayInMonth) -> DayInMonthAfterPublication:
        if day_in_month.month:
            months = text_to_int_hun(day_in_month.month)
        else:
            months = 1

        if day_in_month.day_as_number:
            day = int(day_in_month.day_as_number[0])
        elif day_in_month.day_as_text:
            day = text_to_int_hun(day_in_month.day_as_text)
        else:
            raise ValueError("No actual day in 'DayInMonth'. Grammar is probably wrong")

        return DayInMonthAfterPublication(day=day, months=months)

    @classmethod
    def convert(cls, tree_element: model.EnforcementDate) -> Iterable[EnforcementDate]:
        if tree_element.exact_date:
            date = cls.convert_exact_date(tree_element.exact_date)
        elif tree_element.after_publication:
            date = cls.convert_after_publication_date(tree_element.after_publication)
        elif tree_element.day_in_month:
            date = cls.convert_day_in_month(tree_element.day_in_month)
        else:
            raise ValueError("No actual date in 'EnforcementDate'. Grammar is probably wrong")

        if tree_element.inline_repeal:
            repeal_date = cls.convert_exact_date(tree_element.inline_repeal.date)
        else:
            repeal_date = None
        if not tree_element.references:
            yield EnforcementDate(position=None, date=date, repeal_date=repeal_date)
        else:
            for reference in ReferenceConversionHelper.convert_multiple_in_text_references(None, tree_element.references):
                yield EnforcementDate(position=reference.reference, date=date, repeal_date=repeal_date)


class EnforcementDateToReference(ModelConverter):
    CONVERTED_TYPE = model.EnforcementDate

    @classmethod
    def convert(cls, tree_element: model.EnforcementDate) -> Iterable[OutgoingReference]:
        if tree_element.references:
            yield from ReferenceConversionHelper.convert_multiple_in_text_references(None, tree_element.references)
        if tree_element.exception_references:
            yield from ReferenceConversionHelper.convert_multiple_in_text_references(None, tree_element.exception_references)


class TextAmendmentToTextAmendment(ModelConverter):
    CONVERTED_TYPE = model.TextAmendment

    @classmethod
    def convert_part(cls, reference: Reference, tree_element: model.TextAmendmentPart) -> TextAmendment:
        return TextAmendment(
            position=reference,
            original_text=convert_quote_to_string(tree_element.original_text),
            replacement_text=convert_quote_to_string(tree_element.replacement_text),
        )

    @classmethod
    def convert(cls, tree_element: model.TextAmendment) -> Iterable[TextAmendment]:
        assert tree_element.references is not None
        assert tree_element.parts is not None
        act_id = ActReferenceConversionHelper.get_act_id_from_parse_result(tree_element.act_reference)
        for reference in ReferenceConversionHelper.convert_multiple_in_text_references(act_id, tree_element.references):
            for amendment_part in tree_element.parts:
                yield cls.convert_part(reference.reference, amendment_part)


class TextAmendmentToReference(ModelConverter):
    CONVERTED_TYPE = model.TextAmendment

    @classmethod
    def convert(cls, tree_element: model.TextAmendment) -> Iterable[OutgoingReference]:
        assert tree_element.references is not None
        assert tree_element.parts is not None
        act_id = ActReferenceConversionHelper.get_act_id_from_parse_result(tree_element.act_reference)
        act_start_pos, act_end_pos = ActReferenceConversionHelper.get_act_id_pos_from_parse_result(tree_element.act_reference)
        yield OutgoingReference(act_start_pos, act_end_pos, Reference(act=act_id))
        yield from ReferenceConversionHelper.convert_multiple_in_text_references(act_id, tree_element.references)


class RepealToRepeal(ModelConverter):
    CONVERTED_TYPE = model.Repeal

    @classmethod
    def convert(cls, tree_element: model.Repeal) -> Iterable[Repeal]:
        assert tree_element.references is not None
        assert tree_element.texts is not None
        act_id = ActReferenceConversionHelper.get_act_id_from_parse_result(tree_element.act_reference)
        for reference in ReferenceConversionHelper.convert_multiple_in_text_references(act_id, tree_element.references):
            if not tree_element.texts:
                yield Repeal(position=reference.reference)
            else:
                for text in tree_element.texts:
                    yield Repeal(position=reference.reference, text=convert_quote_to_string(text))


class RepealToReference(ModelConverter):
    CONVERTED_TYPE = model.Repeal

    @classmethod
    def convert(cls, tree_element: model.Repeal) -> Iterable[OutgoingReference]:
        assert tree_element.references is not None
        act_id = ActReferenceConversionHelper.get_act_id_from_parse_result(tree_element.act_reference)
        act_start_pos, act_end_pos = ActReferenceConversionHelper.get_act_id_pos_from_parse_result(tree_element.act_reference)
        yield OutgoingReference(act_start_pos, act_end_pos, Reference(act=act_id))
        yield from ReferenceConversionHelper.convert_multiple_in_text_references(act_id, tree_element.references)


@attr.s(slots=True, frozen=True)
class GrammarResultContainer:
    CONVERTER_CLASSES: Tuple[Type[ModelConverter], ...] = (
        CompoundReferenceToOutgoingReference,
        ActReferenceToActIdAbbreviation,
        BlockAmendmentToBlockAmendment,
        BlockAmendmentWithSubtitleToBlockAmendment,
        BlockAmendmentStructuralToBlockAmendment,
        BlockAmendmentToOutgoingReference,
        EnforcementDateToEnforcementDate,
        EnforcementDateToReference,
        TextAmendmentToTextAmendment,
        TextAmendmentToReference,
        RepealToRepeal,
        RepealToReference,
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
    def all_references(self) -> Tuple[OutgoingReference, ...]:
        return tuple(r for r in self.results if isinstance(r, OutgoingReference))

    @property
    def act_references(self) -> Tuple[OutgoingReference, ...]:
        return tuple(r for r in self.all_references if r.reference.last_component_with_type()[1] is Act)

    @property
    def element_references(self) -> Tuple[OutgoingReference, ...]:
        return tuple(r for r in self.all_references if r.reference.last_component_with_type()[1] is not Act)

    @property
    def act_id_abbreviations(self) -> Tuple[ActIdAbbreviation, ...]:
        return tuple(r for r in self.results if isinstance(r, ActIdAbbreviation))

    @property
    def semantic_data(self) -> Tuple[SemanticData, ...]:
        return tuple(r for r in self.results if isinstance(r, SemanticData))


class GrammaticalParsingError(Exception):
    pass


class GrammaticalAnalyzer:
    def __init__(self) -> None:
        self.parser = ActGrammarParser(
            semantics=model.ActGrammarModelBuilderSemantics(),  # type: ignore
            parseinfo=True
        )

    def analyze(self, s: str, *, debug: bool = False, print_result: bool = False) -> GrammarResultContainer:
        try:
            parse_result = self.parser.parse(
                s,
                rule_name='start_default',
                trace=debug, colorize=debug,
            )
            if print_result:
                self._indented_print(parse_result)
            return GrammarResultContainer(parse_result)
        except Exception as e:
            raise GrammaticalParsingError("Error parsing '{}'".format(s)) from e

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
