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

from collections import namedtuple

extractors_for_class = {}


def Extractor(extractable_class):
    """Decorator that registers an extractor function.

    Extractor functions can accept a parameter of type 'can_extract_from', and
    yield one or more result objects
    """
    def actual_decorator(fn):
        global extractors_for_class
        if extractable_class not in extractors_for_class:
            extractors_for_class[extractable_class] = []
        extractors_for_class[extractable_class].append(fn)
        return fn
    return actual_decorator
