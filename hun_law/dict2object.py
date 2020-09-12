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
from typing import Type, List, Tuple, Union, Dict, Any, Iterable, Set
from abc import ABC, abstractmethod
from inspect import isclass

import attr

# TODO: this should be a proper Union of real and generic types.
TypeOrGeneric = Any


def is_list_type(t: TypeOrGeneric) -> bool:
    return t is list or isinstance(t, type(List[int])) and isclass(t.__origin__) and issubclass(t.__origin__, list)  # type: ignore


def is_tuple_type(t: TypeOrGeneric) -> bool:
    return t is tuple or isinstance(t, type(Tuple[int])) and isclass(t.__origin__) and issubclass(t.__origin__, tuple)  # type: ignore


def is_union_type(t: TypeOrGeneric) -> bool:
    return t is Union or isinstance(t, type(Union[int, str])) and t.__origin__ == Union  # type: ignore


def get_subclasses_recursive(cls: TypeOrGeneric) -> Iterable[TypeOrGeneric]:
    yield cls
    if cls in (int, float, str, type(None)):
        return
    if is_list_type(cls) or is_tuple_type(cls):
        return
    if isclass(cls):
        for candidate in cls.__subclasses__():
            yield from get_subclasses_recursive(candidate)


class Converter(ABC):
    __slots__ = ()

    # __init__ and setup are different steps, since we need the
    # new converter object already cached in the factory to
    # properly handle recursion.
    @abstractmethod
    def setup(self, the_type: TypeOrGeneric, converter_factory: 'ConverterFactory') -> None:
        pass

    @abstractmethod
    def to_object(self, data: Any) -> Any:
        pass

    @abstractmethod
    def to_dict(self, data: Any) -> Any:
        pass

    @abstractmethod
    def input_types(self) -> Iterable[Type]:
        pass

    @abstractmethod
    def converted_type(self) -> Type:
        pass


class NoopConverter(Converter):
    __slots__ = ('the_type',)
    the_type: Type

    def setup(self, the_type: TypeOrGeneric, converter_factory: 'ConverterFactory') -> None:
        self.the_type = the_type

    def to_object(self, data: Any) -> Any:
        return data

    def to_dict(self, data: Any) -> Any:
        return data

    def input_types(self) -> Iterable[Type]:
        return (self.the_type,)

    def converted_type(self) -> Type:
        return self.the_type


class ListConverter(Converter):
    __slots__ = ('subconverter',)
    subconverter: Converter

    def setup(self, the_type: TypeOrGeneric, converter_factory: 'ConverterFactory') -> None:
        if len(the_type.__args__) != 1:
            raise TypeError("ListConverter cannot handle non-typed lists")
        contained_type = the_type.__args__[0]
        self.subconverter = converter_factory.create(contained_type)

    def to_object(self, data: Any) -> Any:
        return list(self.subconverter.to_object(v) for v in data)

    def to_dict(self, data: Any) -> Any:
        return list(self.subconverter.to_dict(v) for v in data)

    def input_types(self) -> Iterable[Type]:
        return (list,)

    def converted_type(self) -> Type:
        return list


class VarLenTupleConverter(Converter):
    __slots__ = ('subconverter',)
    subconverter: Converter

    def setup(self, the_type: TypeOrGeneric, converter_factory: 'ConverterFactory') -> None:
        contained_type = the_type.__args__[0]
        self.subconverter = converter_factory.create(contained_type)

    def to_object(self, data: Any) -> Any:
        return tuple(self.subconverter.to_object(v) for v in data)

    def to_dict(self, data: Any) -> Any:
        return list(self.subconverter.to_dict(v) for v in data)

    def input_types(self) -> Iterable[Type]:
        return (tuple,)

    def converted_type(self) -> Type:
        return list


class TupleConverter(Converter):
    __slots__ = ('subconverters',)
    subconverters: Tuple[Converter, ...]

    def setup(self, the_type: TypeOrGeneric, converter_factory: 'ConverterFactory') -> None:
        self.subconverters = tuple(converter_factory.create(contained_type) for contained_type in the_type.__args__)

    def to_object(self, data: Any) -> Any:
        return tuple(converter.to_object(v) for converter, v in zip(self.subconverters, data))

    def to_dict(self, data: Any) -> Any:
        return list(converter.to_dict(v) for converter, v in zip(self.subconverters, data))

    def input_types(self) -> Iterable[Type]:
        return (tuple,)

    def converted_type(self) -> Type:
        return list


class AttrsClassConverter(Converter):
    __slots__ = ('the_class', 'subconverters',)
    the_class: TypeOrGeneric
    subconverters: Dict[str, Converter]

    def setup(self, the_type: TypeOrGeneric, converter_factory: 'ConverterFactory') -> None:
        self.the_class = the_type
        self.subconverters = {}
        for field in attr.fields(self.the_class):
            if not field.init:
                continue
            assert field.type is not None
            self.subconverters[field.name] = converter_factory.create(field.type)

    def to_object(self, data: Any) -> Any:
        converted_data = {k: self.subconverters[k].to_object(v) for k, v in data.items() if k != '__type__'}
        return self.the_class(**converted_data)

    def to_dict(self, data: Any) -> Any:
        dct = attr.asdict(
            data,
            recurse=False,
            filter=lambda a, v: a.init and v != a.default,
        )
        return {k: self.subconverters[k].to_dict(v) for k, v in dct.items()}

    def input_types(self) -> Iterable[Type]:
        return (self.the_class,)

    def converted_type(self) -> Type:
        return dict


