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
from collections import deque

from hun_law.utils import IndentedLine
from hun_law.structure import StructuredAmendment
from .reference_parser import RigidReference, NotAReferenceError, StructureReference

from . import structure_parser

# Main act on which all the code was based:
# 61/2009. (XII. 14.) IRM rendelet a jogszabályszerkesztésről


class NotAmendmentError(Exception):
    pass


class StructuredAmendmentParser:
    INSTEAD_OF_HEURISTIC_RE = re.compile('^Az? ([A-ZÉÁŐÚÖÜÓÍ][a-zéáőúöüóí]+\\.)(.+)$')

    POSTFIXES = (
        "helyébe a következő rendelkezés lép:",
        "helyébe a következő rendelkezések lépnek:",
        "a következő szöveggel lép hatályba:",
    )
    # 106. §, 107. §

    @classmethod
    def parse(cls, text):
        act_reference = None
        from_now_on = None
        structure_reference = None
        context_intro = None
        context_wrap_up = None
        postfix = None
        text = deque(text)  # We are going to pop the front a lot
        reference_string = text.popleft().content
        while True:
            # Endswith instead of "in", because there is a guaranteed newline after the ':'
            for possible_postfix in cls.POSTFIXES:
                if reference_string.endswith(possible_postfix):
                    postfix = possible_postfix
            if postfix is not None:
                break
            if not text:
                raise NotAmendmentError('Amendment postfix not found')
            reference_string = reference_string + " " + text.popleft().content

        act_reference, from_now_on, structure_reference = cls.parse_refs(reference_string, postfix)

        # To avoid verbosity
        reftype = structure_reference.referenced_structure
        reftypes = StructureReference.RefType

        if reftype in (reftypes.NUMERIC_POINT, reftypes.ALPHABETIC_POINT, reftypes.SUBPOINT):
            context_intro, context_wrap_up = cls.parse_intro_wrap_up(text)

        if reftype == reftypes.ARTICLE:
            children = cls.create_children(text, structure_parser.ArticleParser, structure_reference.article)
        elif reftype == reftypes.PARAGRAPH:
            children = cls.create_children(text, structure_parser.ParagraphParser, structure_reference.paragraph)
        elif reftype == reftypes.NUMERIC_POINT:
            children = cls.create_children(text, structure_parser.NumericPointParser, structure_reference.point)
        elif reftype == reftypes.ALPHABETIC_POINT:
            children = cls.create_children(text, structure_parser.AlphabeticPointParser, structure_reference.point)
        elif reftype == reftypes.SUBPOINT:
            children = cls.create_children(text, structure_parser.AlphabeticSubpointParser, structure_reference.subpoint)
        else:
            raise NotAmendmentError("Reftype {} not supported for amendments".format(reftype))

        return StructuredAmendment(
            reference_string,
            act_reference,
            from_now_on,
            structure_reference,
            context_intro,
            context_wrap_up,
            children
        )

    @classmethod
    def parse_intro_wrap_up(cls, text):
        context_intro = None
        context_wrap_up = None
        while text and text[0].content[0] != "„":
            intro_line = text.popleft()
            if context_intro is not None:
                context_intro = context_intro + " " + intro_line.content
            else:
                context_intro = intro_line.content

        while text and text[-1].content[-1] != "”":
            wrap_up_line = text.pop()
            if context_wrap_up is not None:
                context_wrap_up = wrap_up_line.content + " " + context_wrap_up
            else:
                context_wrap_up = wrap_up_line.content

        if not text:
            raise NotAmendmentError("Block quote not found after cutting intro/wrap_up ('{}' / '{}')".format(context_intro, context_wrap_up))
        return context_intro, context_wrap_up

    @classmethod
    def parse_refs(cls, reference_string, postfix):
        # This would be cleaner, if we would have access to the "instead of" mechanic of
        # references of previous paragraphs, but due to the recursive nature of
        # structure parsing, this is not really possible, so we use a heuristic here
        # and maybe fix up the reference later.
        act_reference = None
        from_now_on = None
        structure_reference = None
        matches = cls.INSTEAD_OF_HEURISTIC_RE.match(reference_string)
        if matches:
            act_reference = matches.group(1)
            structure_reference_string = matches.group(2)
        else:
            try:
                act_reference, from_now_on, structure_reference_string = RigidReference.extract_from_string(reference_string)
            except NotAReferenceError as e:
                raise NotAmendmentError("Rigid reference could not be parsed") from e

        structure_reference_string = structure_reference_string.strip()
        try:
            structure_reference, rest_of_string = StructureReference.extract_from_string(structure_reference_string)
        except NotAReferenceError as e:
            raise NotAmendmentError("Structure reference could not be parsed") from e

        # Cut down any possible suffixes from the reference
        # If no suffix was added to the Reference, rest_of_string
        # will begin with a space character.
        rest_of_string = rest_of_string[rest_of_string.index(' ')+1:]

        if rest_of_string != postfix:
            raise NotAmendmentError("Junk between structure reference and postfix: '{}'".format(rest_of_string))
        return act_reference, from_now_on, structure_reference

    @classmethod
    def create_children(cls, block_quote_text, child_parser, identifier):
        if block_quote_text[0].content[0] != "„" or block_quote_text[-1].content[-1] != '”':
            raise NotAmendmentError("Block quote not found")

        first_line = block_quote_text.popleft()
        if block_quote_text:
            first_indented = IndentedLine(first_line.content[1:], first_line.indent)
            last_line = block_quote_text.pop()
            # TODO XXX: This indentation is certainly wrong and WILL come back to haunt us
            # This is correct though :)
            last_indented = IndentedLine(last_line.content[:-1], last_line.indent)
            text = [first_indented] + list(block_quote_text) + [last_indented]
        else:
            first_indented = IndentedLine(first_line.content[1:-1], first_line.indent)
            text = [first_indented]

        return [child_parser.parse(text, identifier)]
