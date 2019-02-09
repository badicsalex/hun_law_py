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
import json

from hun_law.structure import StructuralElement, SubArticleElement, QuotedBlock, Article, Act


def serialize_sae_to_json_compatible(sae):
    if isinstance(sae, QuotedBlock):
        return "\n".join([l.content for l in sae.lines])
    elif isinstance(sae, SubArticleElement):
        if sae.text is not None:
            return sae.text
        else:
            result = {
                "_intro": sae.intro,
                "_wrap_up": sae.wrap_up,
            }
            if len(sae.children) > 1:
                if sae.children_type == QuotedBlock:
                    result["blocks"] = [serialize_sae_to_json_compatible(c) for c in sae.children]
                else:
                    for c in sae.children:
                        assert c.identifier is not None
                        result[c.identifier] = serialize_sae_to_json_compatible(c)
            else:
                result['content'] = serialize_sae_to_json_compatible(sae.children[0])
            return result
    else:
        raise TypeError("Unknown Sub Article Element Type")


def serialize_act_child_to_json_compatible(child):
    result = {
        "type": child.__class__.__name__,
        "title": child.title,
        "id": child.identifier,
    }
    if isinstance(child, Article):
        if len(child.children) > 1:
            result['content'] = {}
            for c in child.children:
                result['content'][c.identifier] = serialize_sae_to_json_compatible(c)
        else:
            result['content'] = serialize_sae_to_json_compatible(child.children[0])
    elif isinstance(child, StructuralElement):
        result["id_human_readable"] = child.formatted_identifier
    else:
        raise TypeError("Unknown Act child type")
    return result


def serialize_act_to_json_compatible(act):
    return {
        'id': act.identifier,
        'subject': act.subject,
        'preamble': act.preamble,
        'content': [serialize_act_child_to_json_compatible(c) for c in act.children],
    }


def serialize_act_to_json_file(act, f):
    return json.dump(
        serialize_act_to_json_compatible(act),
        f,
        indent='  ',
        ensure_ascii=False,
        sort_keys=True
    )
