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

from typing import Any, Iterable, Tuple, Type, Sequence
import multiprocessing

from . import extractors_for_class

# Yes, this is a hacky way to get all extractors, but you don't get to
# judge me, pylint.
# pylint: disable=unused-import
from . import file, kozlonyok_hu_downloader, magyar_kozlony, pdf, act


# This hack is needed instead of a lambda or wrapped function, since neither of these
# can be pickled by default, which in turn is needed for multiprocessing's map()
class _DoExtractionWrapper:
    def __init__(self, result_classes: Tuple[Type, ...]):
        self.result_classes = result_classes

    def __call__(self, o: Any) -> Iterable[Any]:
        # Listify, because a generator result cannot be pickled.
        return list(self.do_work((o, ), self.result_classes))

    @staticmethod
    def do_work(objects: Iterable[Any], result_classes: Tuple[Type, ...] = ()) -> Iterable[Any]:
        global extractors_for_class
        queue = list(objects)  # simple copy, or listify if not list
        while queue:
            data = queue.pop()
            if data.__class__ in result_classes:
                yield data
            else:
                for extractor_fn in extractors_for_class[data.__class__]:
                    for extracted in extractor_fn(data):
                        queue.append(extracted)


def _do_extraction_multithreaded(objects: Iterable[Any], result_classes: Tuple[Type, ...], workers: int) -> Iterable[Any]:
    with multiprocessing.Pool(workers) as pool:
        for result in pool.imap_unordered(_DoExtractionWrapper(result_classes), objects):
            yield from result


def do_extraction(objects: Sequence[Any], result_classes: Tuple[Type, ...] = (), *, workers: int = 1) -> Iterable[Any]:
    """Processes all objects, and returns the end result processed objects."""
    if workers > 1 and len(objects) > 1:
        yield from _do_extraction_multithreaded(objects, result_classes, min(workers, len(objects)))
    else:
        yield from _DoExtractionWrapper.do_work(objects, result_classes)
