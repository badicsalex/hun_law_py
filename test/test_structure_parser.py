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

import sys
import os

import pytest

from hun_law.extractors.kozlonyok_hu_downloader import KozlonyToDownload
from hun_law.extractors.all import do_extraction
from hun_law.cache import init_cache
from hun_law.structure import Act, Article, Book, Title, Chapter, Subtitle, QuotedBlock


def parse_single_kozlony(year, issue):
    init_cache(os.path.join(os.path.join(os.path.dirname(__file__), '..'), 'cache'))
    extracted = do_extraction([KozlonyToDownload(year, issue)])
    return extracted


def test_end_to_end_2013_31():
    # The 2013 Ptk is a great way to test high level structure
    # parsing, because it has  a ton of Books, chapters, etc.,
    # in various configurations.
    acts = [a for a in parse_single_kozlony(2013, 31) if isinstance(a, Act)]
    assert len(acts) == 1, "Issue 2013/31 of Magyar Kozlony contains a single Act"
    ptk = acts[0]

    assert ptk.identifier == "2013. évi V. törvény"
    assert ptk.subject == "a Polgári Törvénykönyvről"

    books = [b for b in ptk.children if isinstance(b, Book)]
    assert len(books) == 8, "Ptk contains 8 Books"

    articles = ptk.articles
    articles_per_book = [6, 55, 406, 244, 187, 592, 100, 6]
    for booknum, apb in enumerate(articles_per_book, 1):
        article_prefix = "{}:".format(booknum)
        articles_in_book = [a for a in articles if a.identifier.startswith(article_prefix)]
        assert len(articles_in_book) == apb, "Book {} contains {} articles".format(booknum, apb)

    assert len(articles) == sum(articles_per_book), "All articles belong to a book"

    target_titles = [t for t in ptk.children if isinstance(t, Title) and int(t.identifier) == 36]
    assert len(target_titles) == 1, "There is exactly one title with number XXVI (in book 6)"
    assert target_titles[0].title.upper() == "A KÖTELEZETTSÉGVÁLLALÁS KÖZÉRDEKŰ CÉLRA"

    target_chapters = [c for c in ptk.children if isinstance(c, Chapter) and int(c.identifier) == 74]
    assert len(target_chapters) == 1, "There is exactly one chapter with number LXXIV (in book 6)"
    assert target_chapters[0].title == "Felelősség az állatok károkozásáért", "Subtitle is correct. Also, the \"ő\" is correct"

    assert ptk.article('7:65').title == "Dédszülő és a dédszülő leszármazójának öröklése"


def test_end_to_end_2013_185():
    # This test tests two things: a rather large MK issue with lots  of small Acts,
    # so the Act separation in the Kozlony Extractor. The other is that there are
    # A lot of real sub-article element cases in these acts.
    acts = {a.identifier: a for a in parse_single_kozlony(2013, 185) if isinstance(a, Act)}
    assert len(acts) == 11, "Issue 2013/185 of Magyar Kozlony contains 11 separate Acts"

    assert acts["2013. évi CLXXV. törvény"].article(3).paragraph(1).point('a').subpoint('ad').text == "anyjának születési családi és utónevét,"
    assert acts["2013. évi CLXXV. törvény"].article(5).paragraph().text is not None

    # Typical buggy value: "pontjában szereplő adatokat, g) a gyámhatóság", because of the previous line.
    assert acts["2013. évi CLXXV. törvény"].article(6).paragraph(2).point('g').intro == "a gyámhatóság", \
        "Indentation matters in point header parsing."
    assert acts["2013. évi CLXXV. törvény"].article(6).paragraph(2).point('g').subpoint('gb').text == \
        "a gondnokság alá helyezési per megindítása, a gondnokság felülvizsgálata, a választójogból " \
        "való kizárás vagy a választójogból való kizárás megszüntetése iránti per megindítása miatt a 3. § " \
        "(1) bekezdésében szereplő adatokat,"

    assert acts["2013. évi CLXXVI. törvény"].article(36).paragraph(1).wrap_up == "való megfelelést szolgálja."

    # This Act has super-retarded Article Titles, so test the parsing (or fixups)
    assert acts["2013. évi CLXXVII. törvény"].article(5).title == ""
    assert acts["2013. évi CLXXVII. törvény"].article(58).title == "A Ptk. 7:10–7:24. §-ához"
    assert acts["2013. évi CLXXVII. törvény"].article(59).title == "A Ptk. 7:28. § (3) és (4) bekezdéséhez"

    assert acts["2013. évi CLXXVIII. törvény"].article(1).paragraph(1).children_type == QuotedBlock

    assert acts["2013. évi CLXXIX. törvény"].article(1).paragraph(29).intro == "Hatályát veszti az Flt.", \
        "Relatively large number of paragraphs are correctly parsed"
