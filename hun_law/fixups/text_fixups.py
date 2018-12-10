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


# The whole module is a bunch of fixups to existing Acts, that aren't
# well-formed enough to be parsed by the parser out-of-the-box

from .common import add_fixup, replace_line_content, add_empty_line_after, ptke_article_header_fixer, delete_line

# Title IV not found otherwise
add_fixup("2013. évi V. törvény", add_empty_line_after("A SZERZŐDÉS ÁLTALÁNOS SZABÁLYAI"))

# Invalid Rigid reference
add_fixup("2013. évi CCLII. törvény", replace_line_content(
    "(4) A 6:198. § (3) bekezdése a következő szöveggel lép hatályba:",
    "(4) A Ptk. 6:198. § (3) bekezdése a következő szöveggel lép hatályba:"
))

# Article titles starting before the article sign.
# See ptke_article_header_fixer source for details
add_fixup("2013. évi CLXXVII. törvény", ptke_article_header_fixer)

# Botched merge between two range insertion amendments
add_fixup("2011. évi CLXIX. törvény", replace_line_content(
    "(2) Az Mktv. 36. §-a a következő (4)–(6) bekezdéssel egészül ki:",
    "(2) Az Mktv. 36. §-a a következő (4)–(9) bekezdéssel egészül ki:"
))
add_fixup("2011. évi CLXIX. törvény", replace_line_content(
    "adatot át kell adni az NMHH részére, amely azokat tárolja és kezeli.”",
    "adatot át kell adni az NMHH részére, amely azokat tárolja és kezeli."
))
add_fixup("2011. évi CLXIX. törvény", delete_line(
    "„(3) Az Mktv. 36. §-a a következő (7)–(9) bekezdéssel egészül ki:"
))
add_fixup("2011. évi CLXIX. törvény", replace_line_content(
    "„(7) 2012. január 1-je előtt a kiskorúak védelme érdekében",
    "(7) 2012. január 1-je előtt a kiskorúak védelme érdekében",
))

# ---------------------------------------- QUOTING ISSUES -------------------------------------

# Quote characters: „ ”
# template:
"""
add_fixup("", replace_line_content(
    "",
    ""
))
"""

# This is very weird though, as it is in 266/(3), which is about things coming into force,
# and that paragraph should not contain an Amendment.
add_fixup("2010. évi CXLVIII. törvény", replace_line_content(
    "(7) bekezdésében a „huszonkét” szövegrész helyébe a „harminc” szöveg lép.”",
    "(7) bekezdésében a „huszonkét” szövegrész helyébe a „harminc” szöveg lép."
))

add_fixup("2010. évi CLIII. törvény", replace_line_content(
    "a „15 munkanapon belül” szöveg, valamint 140. § (6) bekezdésében a 8 munkanapon belül” szövegrész helyébe",
    "a „15 munkanapon belül” szöveg, valamint 140. § (6) bekezdésében a „8 munkanapon belül” szövegrész helyébe"
))

add_fixup("2010. évi CLIX. törvény", replace_line_content(
    "résztvevő a rendszerüzemeltető számára ismert;”",
    "résztvevő a rendszerüzemeltető számára ismert;"
))

add_fixup("2010. évi CLXXII. törvény", replace_line_content(
    "tesz közzé.”",
    "tesz közzé."
))
add_fixup("2010. évi CLXXII. törvény", replace_line_content(
    "vonatokról, valamint vasúti állomásról és megállóhelyről a szolgáltató a honlapján tájékoztatást tesz közzé.”",
    "vonatokról, valamint vasúti állomásról és megállóhelyről a szolgáltató a honlapján tájékoztatást tesz közzé."
))
add_fixup("2010. évi CLXXII. törvény", replace_line_content(
    "szövegrész helyébe a „miniszterrel egyetértésben” szöveg, 74. § (1) bekezdés m) pontjában az „is – „ szövegrész",
    "szövegrész helyébe a „miniszterrel egyetértésben” szöveg, 74. § (1) bekezdés m) pontjában az „is – ” szövegrész"
))
add_fixup("2010. évi CLXXII. törvény", replace_line_content(
    "helyébe az – egyetértésben” szöveg, 74. § (2) bekezdés k) és l) pontjában a „miniszter az” szövegrész helyébe",
    "helyébe az „– egyetértésben” szöveg, 74. § (2) bekezdés k) és l) pontjában a „miniszter az” szövegrész helyébe"
))

