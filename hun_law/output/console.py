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
from hun_law.structure import StructuralElement, SubArticleElement, QuotedBlock, Article, Act
from hun_law.utils import indented_line_wrapped_print, EMPTY_LINE

all_console_printers = []


def console_printer(printed_type):
    def console_printer_decorator(fn):
        global all_console_printers
        all_console_printers.append((printed_type, fn))
        return fn
    return console_printer_decorator


@console_printer(StructuralElement)
def print_structural_element_to_console(element, indent):
    name = "{} {}".format(element.__class__.__name__, element.identifier)
    indented_line_wrapped_print(name, indent)
    indent = indent + " " * 5
    if element.title:
        indented_line_wrapped_print(element.title)


@console_printer(SubArticleElement)
def print_sub_article_element_to_console(element, indent=''):
    if element.identifier:
        indent = indent + "{:<5}".format(element.header_prefix(element.identifier))
    else:
        indent = indent + " " * 5
    if element.text:
        indented_line_wrapped_print(element.text, indent)
    else:
        if element.intro:
            indented_line_wrapped_print(element.intro, indent)
            indent = " " * len(indent)
        for c in element.children:
            print_to_console(c, indent)
            indent = " " * len(indent)
        if element.wrap_up:
            indented_line_wrapped_print(element.wrap_up, indent)


@console_printer(QuotedBlock)
def print_quoted_block_to_console(element, indent=''):
    print(indent + '„')
    indent = " " * len(indent)
    base_indent_of_quote = min(l.indent for l in element.lines if l != EMPTY_LINE)
    for l in element.lines:
        indent_of_quote = ' ' * int((l.indent - base_indent_of_quote)*0.2)
        print(indent + ' ' * 5 + indent_of_quote + l.content)
    print(indent + '”')


@console_printer(Article)
def print_article_to_console(element, indent=''):
    indent = indent + "{:<10}".format(element.identifier + ". §")
    if element.title:
        indented_line_wrapped_print("     [{}]".format(element.title), indent)
        indent = " " * len(indent)

    for c in element.children:
        print_to_console(c, indent)
        indent = " " * len(indent)


@console_printer(Act)
def print_act_to_console(element, indent=''):
    print("==== Structured text of {} - {} =====\n".format(element.identifier, element.subject))
    indented_line_wrapped_print(element.preamble)
    for c in element.children:
        print_to_console(c, indent)
        indent = " " * len(indent)
        print()


def print_to_console(element, indent=''):
    global all_console_printers
    for printable_type, printer in all_console_printers:
        if isinstance(element, printable_type):
            printer(element, indent)
            break
    else:
        print("Unkown object type: {}\n".format(type(element)))
