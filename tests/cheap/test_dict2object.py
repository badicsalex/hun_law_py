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
from typing import Tuple, List, Type, Any, Union, Optional
import gc
from enum import Enum

import pytest
import attr

from hun_law.dict2object import to_object, to_dict, TypeOrGeneric


@attr.s(slots=True, frozen=True, auto_attribs=True)
class Simple:
    i: int
    s: str


@attr.s(slots=True, frozen=True, auto_attribs=True)
class Containers:
    c: Tuple[int, int]
    l: List[str]


@attr.s(slots=True, frozen=True, auto_attribs=True)
class Defaults:
    i: int
    s: str = 'default'


@attr.s(slots=True, frozen=True, auto_attribs=True)
class Noinit:
    i: int
    s: str = attr.ib(init=False)

    @s.default
    def s_default(self) -> str:
        return str(self.i)


@attr.s(slots=True, frozen=True, auto_attribs=True)
class Complex:
    i: int
    s: Simple


@attr.s(slots=True, frozen=True, auto_attribs=True)
class Recursive:
    i: int
    r: List['Recursive']


@attr.s(slots=True, frozen=True, auto_attribs=True)
class SubclassesA:
    i: int


@attr.s(slots=True, frozen=True, auto_attribs=True)
class SubclassesAA(SubclassesA):
    j: int


@attr.s(slots=True, frozen=True, auto_attribs=True)
class SubclassesAAA(SubclassesAA):
    k: int


@attr.s(slots=True, frozen=True, auto_attribs=True)
class SubclassesAB(SubclassesA):
    j: int


@attr.s(slots=True, frozen=True, auto_attribs=True)
class SubclassesB:
    x: int


@attr.s(slots=True, frozen=True, auto_attribs=True)
class SubclassesBA(SubclassesB):
    y: int


@attr.s(slots=True, frozen=True, auto_attribs=True)
class ProtectedFields:
    public: str
    _protected: str


class MyEnum(Enum):
    VALUE1 = 1
    VALUE_WHAT = 1337
    ENUM_NAMES_YEEE = 25252


attr.resolve_types(Recursive)

# Needed for attr.s(slots=True), and __subclasses__ to work correctly.
gc.collect()