add_fixup("2010. évi CLXXIII. törvény", replace_line_content(
    "a „jelölt tag” szövegrész helyébe a „kinevezett tag” szöveg lép.”",
    "a „jelölt tag” szövegrész helyébe a „kinevezett tag” szöveg lép."
))

add_fixup("2010. évi CLXXX. törvény", replace_line_content(
    "jogosult, ha a szerződésében a teljes önkéntesség tényét nem rögzítette.”",
    "jogosult, ha a szerződésében a teljes önkéntesség tényét nem rögzítette."
))

add_fixup("2010. évi CLXXXIII. törvény", replace_line_content(
    "(4) E törvény 67. §-a, 165. § (2) bekezdés e) és f) pontja 2011. szeptember 1-jén lép hatályba.”",
    "(4) E törvény 67. §-a, 165. § (2) bekezdés e) és f) pontja 2011. szeptember 1-jén lép hatályba."
))

add_fixup("2011. évi XXIII. törvény", replace_line_content(
    "helyébe az „az aktív korúak ellátására való jogosultság keretében megállapított pénzbeli ellátásban” szöveg lép.”",
    "helyébe az „az aktív korúak ellátására való jogosultság keretében megállapított pénzbeli ellátásban” szöveg lép."
))

add_fixup("2011. évi XXIX. törvény", replace_line_content(
    "vonható vissza.”",
    "vonható vissza."
))
add_fixup("2011. évi XXIX. törvény", replace_line_content(
    "alkalmazni.”",
    "alkalmazni.",
    needle_prev_lines=["biztosítása érdekében – a 102/A. § (3) bekezdés a) pontját és a 102/B. § (1) és (2) bekezdését kell megfelelően"]
))
add_fixup("2011. évi XXIX. törvény", replace_line_content(
    "alkalmazható.”",
    "alkalmazható.",
    needle_prev_lines=["megfelel az e §-ban foglaltaknak, a Hivatal határozatának jogerőre emelkedését követően a 102. §–102/E. § nem"]
))
add_fixup("2011. évi XXIX. törvény", replace_line_content(
    "(5) bekezdése, 178. § (7) bekezdése, 181. § (3) és (4) bekezdése, 183. §-a.”",
    "(5) bekezdése, 178. § (7) bekezdése, 181. § (3) és (4) bekezdése, 183. §-a."
))
# Note the í instead of i, lol. TODO
add_fixup("2011. évi XXIX. törvény", replace_line_content(
    "í) dönt a szállítási rendszerüzemeltető és a vertikálisan integrált földgázipari vállalkozás, valamint a 119/A. §",
    "„í) dönt a szállítási rendszerüzemeltető és a vertikálisan integrált földgázipari vállalkozás, valamint a 119/A. §"
))

add_fixup("2011. évi XLVI. törvény", replace_line_content(
    "kifizetett bevétel, illetve a jogviszony megszűnésekor a magánszemélyt megillető jubileumi jutalom.\"",
    "kifizetett bevétel, illetve a jogviszony megszűnésekor a magánszemélyt megillető jubileumi jutalom.”"
))

add_fixup("2013. évi CCLII. törvény", replace_line_content(
    ",,(1) Az egyesület jogutód nélküli megszűnése esetén a hitelezők követeléseinek kiegyenlítése után fennmaradó",
    "„(1) Az egyesület jogutód nélküli megszűnése esetén a hitelezők követeléseinek kiegyenlítése után fennmaradó"
))
add_fixup("2013. évi CCLII. törvény", replace_line_content(
    ",,(3) A nyilvántartó bíróság jogszabályban meghatározott szervezetnek juttatja a vagyont, ha az alapító okirat, vagy",
    "„(3) A nyilvántartó bíróság jogszabályban meghatározott szervezetnek juttatja a vagyont, ha az alapító okirat, vagy"
))

add_fixup("2011. évi LIX. törvény", replace_line_content(
    "szövegrész.”",
    "szövegrész."
))
add_fixup("2011. évi LIX. törvény", replace_line_content(
    "(17) A VET. 171/A. §-a 2012. szeptember 30-án hatályát veszti.”",
    "(17) A VET. 171/A. §-a 2012. szeptember 30-án hatályát veszti."
))

