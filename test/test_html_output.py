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

from hun_law.extractors.kozlonyok_hu_downloader import KozlonyToDownload
from hun_law.extractors.all import do_extraction
from hun_law.cache import init_cache
from hun_law.output.html import generate_html_body_for_act
from hun_law.structure import Act


def parse_single_kozlony(year, issue):
    init_cache(os.path.join(os.path.join(os.path.dirname(__file__), '..'), 'cache'))
    extracted = do_extraction([KozlonyToDownload(year, issue)])
    return extracted


def test_html_output_ptk():
    # Just simply test if html output works.
    acts = [a for a in parse_single_kozlony(2013, 31) if isinstance(a, Act)]
    assert len(acts) == 1, "Issue 2013/31 of Magyar Kozlony contains a single Act"
    ptk = acts[0]

    body = generate_html_body_for_act(ptk)
    all_links = body.findall('.//a')
    assert len(all_links) > 50


def test_html_output_2018_123():
    # Just simply test if html output works on modern MK issues
    acts = {a.identifier: a for a in parse_single_kozlony(2018, 123) if isinstance(a, Act)}
    assert len(acts) == 6, "Issue 2018/123 of Magyar Kozlony contains 6 separate Acts"

    for act_id, act in acts.items():
        body = generate_html_body_for_act(act)
        all_links = body.findall('.//a')
        assert len(all_links) > 1
