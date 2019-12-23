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

import gzip
import os
import json
from typing import Any

cache_dir_path = None


class CacheObject:
    def __init__(self, name: str):
        if cache_dir_path is None:
            raise RuntimeError("Cache not initialized yet")
        self.filename: str = os.path.join(cache_dir_path, name)

    def exists(self) -> bool:
        return os.path.exists(self.filename)

    def write_bytes(self, data: bytes) -> None:
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        with open(self.filename, 'wb') as f:
            f.write(data)

    def read_json(self) -> Any:
        with gzip.open(self.filename, 'rt') as f:
            return json.load(f)

    def write_json(self, data: Any) -> None:
        with gzip.open(self.filename, 'wt') as f:
            json.dump(data, f, separators=(',', ':'))

    def get_filename(self) -> str:
        return self.filename

    def size_on_disk(self) -> int:
        if not self.exists():
            return 0
        return os.path.getsize(self.filename)


def init_cache(cache_dir: str) -> None:
    global cache_dir_path
    cache_dir_path = cache_dir
    os.makedirs(cache_dir, exist_ok=True)
