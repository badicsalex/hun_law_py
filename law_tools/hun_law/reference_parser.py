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
from enum import Enum

# Main act on which all the code was based:
# 61/2009. (XII. 14.) IRM rendelet a jogszabályszerkesztésről
# Along with Appendix 1.


class NotAReferenceError(Exception):
    pass


class RigidReference:
    # 18.-21. §
    # Appendix 1, 4.1.1
    # TODO: split off "A" from "Egyes.*" titles
    # TODO: support not only acts, but reference to the Constitution and Resolutions.
    ACT_RE = re.compile('^(.*)(szóló|című) ([0-9]{4}. évi [IVXLCDM]+. törvény)(.*)$')
    FROM_NOW_ON_RE = re.compile('^ \\(a továbbiakban: ([^)]*)\\)(.*)$')

    def __init__(self, act_id, act_title):
        self.act_id = act_id
        self.act_title = act_title

    @classmethod
    def extract_from_string(cls, reference_string):
        matches = cls.ACT_RE.match(reference_string)
        if not matches:
            raise NotAReferenceError("Unparseable string '{}'.".format(reference_string))
        act_title, _, act_id, rest_of_string = matches.groups()
        # TODO: check -ról -ről in title, if groups(2) == "szolo"

        from_now_on_matches = cls.FROM_NOW_ON_RE.match(rest_of_string)
        if from_now_on_matches:
            from_now_on, rest_of_string = from_now_on_matches.groups()
        else:
            from_now_on = None

        return RigidReference(act_id, act_title), from_now_on, rest_of_string


