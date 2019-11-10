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
from hun_law.structure import \
    Act, Book, Part, Title, Chapter, Subtitle, \
    Article, QuotedBlock, AlphabeticPoint, BlockAmendment, Paragraph


def parse_single_kozlony(year, issue):
    init_cache(os.path.join(os.path.join(os.path.dirname(__file__), '..', '..'), 'cache'))
    extracted = do_extraction([KozlonyToDownload(year, issue)], (Act, ))
    return extracted


def test_end_to_end_2010_181():
    # The  first MK to use "The new format" is 2009/117.
    # But subtitles don't have numbers consistently, until the
    # 2010 CXXX Act about legislation.

    # Of course this whole project is way easier because of that Act
    # anyway, because it requires all in-force laws to be non-contradictory
    # To eachother.

    # The test is mainly a format-compatibility check.
    acts = {a.identifier: a for a in parse_single_kozlony(2010, 181) if isinstance(a, Act)}
    assert len(acts) == 6, "Issue 2010/181 of Magyar Kozlony contains 6 separate Acts"

    # !!!!
    acts["2010. évi CXXX. törvény"].article(25).paragraph(1).text == \
        "A Magyar Köztársaság hivatalos lapja a Magyar Közlöny. A Magyar Közlönyt a kormányzati portálon történő" \
        "elektronikus dokumentumként való közzététellel kell kiadni, melynek szövegét hitelesnek kell tekinteni."


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

    target_parts = [p for p in ptk.children if isinstance(p, Part) and int(p.identifier) == 2]
    assert len(target_parts) == 7, "There are exactly 7 \"Part 2\"s in the Act (almost one for each Book)"
    assert target_parts[4].title.upper() == "A SZERZŐDÉS ÁLTALÁNOS SZABÁLYAI"

    target_chapters = [c for c in ptk.children if isinstance(c, Chapter) and int(c.identifier) == 74]
    assert len(target_chapters) == 1, "There is exactly one chapter with number LXXIV (in book 6)"
    assert target_chapters[0].title == "Felelősség az állatok károkozásáért", "Subtitle is correct. Also, the \"ő\" is correct"

    assert ptk.article('7:65').title == "Dédszülő és a dédszülő leszármazójának öröklése"


def test_end_to_end_2013_67():
    # This issue has empty pages, with which we had problems.
    # It also has a document, where words are not correctly parsed into lines,
    # because y coordinates are not exactly the same

    # It is also a huge "TIR" international agreement, which had:
    # - A ton of quoting errors
    # - Old-style article markings in the Act itself
    # - so many lines I had to enable swap.
    # TODO: It is not parsed correctly, but I couldn't care less right now

    acts = {a.identifier: a for a in parse_single_kozlony(2013, 67) if isinstance(a, Act)}
    assert len(acts) == 6, "Issue 2013/67 of Magyar Kozlony contains 6 separate Acts"


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


def test_end_to_end_2013_222():
    # This Issue contains an Act that has a ton of amendments related to the 2013 Ptk.
    # As such, it is hard to parse correctly, and it has some juicy corner cases
    acts = [a for a in parse_single_kozlony(2013, 222) if isinstance(a, Act)]
    assert len(acts) == 1, "Issue 2013/222 of Magyar Kozlony contains a single Act"
    act = acts[0]

    assert act.identifier == "2013. évi CCLII. törvény"
    assert act.subject == "egyes törvényeknek az új Polgári Törvénykönyv hatálybalépésével összefüggő módosításáról"

    assert act.article(181).paragraph(2).intro == "A Szövtv. 20−24. §-a helyébe a következő rendelkezések lépnek:"
    assert act.article(181).paragraph(2).children_type == QuotedBlock
    assert len(act.article(181).paragraph(2).children) == 1

    # This is a fixupped Paragraph the original text has wrong quote marks to begin the amendment text.
    assert act.article(185).paragraph(4).intro == "A Ptk. 3:85. § (1) bekezdése a következő szöveggel lép hatályba:"
    assert act.article(185).paragraph(4).children_type == BlockAmendment
    assert len(act.article(185).paragraph(4).children) == 1
    assert act.article(185).paragraph(4).block_amendment().children_type == Paragraph

    assert act.article(188).paragraph(3).intro == "A Ptk. 6:155. §-a a következő szöveggel lép hatályba:"

    # This is a fixupped Paragraph the original text does not have "Ptk." in it.
    assert act.article(188).paragraph(4).intro == "A Ptk. 6:198. § (3) bekezdése a következő szöveggel lép hatályba:"

    # This article is literally the best target practice Paragraph for the Reference parser.
    assert act.article(191).paragraph(4).text == "A 35. § (2) bekezdése, a 100. § (4), (5), valamint (7) bekezdése 2014. május 1-jén lép hatályba."

    assert act.article(192).paragraph().intro == "E törvény"
    assert act.article(192).paragraph().point('n').text == "129. § (1)–(8) bekezdése és (14) bekezdése az Alaptörvény 29. cikk (7) bekezdése"
    assert act.article(192).paragraph().wrap_up == "alapján sarkalatosnak minősül."


