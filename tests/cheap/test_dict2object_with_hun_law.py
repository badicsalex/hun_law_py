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
import json


from hun_law.structure import \
    BlockAmendment, SubtitleReferenceArticleRelative, RelativePosition, \
    Reference, StructuralReference, \
    Subtitle

from hun_law import dict2object


def test_obj_to_dict_can_handle_specials() -> None:
    test_data = BlockAmendment(
        expected_type=Subtitle,
        expected_id_range=("123", "123"),
        position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "123")),
        replaces=(
            StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "123")),
            Reference(act="Btk.", article="123"),
        )
    )

    the_dict = dict2object.to_dict(test_data, BlockAmendment)

    # This should not throw
    the_json = json.dumps(the_dict)
    reconstructed_dict = json.loads(the_json)

    reconstructed_data = dict2object.to_object(reconstructed_dict, BlockAmendment)

    assert reconstructed_data == test_data
