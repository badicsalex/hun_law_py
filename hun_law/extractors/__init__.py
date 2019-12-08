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

from collections import namedtuple
from typing import Dict, Callable, List, Type, Any

ExtractorFn = Callable[[Any], Any]

extractors_for_class: Dict[Type, List[ExtractorFn]] = {}


def Extractor(extractable_class: Type) -> Callable:
    """Decorator that registers an extractor function.

    Extractor functions can accept a parameter of type 'can_extract_from', and
    yield one or more result objects
    """
    def actual_decorator(fn: ExtractorFn) -> ExtractorFn:
        global extractors_for_class
        if extractable_class not in extractors_for_class:
            extractors_for_class[extractable_class] = []
        extractors_for_class[extractable_class].append(fn)
        return fn
    return actual_decorator
