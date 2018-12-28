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
import xml.etree.ElementTree as ET

from hun_law.structure import SubArticleElement, QuotedBlock, Article, Subtitle
from hun_law.utils import EMPTY_LINE


def indent_etree_element_in_place(element, level=0):
    indent = "\n" + level * "  "
    if len(element):
        if not element.text or not element.text.strip():
            element.text = indent + "  "
        if not element.tail or not element.tail.strip():
            element.tail = indent
        subelement = None
        for subelement in element:
            indent_etree_element_in_place(subelement, level+1)
        if not subelement.tail or not subelement.tail.strip():
            subelement.tail = indent
    else:
        if level and (not element.tail or not element.tail.strip()):
            element.tail = indent


def generate_html_list(list_elements, element_class):
    css_name = 'sae_' + element_class.__name__.lower()
    table = ET.Element('table', {'class': 'list_table {}_table'.format(css_name)})
    for key, content_element in list_elements:
        tr = ET.SubElement(table, 'tr')
        key_td = ET.SubElement(tr, 'td', {'class': 'list_header {}_header'.format(css_name)})
        key_td.text = str(key)

        content_td = ET.SubElement(tr, 'td', {'class': 'list_item {}_item'.format(css_name)})
        content_td.append(content_element)
    return table


def generate_html_node_for_structural_element(element):
    container = ET.Element('div', {'class': 'structural_element se_' + element.__class__.__name__.lower()})
    if isinstance(element, Subtitle):
        container.text = element.formatted_identifier + " " + element.title
    else:
        container.text = element.formatted_identifier
        ET.SubElement(container, 'br').tail = element.title
    return container


def generate_html_node_for_sub_article_elements(elements):
    processed_elements = []
    for e in elements:
        if isinstance(e, SubArticleElement):
            container = ET.Element('div', {'class': 'list_item_content'})
            if e.text:
                container.text = e.text
            else:
                if e.intro:
                    intro = ET.SubElement(container, 'div')
                    intro.text = e.intro
                container.append(generate_html_node_for_sub_article_elements(e.children))
                if e.wrap_up:
                    wrap_up = ET.SubElement(container, 'div')
                    wrap_up.text = e.wrap_up
            header = e.header_prefix(e.identifier)
            processed_elements.append((header, container))
        elif isinstance(e, QuotedBlock):
            processed_elements.append(('', generate_html_node_for_quoted_block(e)))
    return generate_html_list(processed_elements, elements[0].__class__)


def generate_html_node_for_quoted_block(element):
    container = ET.Element('blockquote')
    indent_offset = min(l.indent for l in element.lines if l != EMPTY_LINE)
    for index, l in enumerate(element.lines):
        padding = int((l.indent-indent_offset) * 2)
        linediv = ET.SubElement(container, 'div', {'style': 'padding-left: {}px;'.format(padding)})
        text = l.content
        if index == 0:
            text = '„' + text
        if index == len(element.lines) - 1:
            text = text + "”"
        if not text:
            text = chr(0xA0)  # Non breaking space, so the div is forced to display.
        linediv.text = text
    return container


def generate_html_node_for_article(article):
    container = ET.Element('div')
    if article.title:
        title = ET.Element('div', {'class': 'article_title'})
        title.text = '[{}]'.format(article.title)
        container.append(title)

    container.append(generate_html_node_for_sub_article_elements(article.children))

    return container


def generate_html_body_for_act(act, indent=True):
    body = ET.Element('div', {'class': 'act_container'})
    act_title = ET.SubElement(body, 'div', {'class': 'act_title'})
    act_title.text = act.identifier
    ET.SubElement(act_title, 'br').tail = act.subject
    if act.preamble:
        preamble = ET.SubElement(body, 'div', {'class': 'preamble'})
        preamble.text = act.preamble
    body_elements = []
    for c in act.children:
        if isinstance(c, Article):
            id_string = '{}. §'.format(c.identifier)
            content = generate_html_node_for_article(c)
        else:
            id_string = ''
            content = generate_html_node_for_structural_element(c)
        body_elements.append((id_string, content))
    body.append(generate_html_list(body_elements, Article))
    if indent:
        indent_etree_element_in_place(body)
    return body
