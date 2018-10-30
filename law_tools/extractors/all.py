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

from . import extractors_for_class


def do_extraction(to_be_processed_objects):
    """Processes all objects, and returns the end result processed objects."""
    global extractors_for_class
    queue = list(to_be_processed_objects)  # simple copy, or listify if not list
    result = []
    while queue:
        data = queue.pop()
        if data.__class__ not in extractors_for_class:
            result.append(data)
        else:
            for extractor_fn in extractors_for_class[data.__class__]:
                for extracted in extractor_fn(data):
                    queue.append(extracted)
    return result