class StructureReference:
    # Not using the structure classes directly, to later support ranges and sets
    # Also to avoid nasty circular dependencies
    RefType = Enum('RefType', ('ARTICLE', 'PARAGRAPH', 'NUMERIC_POINT', 'ALPHABETIC_POINT', 'SUBPOINT'))
    # 19 § (2): only structural elements can be referenced
    # Appendix 1, 4.2.2.4
    REST_OF_STRING = '(?P<rest_of_string>.*)'

    ARTICLE_ID_PATTERN = '([0-9]+:)?([0-9]+)(/[A-Z])?'
    ARTICLE_PREFIX_PATTERN = '(?P<article>' + ARTICLE_ID_PATTERN + ')\\. ?§ '
    ARTICLE_SINGLE_PATTERN = '(?P<article>' + ARTICLE_ID_PATTERN + ')\\. ?§-[aá]'
    # TODO:
    #ARTICLE_RANGE_PATTERN = '(?P<article_range_first>' + ARTICLE_ID_PATTERN + ')-(?P<article_range_last>' + ARTICLE_ID_PATTERN + ')\\. ?§-[aá]'
    #ARTICLE_PAIR_PATTERN = '(?P<article_pair_first>' + ARTICLE_ID_PATTERN + ')\\. ?§-[aá] és (?P<article_pair_second>' + ARTICLE_ID_PATTERN + ')\\. ?§-[aá]'

    PARAGRAPH_ID_PATTERN = "[0-9]+[a-z]?"
    PARAGRAPH_PREFIX_PATTERN = '\\((?P<paragraph>' + PARAGRAPH_ID_PATTERN + ')\\) bekezdés '
    PARAGRAPH_SINGLE_PATTERN = '\\((?P<paragraph>' + PARAGRAPH_ID_PATTERN + ')\\) bekezdés[eé]'
    # TODO:
    #PARAGRAPH_RANGE_PATTERN = '\\((?P<paragraph_range_first>' + PARAGRAPH_ID_PATTERN + ')\\)-\\((?P<paragraph_range_last>' + PARAGRAPH_ID_PATTERN + ')\\)  bekezdés[eé]'

    NUMERIC_POINT_ID_PATTERN = "[0-9]+[a-z]?"
    NUMERIC_POINT_PREFIX_PATTERN = '(?P<numeric_point>' + NUMERIC_POINT_ID_PATTERN + ')\\. pont '
    NUMERIC_POINT_SINGLE_PATTERN = '(?P<numeric_point>' + NUMERIC_POINT_ID_PATTERN + ')\\. pontj[aá]'

    ALPHABETIC_POINT_ID_PATTERN = "[a-z]?"
    ALPHABETIC_POINT_PREFIX_PATTERN = '(?P<alphabetic_point>' + ALPHABETIC_POINT_ID_PATTERN + ')\\) pont '
    ALPHABETIC_POINT_SINGLE_PATTERN = '(?P<alphabetic_point>' + ALPHABETIC_POINT_ID_PATTERN + ')\\) pontj[aá]'

    SUBPOINT_ID_PATTERN = "[a-z][a-z]?"
    SUBPOINT_SINGLE_PATTERN = '(?P<subpoint>' + SUBPOINT_ID_PATTERN + ')\\) alpontj[aá]'

    REGEXES_TO_TRY = (
        #  1. § (1) bekezdés a) pont ac) alpontja
        re.compile(ARTICLE_PREFIX_PATTERN + PARAGRAPH_PREFIX_PATTERN + ALPHABETIC_POINT_PREFIX_PATTERN + SUBPOINT_SINGLE_PATTERN + REST_OF_STRING),
        #  1. § (1) bekezdés 1. pont c) alpontja
        re.compile(ARTICLE_PREFIX_PATTERN + PARAGRAPH_PREFIX_PATTERN + NUMERIC_POINT_PREFIX_PATTERN + SUBPOINT_SINGLE_PATTERN + REST_OF_STRING),
        #  1. § (1) bekezdés a) pontjának
        re.compile(ARTICLE_PREFIX_PATTERN + PARAGRAPH_PREFIX_PATTERN + ALPHABETIC_POINT_SINGLE_PATTERN + REST_OF_STRING),
        #  1. § (1) bekezdés 4. pontjától
        re.compile(ARTICLE_PREFIX_PATTERN + PARAGRAPH_PREFIX_PATTERN + NUMERIC_POINT_SINGLE_PATTERN + REST_OF_STRING),
        # 4. § (4b) bekezdése
        # 2:34. § (13) bekezdéséhez
        # Appendix: 4.2.2.4.1
        re.compile(ARTICLE_PREFIX_PATTERN + PARAGRAPH_SINGLE_PATTERN + REST_OF_STRING),
        # 56. §-a
        # 1:56/A. §-ával ...
        re.compile(ARTICLE_SINGLE_PATTERN + REST_OF_STRING),
    )

    # Private constructor. Use extract_from_string().
    __private_init_key = object()

    def __init__(self, private_init_key):
        if self.__private_init_key != private_init_key:
            raise RuntimeError("StructureReference may not be created directly")

        # TODO: higher elements. Maybe in different class
        self.referenced_structure = None
        self.article = None
        self.paragraph = None
        self.point = None
        self.subpoint = None

    @classmethod
    def extract_from_string(cls, reference_string):
        for rtt in cls.REGEXES_TO_TRY:
            matches = rtt.fullmatch(reference_string)
            if matches:
                self = cls(cls.__private_init_key)
                matches = matches.groupdict()
                if 'article' in matches:
                    self.article = matches['article']
                    self.referenced_structure = cls.RefType.ARTICLE  # May be overwritten by subsequent code
                if 'paragraph' in matches:
                    self.paragraph = matches['paragraph']
                    self.referenced_structure = cls.RefType.PARAGRAPH  # May be overwritten by subsequent code
                if 'numeric_point' in matches:
                    self.point = matches['numeric_point']
                    self.referenced_structure = cls.RefType.NUMERIC_POINT  # May be overwritten by subsequent code
                if 'alphabetic_point' in matches:
                    self.point = matches['alphabetic_point']
                    self.referenced_structure = cls.RefType.ALPHABETIC_POINT  # May be overwritten by subsequent code
                if 'subpoint' in matches:
                    self.subpoint = matches['subpoint']
                    self.referenced_structure = cls.RefType.SUBPOINT
                return self, matches['rest_of_string']

        raise NotAReferenceError("Reference did not have any matches for string '{}'".format(reference_string))
