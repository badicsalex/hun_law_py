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
from typing import TextIO, Any, Callable, Type

from hun_law.extractors.magyar_kozlony import MagyarKozlonyLawRawText
from hun_law.structure import StructuralElement, SubArticleElement, BlockAmendment, QuotedBlock, Article, Act, Subtitle
from hun_law.utils import indented_line_wrapped_print, EMPTY_LINE

TxtWriterFn = Callable[[TextIO, Any, str], None]

all_txt_writers = []


def txt_writer(printed_type: Type) -> Callable[[TxtWriterFn], TxtWriterFn]:
    def txt_writer_decorator(fn: TxtWriterFn) -> TxtWriterFn:
        global all_txt_writers
        all_txt_writers.append((printed_type, fn))
        return fn
    return txt_writer_decorator


@txt_writer(Subtitle)
def write_subtitle_as_txt(output_file: TextIO, element: Subtitle, indent: str) -> None:
    id_to_print = ""
    if element.formatted_identifier:
        id_to_print = element.formatted_identifier + " "
    if element.title:
        id_to_print = id_to_print + element.title
    indented_line_wrapped_print(id_to_print.strip(), indent, file=output_file)


@txt_writer(StructuralElement)
def write_structural_element_as_txt(output_file: TextIO, element: StructuralElement, indent: str) -> None:
    indented_line_wrapped_print(element.formatted_identifier, indent, file=output_file)
    indent = " " * len(indent)
    if element.title:
        indented_line_wrapped_print(element.title, indent, file=output_file)


@txt_writer(BlockAmendment)
def write_block_amendment_as_txt(output_file: TextIO, element: BlockAmendment, indent: str) -> None:
    if element.intro:
        indented_line_wrapped_print('(' + element.intro + ')', indent, file=output_file)
    print(indent + '„', file=output_file)
    assert element.children is not None
    for c in element.children:
        write_txt(output_file, c, indent + " " * 5)
    print(indent + '”', file=output_file)
    if element.wrap_up:
        indented_line_wrapped_print('(' + element.wrap_up + ')', indent, file=output_file)


@txt_writer(SubArticleElement)
def write_sub_article_element_as_txt(output_file: TextIO, element: SubArticleElement, indent: str) -> None:
    if element.identifier:
        indent = indent + "{:<5}".format(element.header_prefix(element.identifier))
    else:
        indent = indent + " " * 5
    if element.text:
        indented_line_wrapped_print(element.text, indent, file=output_file)
    else:
        if element.intro:
            indented_line_wrapped_print(element.intro, indent, file=output_file)
            indent = " " * len(indent)
        assert element.children is not None
        for c in element.children:
            write_txt(output_file, c, indent)
            indent = " " * len(indent)
        if element.wrap_up:
            indented_line_wrapped_print(element.wrap_up, indent, file=output_file)


@txt_writer(QuotedBlock)
def write_quoted_block_as_txt(output_file: TextIO, element: QuotedBlock, indent: str) -> None:
    print(indent + '„', file=output_file)
    indent = " " * len(indent)
    base_indent_of_quote = min(l.indent for l in element.lines if l != EMPTY_LINE)
    for l in element.lines:
        indent_of_quote = ' ' * int((l.indent - base_indent_of_quote)*0.2)
        print(indent + ' ' * 5 + indent_of_quote + l.content, file=output_file)
    print(indent + '”', file=output_file)


@txt_writer(Article)
def write_article_as_txt(output_file: TextIO, element: Article, indent: str) -> None:
    indent = indent + "{:<10}".format(element.identifier + ". §")
    if element.title:
        indented_line_wrapped_print("     [{}]".format(element.title), indent, file=output_file)
        indent = " " * len(indent)

    for c in element.children:
        write_txt(output_file, c, indent)
        indent = " " * len(indent)


@txt_writer(Act)
def write_act_as_txt(output_file: TextIO, element: Act, indent: str) -> None:
    print("==== {} - {} =====\n".format(element.identifier, element.subject), file=output_file)
    indented_line_wrapped_print(element.preamble, file=output_file)
    for c in element.children:
        write_txt(output_file, c, indent)
        indent = " " * len(indent)
        print(file=output_file)


@txt_writer(MagyarKozlonyLawRawText)
def write_mk_raw_as_txt(output_file: TextIO, element: MagyarKozlonyLawRawText, indent: str) -> None:
    print("==== {} - {} =====\n".format(element.identifier, element.subject), file=output_file)
    base_indent_of_body = min(l.indent for l in element.body if l != EMPTY_LINE)
    for l in element.body:
        indent_of_line = ' ' * int((l.indent - base_indent_of_body)*0.2)
        bold_marker = '<BOLD> ' if l.bold else '       '
        print(indent + indent_of_line + bold_marker + l.content, file=output_file)
    print(file=output_file)


def write_txt(output_file: TextIO, element: Any, indent: str = '') -> None:
    global all_txt_writers
    for printable_type, printer in all_txt_writers:
        if isinstance(element, printable_type):
            printer(output_file, element, indent)
            break
    else:
        print("Unkown object type: {}\n".format(type(element)), file=output_file)
