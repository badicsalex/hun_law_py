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
import xml.etree.ElementTree as ET


STYLE = """
div {
    margin: 0px;
    padding: 0px;
}

table {
    border-spacing: 0px;
}

.list_header {
    width: 70px;
    vertical-align: top;
}

.list_item {
    vertical-align: top;
}

.article_title {
    font-style: italic;
    margin: 0px 0px 0px 50px;
}
"""

def indent_etree_element_in_place(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent_etree_element_in_place(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def generate_html_list(list_elements):
    table = ET.Element('table')
    for key, content_element in list_elements:
        tr = ET.SubElement(table, 'tr')
        key_td = ET.SubElement(tr, 'td', {'class': 'list_header'})
        key_td.text = str(key)

        content_td = ET.SubElement(tr, 'td', {'class': 'list_item'})
        content_td.append(content_element)
    return table

def generate_html_node_for_structural_element(element):
    pass


def generate_html_node_for_sub_article_elements(elements):
    processed_elements = []
    for e in elements:
        if isinstance(e, SubArticleElement):
            container = ET.Element('div')
            if e.text:
                container.text = e.text
            else:
                if e.intro:
                    intro = ET.SubElement(container,'div')
                    intro.text = e.intro
                container.append(generate_html_node_for_sub_article_elements(e.children))
                if e.wrap_up:
                    wrap_up = ET.SubElement(container,'div')
                    wrap_up.text = e.wrap_up
            header = e.header_prefix(e.identifier)
            processed_elements.append((header, container))
    return generate_html_list(processed_elements)


def generate_html_node_for_quoted_block(element):
    pass


def generate_html_node_for_article(article):
    container = ET.Element('div')
    if article.title:
        title = ET.Element('p', {'class': 'article_title'})
        title.text = '[{}]'.format(article.title)
        container.append(title)

    container.append(generate_html_node_for_sub_article_elements(article.children))

    return container


def generate_head_section(title_text):
    head = ET.Element('head')
    title = ET.SubElement(head,'title')
    title.text = title_text
    ET.SubElement(head, 'meta', {'http-equiv': "Content-Type", 'content': "text/html; charset=utf-8"})
    ET.SubElement(head, 'style').text = STYLE
    return head


def generate_html_document_for_act(act, output_file):
    html = ET.Element('html')
    html.append(generate_head_section(act.identifier))
    body = ET.Element('body')
    act_title = ET.Element('h1')
    act_title.text = act.identifier + ' ' + act.subject
    body.append(act_title)
    if act.preamble:
        preamble = ET.Element('p')
        # preamble.text = act.preamble
    articles = []
    for c in act.children:
        if not isinstance(c, Article):
            continue
        id_string = '{}. §'.format(c.identifier)
        articles.append((id_string, generate_html_node_for_article(c)))
    body.append(generate_html_list(articles))
    html.append(body)

    indent_etree_element_in_place(html)
    document = ET.ElementTree(html)
    output_file.write('<!DOCTYPE html>\n')
    document.write(output_file, encoding="unicode", method="html", xml_declaration=True)
