# Copyright 2018 Alex Badics <admin@stickman.hu>
#
# This file is part of Law-tools.
#
# Law-tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Law-tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Law-tools.  If not, see <https://www.gnu.org/licenses/>.
import re
from collections import deque

from . import structure_parser, reference_parser
from law_tools.utils import IndentedLine, indented_line_wrapped_print

# Main act on which all the code was based:
# 61/2009. (XII. 14.) IRM rendelet a jogszabályszerkesztésről


class NotAmendmentError(Exception):
    pass


class StructuredAmendment:
    INSTEAD_OF_HEURISTIC_RE = re.compile('^Az? ([A-ZÉÁŐÚÖÜÓÍ][a-zéáőúöüóí]+\\.)(.+)$')

    POSTFIXES = (
        "helyébe a következő rendelkezés lép:",
        "helyébe a következő rendelkezések lépnek:",
        "a következő szöveggel lép hatályba:",
    )
    def __init__(self, text):
        self.reference_string = None
        self.act_reference = None
        self.from_now_on = None
        self.structure_reference = None
        self.context_intro = None
        self.children = None
        self.context_wrap_up = None
        self.parse_text(text)

    # 106. §, 107. §
    def parse_text(self, text):
        text = deque(text)  # We are going to pop the front a lot
        self.reference_string = text.popleft().content
        self.postfix = None
        while True:
            # Endswith instead of "in", because there is a guaranteed newline after the ':'
            for postfix in self.POSTFIXES:
                if self.reference_string.endswith(postfix):
                    self.postfix = postfix
            if self.postfix is not None:
                break
            if not text:
                raise NotAmendmentError('Amendment postfix not found')
            self.reference_string = self.reference_string + " " + text.popleft().content

        self.parse_refs()

        # To avoid verbosity
        reftype = self.structure_reference.referenced_structure
        reftypes = reference_parser.StructureReference.RefType

        if reftype in (reftypes.NUMERIC_POINT, reftypes.ALPHABETIC_POINT, reftypes.SUBPOINT):
            self.parse_intro_wrap_up(text)

        if reftype == reftypes.ARTICLE:
            self.create_children(text, structure_parser.Article, self.structure_reference.article)
        elif reftype == reftypes.PARAGRAPH:
            self.create_children(text, structure_parser.Paragraph, self.structure_reference.paragraph)
        elif reftype == reftypes.NUMERIC_POINT:
            self.create_children(text, structure_parser.NumericPoint, self.structure_reference.point)
        elif reftype == reftypes.ALPHABETIC_POINT:
            self.create_children(text, structure_parser.AlphabeticPoint, self.structure_reference.point)
        elif reftype == reftypes.SUBPOINT:
            self.create_children(text, structure_parser.AlphabeticSubpoint, self.structure_reference.subpoint)
        else:
            raise NotAmendmentError("Reftype {} not supported for amendments".format(reftype))

    def parse_intro_wrap_up(self, text):
        while text and text[0].content[0] != "„":
            intro_line = text.popleft()
            if self.context_intro is not None:
                self.context_intro = self.context_intro + " " + intro_line.content
            else:
                self.context_intro = intro_line.content

        while text and text[-1].content[-1] != "”":
            wrap_up_line = text.pop()
            if self.context_wrap_up is not None:
                self.context_wrap_up = wrap_up_line.content + " " + self.context_wrap_up
            else:
                self.context_wrap_up = wrap_up_line.content

        if not text:
            raise NotAmendmentError("Block quote not found after cutting intro/wrap_up ('{}' / '{}')".format(self.context_intro, self.context_wrap_up))

    def parse_refs(self):
        # This would be cleaner, if we would have access to the "instead of" mechanic of
        # references of previous paragraphs, but due to the recursive nature of
        # structure parsing, this is not really possible, so we use a heuristic here
        # and maybe fix up the reference later.
        matches = self.INSTEAD_OF_HEURISTIC_RE.match(self.reference_string)
        if matches:
            self.act_reference = matches.group(1)
            structure_reference_string = matches.group(2)
        else:
            try:
                self.act_reference, self.from_now_on, structure_reference_string = reference_parser.RigidReference.extract_from_string(self.reference_string)
            except reference_parser.NotAReferenceError as e:
                raise NotAmendmentError("Rigid reference could not be parsed") from e

        structure_reference_string = structure_reference_string.strip()
        try:
            self.structure_reference, rest_of_string = reference_parser.StructureReference.extract_from_string(structure_reference_string)
        except reference_parser.NotAReferenceError as e:
            raise NotAmendmentError("Structure reference could not be parsed") from e

        # Cut down any possible suffixes from the reference
        # If no suffix was added to the Reference, rest_of_string
        # will begin with a space character.
        rest_of_string = rest_of_string[rest_of_string.index(' ')+1:]

        if rest_of_string != self.postfix:
            raise NotAmendmentError("Junk between structure reference and postfix: '{}'".format(rest_of_string))

    def create_children(self, block_quote_text, child_class, identifier):
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

        self.children = [child_class(text, identifier)]

    def print_to_console(self, indent):
        indented_line_wrapped_print(self.reference_string, indent)
        indent = " " * len(indent)
        indented_line_wrapped_print("„", indent)
        for p in self.children:
            p.print_to_console(indent + " "*5)
        indented_line_wrapped_print("”", indent)
