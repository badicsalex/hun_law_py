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

from hun_law.structure import Reference, MutableReference


class GrammaticalAnalysisResult:
    def __init__(self, s, tree):
        self.s = s
        self.tree = tree

    def get_references(self):
        for ref_container in self.tree.find_data('compound_reference'):
            mutable_ref = MutableReference()
            if len(ref_container.children) == 1:
                ref = ref_container.children[0]
                if ref.data == 'act_reference':
                    continue
            else:
                act_ref, ref = ref_container.children
                assert act_ref.data == 'act_reference'
                mutable_ref.act = self.get_act_id_from_parse_result(act_ref)
            assert ref.data == 'reference', ref
            for subtree in ref_container.iter_subtrees():
                for token in subtree.children:
                    if isinstance(token, Token):
                        self.update_mutable_ref(mutable_ref, token)
            start_pos, end_pos = self.get_subtree_start_and_end_pos(ref)
            yield (Reference(mutable_ref), start_pos, end_pos)

    @classmethod
    def update_mutable_ref(cls, mutable_ref, token):
        if token.type == "ABBREVIATION" and mutable_ref.act is None:
            mutable_ref.act = str(token)
        if token.type == "ARTICLE_ID":
            mutable_ref.article = str(token)

    def get_act_references(self):
        for act_ref in self.tree.find_data('act_reference'):
            start_pos, end_pos = self.get_subtree_start_and_end_pos(act_ref.children[0])
            yield self.get_act_id_from_parse_result(act_ref), start_pos, end_pos

    @classmethod
    def get_act_id_from_parse_result(cls, act_ref):
        act_id = act_ref.children[0]
        if act_id.data == 'abbreviated_act_id':
            return str(act_id.children[0])
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