# TODO: this text is inside a table. This might not be the best solution here.
add_fixup("2011. évi LXV. törvény", replace_line_content(
    "Szlovén Köztársaság A 20. cikkben kijelölt szolgálatok",
    "Szlovén Köztársaság A 20. cikkben kijelölt szolgálatok”",
))

add_fixup("2011. évi LXXXVI. törvény", replace_line_content(
    "(5) E törvény 2012. május 2-án hatályát veszti.”",
    "(5) E törvény 2012. május 2-án hatályát veszti."
))

# Wrong ending quote char
add_fixup("2011. évi LXXXIV. törvény", replace_line_content(
    "a silent partner ( „stiller Gesellschafter“) from his participation as such, or from a loan with an interest rate linked to",
    "a silent partner ( „stiller Gesellschafter”) from his participation as such, or from a loan with an interest rate linked to"
))
add_fixup("2011. évi LXXXIV. törvény", replace_line_content(
    "borrower’s profit ( „partiarisches Darlehen“) or from profit sharing bonds ( „Gewinnobligationen“) within",
    "borrower’s profit ( „partiarisches Darlehen”) or from profit sharing bonds ( „Gewinnobligationen”) within"
))

add_fixup("2011. évi XCVI. törvény", replace_line_content(
    "35. § (1) A MódTv. 82. § (1) bekezdésében a „2010. október 31.” szövegrész helyébe a 2011. április 30.” szöveg lép.",
    "35. § (1) A MódTv. 82. § (1) bekezdésében a „2010. október 31.” szövegrész helyébe a „2011. április 30.” szöveg lép."
))

add_fixup("2011. évi XCVI. törvény", replace_line_content(
    "Zsigmond Király Főiskola, Budapest\"",
    "Zsigmond Király Főiskola, Budapest”"
))

# The "Felhatalmazás" line is not actually part of the amendment, it's just context.
add_fixup("2015. évi CIV. törvény", replace_line_content(
    "„Felhatalmazás",
    "Felhatalmazás"
))
add_fixup("2015. évi CIV. törvény", replace_line_content(
    "28. § Felhatalmazást kap a Kormány, hogy e törvény alapján",
    "„28. § Felhatalmazást kap a Kormány, hogy e törvény alapján"
))

add_fixup("2011. évi CV. törvény", replace_line_content(
    "b) ha egyenlőtlen munkaidő-beosztásban kíván dolgozni, a munkaidő-beosztásra vonatkozó javaslatáról.”",
    "b) ha egyenlőtlen munkaidő-beosztásban kíván dolgozni, a munkaidő-beosztásra vonatkozó javaslatáról."
))
add_fixup("2011. évi CV. törvény", replace_line_content(
    "történő foglalkoztatásnak a Módtv. hatálybalépését követően ledolgozott időtartama tekintetében kell alkalmazni.”",
    "történő foglalkoztatásnak a Módtv. hatálybalépését követően ledolgozott időtartama tekintetében kell alkalmazni."
))

add_fixup("2011. évi CVI. törvény", replace_line_content(
    "(6) bekezdésében, valamint 37/C. § (8) bekezdés a) pontjában a ”bérpótló juttatásra” szövegrész helyébe",
    "(6) bekezdésében, valamint 37/C. § (8) bekezdés a) pontjában a „bérpótló juttatásra” szövegrész helyébe"
))

add_fixup("2011. évi CVII. törvény", replace_line_content(
    "szempontjából nem megfelelő, akkor annak üzemben tartóját terhelik.”",
    "szempontjából nem megfelelő, akkor annak üzemben tartóját terhelik."
))
add_fixup("2011. évi CVII. törvény", replace_line_content(
    "49/a. Helymeghatározási szolgáltatás: olyan kapcsolódó szolgáltatás, amelyet az előfizető vagy felhasználó",
    "„49/a. Helymeghatározási szolgáltatás: olyan kapcsolódó szolgáltatás, amelyet az előfizető vagy felhasználó"
))
add_fixup("2011. évi CVII. törvény", replace_line_content(
    "szöveg,”, a 31. § (3) bekezdésében „Az (1)–(2) bekezdésben” szövegrész helyébe „A (2) bekezdésben” szöveg, a 33. §",
    "szöveg, a 31. § (3) bekezdésében „Az (1)–(2) bekezdésben” szövegrész helyébe „A (2) bekezdésben” szöveg, a 33. §"
))
add_fixup("2011. évi CVII. törvény", replace_line_content(
    "rendelkezések alkalmazandók.”",
    "rendelkezések alkalmazandók."
))