class DictDisambiguator:
    __slots__ = ('subconverters_to_dict', 'subconverters_to_obj')
    subconverters_to_dict: Dict[Type, Converter]
    subconverters_to_obj: Dict[str, Converter]

    def __init__(self, subconverters: Iterable[Converter]):
        self.subconverters_to_dict = {}
        self.subconverters_to_obj = {}
        for subconverter in subconverters:
            assert subconverter.converted_type() is dict
            for input_type in subconverter.input_types():
                type_name = input_type.__name__
                if type_name in self.subconverters_to_obj:
                    # If you're reading this comment because you ran into this error, and
                    # you are using attr.s classes with slots=True, be sure to call gc.collect()
                    # after defining all classes. See https://github.com/python-attrs/attrs/issues/407
                    raise TypeError("Type name collision within Union (or subclasses): {}".format(type_name))
                self.subconverters_to_obj[type_name] = subconverter
                self.subconverters_to_dict[input_type] = subconverter

    def can_convert_to_dict(self, data: Any) -> bool:
        return type(data) in self.subconverters_to_dict

    def to_object(self, data: Any) -> Any:
        if len(self.subconverters_to_obj) == 1:
            return next(iter(self.subconverters_to_obj.values())).to_object(data)
        return self.subconverters_to_obj[data['__type__']].to_object(data)

    def to_dict(self, data: Any) -> Any:
        result = self.subconverters_to_dict[type(data)].to_dict(data)
        if len(self.subconverters_to_dict) > 1:
            result['__type__'] = type(data).__name__
        return result


class UnionConverter(Converter):
    __slots__ = ('dict_disambiguator', 'subconverters_to_dict', 'subconverters_to_obj')
    subconverters_to_dict: Dict[Type, Converter]
    subconverters_to_obj: Dict[Type, Converter]
    dict_disambiguator: DictDisambiguator

    def setup(self, the_type: TypeOrGeneric, converter_factory: 'ConverterFactory') -> None:
        raise RuntimeError("UnionConverter.setup() called instead of setup_multi()")

    def setup_multi(self, the_type: Iterable[Type], converter_factory: 'ConverterFactory') -> None:
        # TODO: Assert that the_type is a list here
        self.subconverters_to_dict = {}
        self.subconverters_to_obj = {}
        dict_converters = []
        all_possible_types: Set[Type] = set()
        for contained_type in the_type:
            all_possible_types.update(get_subclasses_recursive(contained_type))

        for contained_type in all_possible_types:
            subconverter = converter_factory.create(contained_type, handle_subclasses=False)
            if subconverter.converted_type() is dict:
                dict_converters.append(subconverter)
            else:
                self.add_typed_subconverter(subconverter)
        self.dict_disambiguator = DictDisambiguator(dict_converters)

    def add_typed_subconverter(self, subconverter: Converter) -> None:
        if subconverter.converted_type() in self.subconverters_to_dict:
            raise TypeError(
                "Cannot disambiguate between {} and {} in Union"
                .format(subconverter, self.subconverters_to_dict[subconverter.converted_type()])
            )
        for t in subconverter.input_types():
            self.subconverters_to_dict[t] = subconverter
        self.subconverters_to_obj[subconverter.converted_type()] = subconverter

    def to_object(self, data: Any) -> Any:
        if isinstance(data, dict):
            return self.dict_disambiguator.to_object(data)
        return self.subconverters_to_obj[type(data)].to_object(data)

    def to_dict(self, data: Any) -> Any:
        if self.dict_disambiguator.can_convert_to_dict(data):
            return self.dict_disambiguator.to_dict(data)
        if type(data) not in self.subconverters_to_dict:
            raise TypeError(
                "Data is of unknown type {}. (Known types:{})"
                .format(type(data), tuple(self.subconverters_to_dict.keys()))
            )
        return self.subconverters_to_dict[type(data)].to_dict(data)

    def input_types(self) -> Iterable[Type]:
        raise TypeError("Nesting Unions is not supported")

    def converted_type(self) -> Type:
        raise TypeError("Nesting Unions is not supported")


class ConverterFactory:
    __slots__ = ('cache',)
    cache: Dict[Tuple[TypeOrGeneric, bool], Converter]

    def __init__(self) -> None:
        self.cache = {}

    def create(self, the_type: TypeOrGeneric, *, handle_subclasses: bool = True) -> Converter:
        cache_key = (the_type, handle_subclasses)
        if cache_key in self.cache:
            return self.cache[cache_key]

        converter: Converter
        if the_type in (int, float, str, type(None)):
            converter = NoopConverter()
        elif is_list_type(the_type):
            converter = ListConverter()
        elif is_tuple_type(the_type):
            if ... in the_type.__args__:
                converter = VarLenTupleConverter()
            else:
                converter = TupleConverter()
        elif handle_subclasses and isclass(the_type) and the_type.__subclasses__():
            converter = UnionConverter()
            the_types = [the_type]
        elif attr.has(the_type):
            converter = AttrsClassConverter()
        elif is_union_type(the_type):
            converter = UnionConverter()
            the_types = the_type.__args__
        else:
            raise TypeError("Dict2object cannot handle type {}".format(the_type))

        self.cache[cache_key] = converter
        if isinstance(converter, UnionConverter):
            converter.setup_multi(the_types, self)
        else:
            converter.setup(the_type, self)
        return converter


def to_object(data: Any, the_type: TypeOrGeneric) -> Any:
    return get_converter(the_type).to_object(data)


def to_dict(data: Any, the_type: TypeOrGeneric) -> Any:
    return get_converter(the_type).to_dict(data)


def get_converter(the_type: TypeOrGeneric) -> Converter:
    return ConverterFactory().create(the_type)
