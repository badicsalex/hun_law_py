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

from lark import Lark, Tree, Token

from hun_law.structure import Reference


class ReferenceCollector:
    def __init__(self):
        self.act = None
        self.articles = [(None, 0, 0)]
        self.paragraphs = [(None, 0, 0)]
        self.points = [(None, 0, 0)]
        self.alphabetic_points = self.points  # alias
        self.numeric_points = self.points  # alias
        self.subpoints = [(None, 0, 0)]
        self.alphabetic_subpoints = self.subpoints  # alias
        self.numeric_subpoints = self.subpoints  # alias

    def add_item(self, ref_type, ref_data, start_pos, end_pos):
        ref_list = getattr(self, ref_type + 's')
        if ref_list[0][0] is None:
            ref_list[0] = (ref_data, start_pos, end_pos)
        else:
            ref_list.append((ref_data, start_pos, end_pos))

    def iter(self):
        ref_args = [self.act, None, None, None, None]
        levels = ("articles", "paragraphs", "points", "subpoints")
        start_override = None
        last_end = 0
        for arg_pos, level in enumerate(levels, start=1):
            level_vals = getattr(self, level)
            if len(level_vals) == 1:
                ref_args[arg_pos] = level_vals[0][0]
            else:
                for level_val, start, end in level_vals[:-1]:
                    if start_override is not None:
                        start = start_override
                        start_override = None
                    ref_args[arg_pos] = level_val
                    yield Reference(*ref_args), start, end
                ref_args[arg_pos] = level_vals[-1][0]
            if start_override is None:
                start_override = level_vals[-1][1]
            last_end = max(last_end, level_vals[-1][2])
        yield Reference(*ref_args), start_override, last_end


class AbbreviationNotFoundError(Exception):
    pass


class GrammaticalAnalysisResult:
    def __init__(self, s, tree):
        self.s = s
        self.tree = tree

    def get_references(self, abbreviations):
        refs_to_parse = []
        refs_found = set()
        # Collect references where we might have Act Id
        for ref_container in self.tree.find_data('compound_reference'):
            act_id = None
            if len(ref_container.children) == 1:
                ref = ref_container.children[0]
                if ref.data == 'act_reference':
                    continue
            else:
                act_ref, ref = ref_container.children
                assert act_ref.data == 'act_reference'
                try:
                    act_id = self.get_act_id_from_parse_result(act_ref, abbreviations)
                except AbbreviationNotFoundError:
                    pass
            refs_to_parse.append((act_id, ref))
            refs_found.add(ref)

        # Collect all other refs scattered elsewhere
        for ref in self.tree.find_data('reference'):
            if ref in refs_found:
                continue
            refs_to_parse.append((None, ref))

        result = []
        for act_id, ref in refs_to_parse:
            reference_collector = ReferenceCollector()
            if act_id is not None:
                reference_collector.act = act_id

            self.fill_reference_collector(ref, reference_collector)
            collected_refs = [list(r) for r in reference_collector.iter()]
            if collected_refs:
                full_start_pos, full_end_pos = self.get_subtree_start_and_end_pos(ref)
                collected_refs[0][1] = full_start_pos
                collected_refs[-1][2] = full_end_pos
                result.extend(collected_refs)
        result.sort(key=lambda x: x[1])
        return result

    @classmethod
    def fill_reference_collector(cls, parsed_ref, reference_collector):
        assert parsed_ref.data == 'reference', ref
        for ref_part in parsed_ref.children:
            assert ref_part.data.endswith("_reference")
            ref_type = ref_part.data[:-10]
            for ref_list_item in ref_part.children:
                if not isinstance(ref_list_item, Tree):
                    continue
                relevant_children = [str(c) for c in ref_list_item.children if c.type == ref_type.upper() + "_ID"]
                start_pos, end_pos = cls.get_subtree_start_and_end_pos(ref_list_item)
                if ref_list_item.data == ref_type + '_id':
                    assert len(relevant_children) == 1, ("Wrong amount of IDs in", ref_list_item)
                    reference_collector.add_item(ref_type, relevant_children[0], start_pos, end_pos)
                elif ref_list_item.data == ref_type + '_range':
                    assert len(relevant_children) == 2, ("Wrong amount of IDs in", ref_list_item)
                    reference_collector.add_item(ref_type, (relevant_children[0], relevant_children[1]), start_pos, end_pos)
                elif ref_list_item.data in ("this", "previous"):
                    # TODO: actually handle this case
                    pass
                else:
                    raise ValueError("Unknown type in reference list: {}".format(ref_list_item.data))

    @classmethod
    def update_mutable_ref(cls, mutable_ref, token):
        # TODO: Ranges and  lists
        if token.type == "ABBREVIATION" and mutable_ref.act is None:
            mutable_ref.act = str(token)
        if token.type == "ARTICLE_ID":
            mutable_ref.article = str(token)
        if token.type == "PARAGRAPH_ID":
            mutable_ref.paragraph = str(token)
        if token.type == "ALPHABETIC_POINT_ID":
            mutable_ref.point = str(token)
        if token.type == "NUMERIC_POINT_ID":
            mutable_ref.point = str(token)

    def get_act_references(self, abbreviations):
        for act_ref in self.tree.find_data('act_reference'):
            start_pos, end_pos = self.get_subtree_start_and_end_pos(act_ref.children[0])
            try:
                yield self.get_act_id_from_parse_result(act_ref, abbreviations), start_pos, end_pos
            except AbbreviationNotFoundError:
                pass

    @classmethod
    def get_act_id_from_parse_result(cls, act_ref, abbreviations):
        act_id = act_ref.children[0]
        if act_id.data == 'abbreviated_act_id':
            abbrev = str(act_id.children[0])
            if abbrev not in abbreviations:
                raise AbbreviationNotFoundError()
            return abbreviations[abbrev]
        elif act_id.data == 'act_id':
            assert len(act_id.children) == 4
            return "{} évi {} törvény".format(act_id.children[0], act_id.children[2])
        else:
            raise ValueError('Unknown act id type in parse result: {}'.format(act_id.type))

    @classmethod
    def get_subtree_start_and_end_pos(cls, subtree):
        first_token = subtree
        while not isinstance(first_token, Token):
            first_token = first_token.children[0]
        last_token = subtree
        while not isinstance(last_token, Token):
            last_token = last_token.children[-1]
        return first_token.column - 1, last_token.column + len(last_token) - 2

    def get_new_abbreviations(self):
        for act_ref in self.tree.find_data('act_reference'):
            try:
                from_now_on = next(act_ref.find_data('from_now_on'))
            except StopIteration:
                continue
            abbrev = next(t for t in from_now_on.children if t.type == 'ABBREVIATION')
            yield str(abbrev), self.get_act_id_from_parse_result(act_ref, {})

    def indented_print(self,  tree=None, indent=''):
        if tree is None:
            tree = self.tree
        if isinstance(tree, Token):
            print(indent + tree.type + ":  " + str(tree))
            return
        print(indent + tree.data)
        for c in tree.children:
            self.indented_print(c, indent + '  ')

    def __eq__(self, other):
        return self.s == other.s and self.tree == other.tree


class GrammaticalAnalyzer:
    def __init__(self):
        self.parser = Lark.open('grammar.lark', rel_to=__file__, keep_all_tokens=True)

    def analyze(self, s):
        return GrammaticalAnalysisResult(s, self.parser.parse(s))