add_fixup("2011. évi CXXV. törvény", replace_line_content(
    "a 2012. január–március tárgynegyedévre kell alkalmazni.”",
    "a 2012. január–március tárgynegyedévre kell alkalmazni.",
    needle_prev_lines=["CXXV. törvénnyel megállapított 33. § (2), (3), (6) bekezdéseit 2012. január 1. napjától és első alkalommal"]
))

add_fixup("2011. évi CXXXVI. törvény", replace_line_content(
    "2. § Az Országgyűlés Szigetvár városnak a „Leghősiesebb Város” ( „Civitas Invicta\") címet adományozza.",
    "2. § Az Országgyűlés Szigetvár városnak a „Leghősiesebb Város” ( „Civitas Invicta”) címet adományozza."
))


add_fixup("2011. évi CXLV. törvény", replace_line_content(
    "\"C O N V E N T I O N",
    "„C O N V E N T I O N"
))

add_fixup("2011. évi CXLIV. törvény", replace_line_content(
    "Ireland signed at Budapest on 28th November 1977 (”the prior Convention”) shall cease to be effective from the dates",
    "Ireland signed at Budapest on 28th November 1977 („the prior Convention”) shall cease to be effective from the dates"
))

add_fixup("2011. évi CLIV. törvény", replace_line_content(
    "g) 92. § (3) bekezdés első mondatában az ”, illetve a megyei önkormányzat a településen, illetve a megyében”",
    "g) 92. § (3) bekezdés első mondatában az „, illetve a megyei önkormányzat a településen, illetve a megyében”"
))
add_fixup("2011. évi CLIV. törvény", replace_line_content(
    "j) 89/B. § (7) bekezdésében a „megyei önkormányzat” szövegrész helyébe a Kormány általános hatáskörű területi",
    "j) 89/B. § (7) bekezdésében a „megyei önkormányzat” szövegrész helyébe a „Kormány általános hatáskörű területi"
))

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

add_fixup("2011. évi CLXII. törvény", replace_line_content(
    ",,Fogadom, hogy a rám bízott ügyeket tisztességes eljárásban, részrehajlás nélkül, lelkiismeretesen, kizárólag",
    "„Fogadom, hogy a rám bízott ügyeket tisztességes eljárásban, részrehajlás nélkül, lelkiismeretesen, kizárólag"
))
add_fixup("2011. évi CLXI. törvény", replace_line_content(
    ",,A munkaköri kötelességeimet részrehajlás nélkül, lelkiismeretesen, kizárólag a jogszabályoknak megfelelően,",
    "„A munkaköri kötelességeimet részrehajlás nélkül, lelkiismeretesen, kizárólag a jogszabályoknak megfelelően,"
))

add_fixup("2011. évi CLXVI. törvény", replace_line_content(
    "„(A kiadások fedezetét a következő bevételek képezik:",
    "(A kiadások fedezetét a következő bevételek képezik:"
))

add_fixup("2011. évi CLXX. törvény", replace_line_content(
    "(2) Az 1–25. §, a 27. § és az 1. melléklet 2012. január 1-jén lép hatályba.”",
    "(2) Az 1–25. §, a 27. § és az 1. melléklet 2012. január 1-jén lép hatályba."
))

add_fixup("2011. évi CLXXV. törvény", replace_line_content(
    "„ „45. § A Tao tv. a következő 29/Q. §-sal egészül ki:",
    "„45. § A Tao tv. a következő 29/Q. §-sal egészül ki:"
))
add_fixup("2011. évi CLXXV. törvény", replace_line_content(
    "szöveg lép .",
    "szöveg lép .”"
))

