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

import os
import json

cache_dir_path = None


class CacheObject:
    def __init__(self, name):
        if cache_dir_path is None:
            raise RuntimeError("Cache not initialized yet")
        self.filename = os.path.join(cache_dir_path, name)

    def exists(self):
        return os.path.exists(self.filename)

    def write_bytes(self, data):
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        with open(self.filename, 'wb') as f:
            f.write(data)

    def read_json(self):
        with open(self.filename, 'r') as f:
            return json.load(f)

    def write_json(self, data):
        with open(self.filename, 'w') as f:
            # TODO: Indenting for debuggging purposes, this will not
            # create minimal files. This means something like 15% bigger.
            json.dump(data, f, indent=2, sort_keys=True)

    def get_filename(self):
        return self.filename


def init_cache(cache_dir):
    global cache_dir_path
    cache_dir_path = cache_dir
    os.makedirs(cache_dir, exist_ok=True)