def test_end_to_end_2016_210():
    acts = {a.identifier: a for a in parse_single_kozlony(2016, 210) if isinstance(a, Act)}
    assert len(acts) == 11, "Issue 2016/210 of Magyar Kozlony contains 11 separate Acts"

    acts["2016. évi CLXXXIV. törvény"].article(54).paragraph().intro == \
        "A Hjt. 215. § (1) bekezdés a) és b) pontja helyébe a következő rendelkezések lépnek: " \
        "(Megszűnik az önkéntes tartalékos szolgálati viszony akkor is, ha)"
    assert acts["2016. évi CLXXXIV. törvény"].article(54).paragraph().children_type == QuotedBlock
    assert len(acts["2016. évi CLXXXIV. törvény"].article(54).paragraph().children) == 1

    acts["2016. évi CLXXXIV. törvény"].article(46).paragraph().intro == "A Hjt. 85. alcíme helyébe a következő alcím lép:"
    assert acts["2016. évi CLXXXIV. törvény"].article(46).paragraph().children_type == QuotedBlock
    assert len(acts["2016. évi CLXXXIV. törvény"].article(46).paragraph().children) == 1


def test_end_to_end_2018_123():
    # This is the most modern Act we want to touch right now.
    # The purpose of the test is mainly document-format-compatibility
    acts = {a.identifier: a for a in parse_single_kozlony(2018, 123) if isinstance(a, Act)}
    assert len(acts) == 6, "Issue 2018/123 of Magyar Kozlony contains 6 separate Acts"

    subtitles_in_2018_L = [s for s in acts["2018. évi L. törvény"].children if isinstance(s, Subtitle)]
    assert len(subtitles_in_2018_L) == 22
    assert subtitles_in_2018_L[18].identifier == '19'
    assert subtitles_in_2018_L[18].title == \
        'A kis összegű követelés értékhatára, a filmalkotásokhoz kapcsolódó gyártási értékhatár és ' \
        'a közbeszerzési értékhatárok', \
        "Multiline subtitles parsed correctly"

    assert acts["2018. évi LII. törvény"].article(5).paragraph(6).intro == "A Tbj. szerint külföldinek minősülő személy által megszerzett"
    assert acts["2018. évi LII. törvény"].article(5).paragraph(6).point("b").text == "az Szja tv. szerint egyéb jövedelemnek minősülő jövedelmet"
    assert acts["2018. évi LII. törvény"].article(5).paragraph(6).wrap_up == "nem terheli adófizetési kötelezettség."

    assert acts["2018. évi LII. törvény"].article(34).paragraph().point(11).subpoint("p").text.endswith("járadék folyósításának időtartama;"), \
        "Multiline points/subpoints do not generate a wrap-up, if the indentation is correct"

    assert acts["2018. évi LIII. törvény"].subject == "a magánélet védelméről"
    assert acts["2018. évi LIII. törvény"].preamble is not None
    assert acts["2018. évi LIII. törvény"].preamble.startswith("A magánélet, a családi élet, az otthon")
    assert acts["2018. évi LIII. törvény"].preamble.endswith("fokozott védelme, a következő törvényt alkotja:")

    block_amendment = acts["2018. évi LV. törvény"].article(25).paragraph(5).block_amendment()
    assert block_amendment.children_type == AlphabeticPoint
    assert block_amendment.intro == "(3) A büntetés bűntett miatt három évig terjedő szabadságvesztés, ha a rendbontást"
    assert block_amendment.child("e").text == \
        "a gyűlés gyülekezési jogról szóló törvény szerinti békés jellegét biztosító korlátozásokat megsértve"
    assert block_amendment.wrap_up == "követik el."

    assert acts["2018. évi LIV. törvény"].article(2).paragraph().point(4).text.endswith("felfedett üzleti titokra épül."), \
        "Multiline numeric points parsed correctly"

    # International convention parsing
    assert acts["2018. évi LI. törvény"].article(3).paragraph().children_type == QuotedBlock
    assert len(acts["2018. évi LI. törvény"].article(3).paragraph().children) == 2, \
        "Multiple quote blocks parsed properly"
    last_line_of_hungarian_version = acts["2018. évi LI. törvény"].article(3).paragraph().quoted_block(0).lines[-1].content
    assert last_line_of_hungarian_version.endswith("Szlovák Köztársaság nevében"), \
        "Quote blocks are separated correctly"
    assert acts["2018. évi LI. törvény"].article(3).paragraph().wrap_up is None, "No junk is parsed after Quote blocks"