add_fixup("2011. évi CLXXVI. törvény", replace_line_content(
    "(3) bekezdésében foglaltakon túl – „ szövegrész helyébe az „– az 5/A. § (3) bekezdésében és (11) bekezdésének",
    "(3) bekezdésében foglaltakon túl – ” szövegrész helyébe az „– az 5/A. § (3) bekezdésében és (11) bekezdésének"
))
add_fixup("2011. évi CLXXVI. törvény", replace_line_content(
    "g) 4. számú melléklete.”",
    "g) 4. számú melléklete."
))

add_fixup("2011. évi CLXXIII. törvény", replace_line_content(
    "„kihirdetésétől” szövegrész helyébe a „kézbesítésétől” szöveg lép.”",
    "„kihirdetésétől” szövegrész helyébe a „kézbesítésétől” szöveg lép."
))
add_fixup("2011. évi CLXXII. törvény", replace_line_content(
    "a bi) alpontjában a „Magyar Köztársaság” szövegrész helyébe a „Magyarország” szöveg lép.”",
    "a bi) alpontjában a „Magyar Köztársaság” szövegrész helyébe a „Magyarország” szöveg lép."
))

add_fixup("2011. évi CLXXXIV. törvény", replace_line_content(
    "helyébe a ”kormányzati szolgálati, közszolgálati, vagy” szöveg,",
    "helyébe a „kormányzati szolgálati, közszolgálati, vagy” szöveg,"
))

add_fixup("2011. évi CXCIII. törvény", replace_line_content(
    "megszüntetéséről a befektetési alapkezelő dönt, amelynek során az ”IL” sorozatjelű befektetési jegyeket az alap",
    "megszüntetéséről a befektetési alapkezelő dönt, amelynek során az „IL” sorozatjelű befektetési jegyeket az alap",
))
add_fixup("2011. évi CXCIII. törvény", replace_line_content(
    "a „2011. december 31-ig” szövegrész helyébe a „2012. június 30-ig” szöveg lép.”",
    "a „2011. december 31-ig” szövegrész helyébe a „2012. június 30-ig” szöveg lép."
))
add_fixup("2011. évi CXCIII. törvény", replace_line_content(
    "hatósági felügyeleti,” szöveg lép.”",
    "hatósági felügyeleti,” szöveg lép."
))
add_fixup("2011. évi CXCIII. törvény", replace_line_content(
    "valamint e szolgáltatások fedezetéről szóló 1997. évi LXXX. törvény 3. § (2) bekezdése szerinti kötelezettségét.”",
    "valamint e szolgáltatások fedezetéről szóló 1997. évi LXXX. törvény 3. § (2) bekezdése szerinti kötelezettségét.””"
))

add_fixup("2011. évi CXCVII. törvény", replace_line_content(
    "bocsátott vagyonból.”",
    "bocsátott vagyonból.",
    needle_prev_lines=[
        "biztosíték teljesítéséért a vezetőtől való behajthatatlanság esetén kezesként felel. A külföldi székhelyű vállalkozás",
        "az említett kezesi kötelezettségéből eredő fizetési kötelezettségét nem teljesítheti a fióktelepe rendelkezésére"
    ]
))
add_fixup("2011. évi CXCVII. törvény", replace_line_content(
    "(8) bekezdése.”",
    "(8) bekezdése."
))

add_fixup("2011. évi CCIX. törvény", replace_line_content(
    "alkalmazni.”",
    "alkalmazni.””"
))

add_fixup("2011. évi CCVII. törvény", replace_line_content(
    "g) 2. számú melléklet 10. pontja.”",
    "g) 2. számú melléklet 10. pontja."
))

# Wrong quote ending character
add_fixup("2018. évi LI. törvény", replace_line_content(
    "Maďarsko a Slovenská republika (ďalej len „zmluvné strany“),",
    "Maďarsko a Slovenská republika (ďalej len „zmluvné strany”),",
))
add_fixup("2018. évi LI. törvény", replace_line_content(
    "slovenskej hraničnej čiary – hraničné úseky č. III., IV. a VIII. – 2013“, ktorý ako príloha tejto zmluvy tvorí jej",
    "slovenskej hraničnej čiary – hraničné úseky č. III., IV. a VIII. – 2013”, ktorý ako príloha tejto zmluvy tvorí jej",
))
add_fixup("2018. évi LI. törvény", replace_line_content(
    "MAĎARSKO SLOVENSKÚ REPUBLIKU“",
    "MAĎARSKO SLOVENSKÚ REPUBLIKU”",
))
