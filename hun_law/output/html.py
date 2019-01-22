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
import xml.etree.ElementTree as ET

from hun_law.structure import SubArticleElement, QuotedBlock, Article, Subtitle, Reference
from hun_law.utils import EMPTY_LINE, is_uppercase_hun
from hun_law.parsers.grammatical_analyzer import GrammaticalAnalyzer, GrammaticalAnalysisError


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


def generate_html_node_for_structural_element(element):
    container = ET.Element('div', {'class': 'se_' + element.__class__.__name__.lower()})
    if isinstance(element, Subtitle):
        container.text = element.formatted_identifier + " " + element.title
    else:
        container.text = element.formatted_identifier
        ET.SubElement(container, 'br').tail = element.title
    yield container


def get_href_for_ref(ref):
    result = ''
    if ref.act is not None:
        result = ref.act + ".html"
    result = result + "#" + ref.relative_id_string
    return result


grammatical_analyzer = None


def generate_text_with_ref_links(container, text, current_ref, abbreviations):
    global grammatical_analyzer

    container.text = text
    if len(text)>10000:
        return

    interesting_substrings = (")", "§", "törvén")
    if not any(s in text for s in interesting_substrings):
        return

    if grammatical_analyzer is None:
        grammatical_analyzer = GrammaticalAnalyzer()

    # TODO: Points are actually parts of a bigger sentence, and we don't really put the
    # intro and wrap-up around them right now.
    intro = ''
    if not is_uppercase_hun(text[0]):
        intro = 'A '
    wrap_up = ''
    if text[-1] not in (".", ":", "?"):
        wrap_up = '.'
    offset = len(intro)
    end_offset = len(intro) + len(text)
    text = intro + text + wrap_up
    try:
        analysis_result = grammatical_analyzer.analyze(text)
    except GrammaticalAnalysisError as e:
        print("Error during parsing {}: {}".format(current_ref, e))
        return

    for k, v in analysis_result.get_new_abbreviations():
        abbreviations[k] = v

    links_to_create = []
    for ref, start, end in analysis_result.get_references(abbreviations):
        absolute_ref = ref.relative_to(current_ref)
        links_to_create.append((start, end, get_href_for_ref(absolute_ref)))

    for ref, start, end in analysis_result.get_act_references(abbreviations):
        links_to_create.append((start, end, ref + ".html"))

    links_to_create.sort()
    last_a_tag = None
    for start, end, href in links_to_create:
        assert start >= offset
        assert end > start
        if last_a_tag is None:
            container.text = text[offset:start]
        else:
            last_a_tag.tail = text[offset:start]
        last_a_tag = ET.SubElement(container, 'a', {'href': href})
        last_a_tag.text = text[start:end+1]
        offset = end + 1

    if last_a_tag is None:
        container.text = text[offset:end_offset]
    else:
        last_a_tag.tail = text[offset:end_offset]


def generate_html_nodes_for_children(element, parent_ref, abbreviations):
    for child in element.children:
        if isinstance(child, SubArticleElement):
            yield from generate_html_nodes_for_sub_article_element(child, parent_ref, abbreviations)
        elif isinstance(child, QuotedBlock):
            yield from generate_html_nodes_for_quoted_block(child, element)
        else:
            raise TypeError("Unknown child type {}".format(child.__class__))


def generate_html_nodes_for_sub_article_element(e, parent_ref, abbreviations):
    current_ref = e.relative_reference.relative_to(parent_ref)
    element_type_as_text = e.__class__.__name__.lower()
    id_element = ET.Element('div', {"id": current_ref.relative_id_string, 'class': '{}_id'.format(element_type_as_text)})
    id_element.text = e.header_prefix(e.identifier)
    yield id_element
    if e.text:
        container = ET.Element('div', {'class': '{}_text'.format(element_type_as_text)})
        generate_text_with_ref_links(container, e.text, current_ref, abbreviations)
        yield container
    else:
        if e.intro:
            intro_element = ET.Element('div', {'class': '{}_text'.format(element_type_as_text)})
            # TODO: We don't currently parse structural amendments properly
            # They have a two-part intro, which we unfortunately merge, which looks bad.
            matches = re.match(r"^(.*): ?(\([^\)]*\)|\[[^\]]*\])$", e.intro)
            if matches is not None:
                generate_text_with_ref_links(intro_element, matches.group(1), current_ref, abbreviations)
                ET.SubElement(intro_element, 'br').tail = matches.group(2)
            else:
                generate_text_with_ref_links(intro_element, e.intro, current_ref, abbreviations)
            yield intro_element

        yield from generate_html_nodes_for_children(e, current_ref, abbreviations)

        if e.wrap_up:
            wrap_up_element = ET.Element('div', {'class': '{}_text'.format(element_type_as_text)})
            wrap_up_element.text = e.wrap_up
            yield wrap_up_element


def generate_html_nodes_for_quoted_block(element, parent):
    container = ET.Element('blockquote', {'class': 'quote_in_{}'.format(parent.__class__.__name__.lower())})
    indent_offset = min(l.indent for l in element.lines if l != EMPTY_LINE)
    for index, l in enumerate(element.lines):
        padding = int((l.indent-indent_offset) * 2)
        if padding < 0:
            padding = 0
        linediv = ET.SubElement(container, 'div', {'style': 'padding-left: {}px;'.format(padding)})
        text = l.content
        if index == 0:
            text = '„' + text
        if index == len(element.lines) - 1:
            text = text + "”"
        if not text:
            text = chr(0xA0)  # Non breaking space, so the div is forced to display.
        linediv.text = text
    yield container


def generate_html_node_for_article(article, abbreviations):
    current_ref = article.relative_reference
    id_element = ET.Element('div', {"id": current_ref.relative_id_string, 'class': 'article_id'})
    id_element.text = '{}. §'.format(article.identifier)
    yield id_element

    if article.title:
        title_element = ET.Element('div', {'class': 'article_title'})
        title_element.text = '[{}]'.format(article.title)
        yield title_element

    yield from generate_html_nodes_for_children(article, current_ref, abbreviations)

    yield ET.Element('div', {'class': 'space_after_article'})


def generate_html_body_for_act(act, indent=True):
    body = ET.Element('div', {'class': 'act_container'})
    act_title = ET.SubElement(body, 'div', {'class': 'act_title'})
    act_title.text = act.identifier
    ET.SubElement(act_title, 'br').tail = act.subject
    if act.preamble:
        preamble = ET.SubElement(body, 'div', {'class': 'preamble'})
        preamble.text = act.preamble
    body_elements = []
    abbreviations = {}
    for c in act.children:
        if isinstance(c, Article):
            elements_to_add = generate_html_node_for_article(c, abbreviations)
        else:
            elements_to_add = generate_html_node_for_structural_element(c)
        for element_to_add in elements_to_add:
            body.append(element_to_add)
    if indent:
        indent_etree_element_in_place(body)
    return body
