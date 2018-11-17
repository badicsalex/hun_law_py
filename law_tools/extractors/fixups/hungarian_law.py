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


# The whole module is a bunch of fixups to existing Acts, that aren't
# well-formed enough to be parsed by the parser out-of-the-box

from .common import add_fixup, replace_line_content, add_empty_line_after, ptke_article_header_fixer

# Title IV not found otherwise
add_fixup("2013. évi V. törvény", add_empty_line_after("A SZERZŐDÉS ÁLTALÁNOS SZABÁLYAI"))

# Mistyped quoting
add_fixup("2013. évi CCLII. törvény", replace_line_content(
    ",,(1) Az egyesület jogutód nélküli megszűnése esetén a hitelezők követeléseinek kiegyenlítése után fennmaradó",
    "„(1) Az egyesület jogutód nélküli megszűnése esetén a hitelezők követeléseinek kiegyenlítése után fennmaradó"
))
add_fixup("2013. évi CCLII. törvény", replace_line_content(
    ",,(3) A nyilvántartó bíróság jogszabályban meghatározott szervezetnek juttatja a vagyont, ha az alapító okirat, vagy",
    "„(3) A nyilvántartó bíróság jogszabályban meghatározott szervezetnek juttatja a vagyont, ha az alapító okirat, vagy"
))
# Invalid Rigid reference
add_fixup("2013. évi CCLII. törvény", replace_line_content(
    "(4) A 6:198. § (3) bekezdése a következő szöveggel lép hatályba:",
    "(4) A Ptk. 6:198. § (3) bekezdése a következő szöveggel lép hatályba:"
))

# Article titles starting before the article sign.
# See ptke_article_header_fixer source for details
add_fixup("2013. évi CLXXVII. törvény", ptke_article_header_fixer)

# The "Felhatalmazás" line is not actually part of the amendment, it's just context.
# TODO: I don't know what to actually do about this. Maybe do automatically parse these junk things?
# Only if this needs to be fixed more than once. It may even cause  problems anyway, who knows.
add_fixup("2015. évi CIV. törvény", replace_line_content(
    "„Felhatalmazás",
    "Felhatalmazás"
))
add_fixup("2015. évi CIV. törvény", replace_line_content(
    "28. § Felhatalmazást kap a Kormány, hogy e törvény alapján",
    "„28. § Felhatalmazást kap a Kormány, hogy e törvény alapján"
))

# Invalid quoting all over the place
add_fixup("2016. évi CLXXIX. törvény", replace_line_content(
    "tizenöt nappal követő időpontra hívják össze.”",
    "tizenöt nappal követő időpontra hívják össze."
))
add_fixup("2016. évi CLXXXIV. törvény", replace_line_content(
    "„143. § (1) Árvák kiegészítő támogatására jogosult az állomány elhunyt tagjának – ideértve a 224. § (3) bekezdése",
    "143. § (1) Árvák kiegészítő támogatására jogosult az állomány elhunyt tagjának – ideértve a 224. § (3) bekezdése",
))
add_fixup("2016. évi CLXXXIV. törvény", replace_line_content(
    "a) az önkéntes tartalékos katona hivatásos, szerződéses, honvéd tisztjelölt vagy honvéd altiszt-jelölt szolgálati",
    "„a) az önkéntes tartalékos katona hivatásos, szerződéses, honvéd tisztjelölt vagy honvéd altiszt-jelölt szolgálati",
))