TEST_DATA: List[Tuple[TypeOrGeneric, Any, Any]] = [
    (int, 5, 5),
    (str, 'lel', 'lel'),
    (bool, True, True),
    (type(None), None, None),
    (
        List[int],
        [2, 3, 4],
        [2, 3, 4]
    ),
    (
        List[List[int]],
        [[2], [3, 4]],
        [[2], [3, 4]]
    ),
    (
        Tuple[int, str, int],
        (2, '1234', 4),
        [2, '1234', 4]
    ),
    (
        Tuple[int, Tuple[str, int], int],
        (2, ('1234', 5), 4),
        [2, ['1234', 5], 4]
    ),
    (
        Tuple[int, List[Tuple[str, int]], int],
        (2, [('1234', 5), ('abcd', 15)], 4),
        [2, [['1234', 5], ['abcd', 15]], 4]
    ),
    (
        Tuple[int, ...],
        (2, 3, 4),
        [2, 3, 4]
    ),
    (
        Tuple[int, Tuple[Tuple[str, int], ...], int],
        (2, (('1234', 5), ('abcd', 15)), 4),
        [2, [['1234', 5], ['abcd', 15]], 4]
    ),
    (
        Simple,
        Simple(1, '1234'),
        {'i': 1, 's': '1234'},
    ),
    (
        Containers,
        Containers((1, 2), ['a', 'b', 'c']),
        {'c': [1, 2], 'l': ['a', 'b', 'c']},
    ),
    (
        Defaults,
        Defaults(1),
        {'i': 1},
    ),
    (
        Defaults,
        Defaults(1, 'no'),
        {'i': 1, 's': 'no'},
    ),
    (
        Noinit,
        Noinit(1),
        {'i': 1},
    ),
    (
        Complex,
        Complex(5, Simple(1, '1234')),
        {'i': 5, 's': {'i': 1, 's': '1234'}},
    ),
    (
        Recursive,
        Recursive(5, [Recursive(6, []), Recursive(7, [Recursive(8, [])])]),
        {'i': 5, 'r': [{'i': 6, 'r': []}, {'i': 7, 'r': [{'i': 8, 'r': []}]}]},
    ),
    (
        Union[str, int],
        5,
        5
    ),
    (
        Union[str, int],
        'a',
        'a'
    ),
    (
        Union[str, List[int], Simple],
        [1, 2, 3],
        [1, 2, 3]
    ),
    (
        Union[str, List[int], Simple],
        Simple(1, 'a'),
        {'i': 1, 's': 'a'}
    ),
    (
        Union[Simple, Defaults],
        Simple(1, 'a'),
        {'i': 1, 's': 'a', '__type__': 'Simple'}
    ),
    (
        Union[Simple, Defaults],
        Defaults(1),
        {'i': 1, '__type__': 'Defaults'}
    ),
    (
        Tuple[Union[int, str], ...],
        (1, 'a', 2),
        [1, 'a', 2],
    ),
    (
        Tuple[SubclassesA, ...],
        (SubclassesA(1), SubclassesAA(1, 2), SubclassesAAA(5, 6, 7), SubclassesAB(2, 3)),
        [
            {'i': 1, '__type__': 'SubclassesA'},
            {'i': 1, 'j': 2, '__type__': 'SubclassesAA'},
            {'i': 5, 'j': 6, 'k': 7, '__type__': 'SubclassesAAA'},
            {'i': 2, 'j': 3, '__type__': 'SubclassesAB'}
        ],
    ),
    (
        Tuple[Union[SubclassesA, SubclassesB, str], ...],
        (SubclassesA(1), SubclassesAB(2, 3), 'no', SubclassesBA(5, 6)),
        [
            {'__type__': 'SubclassesA', 'i': 1},
            {'__type__': 'SubclassesAB', 'i': 2, 'j': 3},
            'no',
            {'__type__': 'SubclassesBA', 'x': 5, 'y': 6}
        ]
    ),
    (
        Tuple[Union[SubclassesA, SubclassesAB, str], ...],
        (SubclassesA(1), SubclassesAB(2, 3), SubclassesAAA(3, 4, 5), 'no'),
        [
            {'__type__': 'SubclassesA', 'i': 1},
            {'__type__': 'SubclassesAB', 'i': 2, 'j': 3},
            {'i': 3, 'j': 4, 'k': 5, '__type__': 'SubclassesAAA'},
            'no',
        ]
    ),
    (
        MyEnum,
        MyEnum.ENUM_NAMES_YEEE,
        'ENUM_NAMES_YEEE',
    ),
    (
        Union[int, MyEnum, Tuple[int]],
        MyEnum.VALUE_WHAT,
        'VALUE_WHAT',
    ),
    (
        Type[SubclassesA],
        SubclassesAAA,
        'SubclassesAAA'
    ),
    (
        Type[Union[SubclassesB, SubclassesAA]],
        SubclassesAA,
        'SubclassesAA'
    ),
    (
        ProtectedFields,
        ProtectedFields('a', 'b'),
        {'public': 'a', '_protected': 'b'}
    )
]


@pytest.mark.parametrize("cls,obj,dct", TEST_DATA)  # type: ignore
def test_to_dict(cls: Type, obj: Any, dct: Any) -> None:
    assert to_dict(obj, cls) == dct


@pytest.mark.parametrize("cls,obj,dct", TEST_DATA)  # type: ignore
def test_to_obj(cls: Type, obj: Any, dct: Any) -> None:
    assert to_object(dct, cls) == obj


@pytest.mark.parametrize("cls,obj,dct", TEST_DATA)  # type: ignore
def test_optional(cls: Type, obj: Any, dct: Any) -> None:
    assert to_dict(obj, Optional[cls]) == dct
    assert to_object(dct, Optional[cls]) == obj
    assert to_dict(None, Optional[cls]) is None
    assert to_object(None, Optional[cls]) is None


@pytest.mark.parametrize("cls,obj,dct", TEST_DATA)  # type: ignore
def test_as_field(cls: Type, obj: Any, dct: Any) -> None:
    @attr.s(slots=True, frozen=True, auto_attribs=True)
    class Tester:
        field: cls  # type: ignore
    obj = Tester(obj)
    dct = {'field': dct}

    assert to_dict(obj, Tester) == dct
    assert to_object(dct, Tester) == obj
