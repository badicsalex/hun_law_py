# Copyright 2018-2019 Alex Badics <admin@stickman.hu>
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

from typing import Tuple, List, Optional
import pytest

from hun_law.parsers.grammatical_analyzer import GrammaticalAnalyzer
from hun_law.structure import Reference

from tests.cheap.utils import ref

CASES: List[Tuple[
    str,  # Text
    Optional[str],  # Reference positions in string form
    Optional[List[Reference]],  # Expected references
    Optional[List[str]]  # Expected act references
]] = [
    (
        "A hegyközségekről szóló 2012. évi CCXIX. törvény (a továbbiakban: Hktv.) 28. §-a helyébe a következő rendelkezés lép:",
        "                        [                      ]                         <     >                                     ",
        [ref("2012. évi CCXIX. törvény", '28')],
        ["2012. évi CCXIX. törvény"],
    ),
    (
        "A Magyarország 2013. évi központi költségvetéséről szóló 2012. évi CCIV. törvény 44/B. és 44/C. §-a helyébe a következő rendelkezés lép:",
        "                                                         [                     ] <                >                                     ",
        [
            ref("2012. évi CCIV. törvény", ("44/B", "44/C")),
        ],
        ["2012. évi CCIV. törvény"],
    ),
    (
        "A pénzügyi tranzakciós illetékről szóló 2012. évi CXVI. törvény (a továbbiakban: Pti. törvény) 7. § (1) bekezdése helyébe a következő rendelkezés lép:",
        "                                        [                     ]                                <                >                                     ",
        [ref("2012. évi CXVI. törvény", "7", "1")],
        ["2012. évi CXVI. törvény"]
    ),
    (
        "Ez a törvény – a (2) bekezdésben foglalt kivétellel – 2013. augusztus 1-jén lép hatályba.",
        "                 <             >                                                         ",
        [ref(None, None, "2")],
        [],
    ),
    (
        "Az erdőről, az erdő védelméről és az erdőgazdálkodásról szóló törvény szerint erdőnek, valamint erdőgazdálkodási célt közvetlenül szolgáló földterületnek minősülő földre (a továbbiakban együtt: erdőnek minősülő föld) e törvény rendelkezéseit kell alkalmazni.",
        None, None, None,
    ),
    (
        "Az adás-vételnek nem minősülő, a föld tulajdonjogának átruházásáról szóló szerződést (ezen alcímben a továbbiakban: szerződés) – annak létrejöttétől számított 8 napon belül – a tulajdonjogot szerző félnek (csere esetén a cserepartnerek valamelyikének) a mezőgazdasági igazgatási szerv részére kell megküldeni jóváhagyás céljából.",
        None, None, None,
    ),
    (
        # Note the abbreviation without the rigid referenc to the Act.
        "A haszonbérletre e törvény rendelkezései mellett a Polgári Törvénykönyv (a továbbiakban: Ptk.), valamint a földről szóló törvény haszonbérletre vonatkozó szabályait is alkalmazni kell.",
        None, None, None,
    ),
    (
        "Az UNESCO Világörökség Bizottsága által az Egyezmény 11. cikk (2) bekezdése alapján létrehozott és vezetett lista.",
        None, None, None
    ),
    (
        "Világörökségi várományos helyszín (a továbbiakban: várományos helyszín): a kiemelkedõ kulturális örökségi, illetve természeti értékei (a továbbiakban: kiemelkedõ érték) révén, az Egyezmény 1. és 2. cikkében meghatározott kritériumok szerint az UNESCO Világörökség Központhoz (a továbbiakban: Központ) bejelentett.",
        None, None, None
    ),
    (
        "A gyermeknevelési támogatás (e § alkalmazásában a továbbiakban együtt: anyasági ellátás) folyósításának időszakát nem kell beszámítani.",
        None, None, None
    ),
    (
        "A minimálbér után a 2. § (1) bekezdés szerinti adómérték 50 százalékával megállapított összeggel a foglalkoztatás harmadik évében (a továbbiakban e § alkalmazásában: érvényesítési időszak).",
        None, None, None
    ),
    (
        "Az egyéb használati jogviszonyt alapító szerzõdés a miniszteri döntés minisztériumi honlapon történõ közzétételétõl számított 60. napon e törvény erejénél fogva megszûnik.",
        None, None, None
    ),
    (
        "Tilos a 67/548/EGK tanácsi irányelv 2. cikkének (2) bekezdésében meghatározott veszélyes anyagot vagy ezek utánzatát magánál tartva megjelenni.",
        None, None, None
    ),
    (
        "E törvény 3. § (3) bekezdésének b) pontja az Unió polgárainak és családtagjaiknak a tagállamok területén történő"
        "szabad mozgáshoz és tartózkodáshoz való jogáról, valamint az 1612/68/EGK rendelet módosításáról, továbbá"
        "a 64/221/EGK, a 68/360/EGK, a 72/194/EGK, a 73/148/EGK, a 75/34/EGK, a 75/35/EGK, a 90/364/EGK, a 90/365/EGK"
        "és a 93/96/EGK irányelv hatályon kívül helyezéséről szóló, 2004. április 29-i 2004/38/EK európai parlamenti és tanácsi"
        "irányelv 24. cikkének való megfelelést szolgálja.",
        None, None, None
    ),
    (
        "A felhívás előtt legalább 48 órával köteles bejelenteni az illetékes rendőrkapitányságnak – Budapesten a Budapesti Rendőr-főkapitányságnak – (a továbbiakban: gyülekezési hatóság).",
        None, None, None
    ),
    (
        "A jogosultnak joga van az üzleti titok hasznosítására, mással történő közlésére és nyilvánosságra hozatalára (a közlés és nyilvánosságra hozatal együtt: az üzleti titok felfedése).",
        None, None, None
    ),
    (
        " Az adó mértéke az adóalap 19,5 százaléka, az 1. § (4) bekezdésben foglalt esetekben a juttatások adóalapként meghatározott összegének 19,5 százaléka.",
        None, None, None
    ),
    (
        # Note that there is no "." after 25.
        # This caused a weird exception with a broken grammar in the past
        # TODO: Do we want to parse this?
        "A 2006. évi X. törvény 25 §-a.",
        "  [                  ]        ",
        [],
        ["2006. évi X. törvény"]
    ),
    (
        # TODO: Fix "this article" parsing. I just can't be bothered TBH.
        "E § (2) bekezdés d) pontjában foglaltaktól eltérni tilos.",
        "    <                       >                            ",
        [ref(None, None, "2", "d")],
        [],
    ),
    (
        "A szabálysértésekről és egyebekről szóló 2012. évi I. törvény (a továbbiakban: Szabs. tv.) 29. § (2) bekezdés e) pontja helyébe a következő rendelkezés lép:",
        "                                         [                  ]                              <                          >                                     ",
        [ref("2012. évi I. törvény", "29", "2", "e")],
        ["2012. évi I. törvény"],
    ),
    (
        "A (2) bekezdés szerinti hitelezõkkel szemben a kényszerértékesítési kvótára vonatkozó szabályok (6–8. §) és a (2) bekezdés megsértése esetén:",
        "  <          >                                                                                   <    >       <          >                   ",
        [
            ref(paragraph="2"),
            ref(article=("6", "8")),
            ref(paragraph="2"),
        ],
        [],
    ),
    (
        "Ha az (1) és a (2) bekezdésben meghatározott előzetes.",
        "      <                      >                        ",
        [
            ref(None, None, ("1", "2")),
        ],
        []
    ),
    (
        "Ha létrejött adás-vételi szerződést a 23. § (4) bekezdésének a) vagy b) pontjában foglalt esetek fennállása alapján jóváhagyja.",
        "                                      <                                         >                                              ",
        [
            ref(None, "23", "4", ("a", "b")),
        ],
        []
    ),
    (
        "Az (1) bekezdés b) pont bb) alpontban meghatározott esetben a tilos a hasznosítás.",
        "   <                                >                                             ",
        [ref(None, None, "1", "b", "bb")],
        [],
    ),
    (
        "A Gyvt. 5. §-a a következő ny) ponttal egészül ki:",
        "  [   ] <                            >            ",
        [
            ref("Gyvt.", "5", None, "ny"),
        ],
        ["Gyvt."],
    ),
    (
        "Az Eht. 188. §-a a következő 31/a. ponttal egészül ki:",
        "   [  ] <                                >            ",
        [
            ref("Eht.", "188", None, "31/a"),
        ],
        ["Eht."],
    ),
    (
        "A Gyvt. 69/D. §-a a következő (1a) és (1b) bekezdéssel egészül ki:",
        "  [   ] <                                            >            ",
        [
            ref("Gyvt.", "69/D", ("1a", "1b")),
        ],
        ["Gyvt."],
    ),
    (
        "Az alpontok rendjéről szóló 2111. évi LXXV. törvény (a továbbiakban: Tv.) 1. § (1) bekezdés 1. pont c) alpontja helyébe a következő rendelkezés lép:",
        "                            [                     ]                       <                                   >                                     ",
        [ref("2111. évi LXXV. törvény", "1", "1", "1", "c")],
        ["2111. évi LXXV. törvény"],
    ),
    (
        "Amely a Tbj. 4. § k) pont 2. alpontja alapján járulékalapot képez.",
        "        [  ] <                      >                             ",
        [ref("Tbj.", "4", None, "k", "2")],
        ["Tbj."]
    ),
    (
        # Multiple sentences
        "Az Eht. 188. §-a a következő 31/a. ponttal egészül ki. Az Eht. 188. §-a a következő 31/a. ponttal egészül ki.",
        "   [  ] <      >             <           >                [  ] <      >             <           >            ",
        [
            ref("Eht.", "188"),
            ref(point="31/a"),
            ref("Eht.", "188"),
            ref(point="31/a"),
        ],
        ["Eht.", "Eht."],
    ),
    (
        "A légiközlekedésről szóló 1995. évi XCVII. törvény 71. §-a a következő 3a. ponttal egészül ki:",
        "                          [                      ] <                             >            ",
        [
            ref("1995. évi XCVII. törvény", "71", None, "3a"),
        ],
        ["1995. évi XCVII. törvény"],
    ),
    (
        "A (6) bekezdés szerinti adóalap csökkenti a mezőgazdasági őstermelőként az 1. § (1) és (5) bekezdés f)–g) pont szerint fennálló adókötelezettség alapját.",
        "  <          >                                                             <      >    <                     >                                           ",
        [
            ref(paragraph="6"),
            ref(None, "1", "1"),
            ref(None, "1", "5", ("f", "g")),
        ],
        []
    ),
    (
        "A temetőkről és a temetkezésről szóló 1999. évi XLIII. törvény (a továbbiakban: temetőkről és a temetkezésről szóló törvény) 3. §-a a következő k) ponttal egészül ki:",
        "                                      [                      ]                                                               <                           >            ",
        [
            ref("1999. évi XLIII. törvény", "3", None, "k"),
        ],
        ["1999. évi XLIII. törvény"],
    ),
    (
        "A víziközmű-szolgáltatásról szóló 2011. évi CCIX. törvény (a továbbiakban: Víziközmű tv.) 2. §-a a következő 31. ponttal egészül ki:",
        "                                  [                     ]                                 <                            >            ",
        [
            ref("2011. évi CCIX. törvény", "2", None, "31"),
        ],
        ["2011. évi CCIX. törvény"],
    ),
    (
        "A Víziközmű tv. 63. §-a a következő (5)–(7) bekezdéssel egészül ki:",
        "  [           ] <                                     >            ",
        [
            ref("Víziközmű tv.", "63", ("5", "7")),
        ],
        ["Víziközmű tv."]
    ),
    (
        "Az európai részvénytársaságról szóló 2004. évi XLV. törvény (a továbbiakban: Eurt.tv.) 2. §-a helyébe a következő rendelkezés lép:",
        "                                     [                    ]                            <    >                                     ",
        [
            ref("2004. évi XLV. törvény", "2"),
        ],
        ["2004. évi XLV. törvény"],
    ),
    (
        # This will later be a chapter reference, but not now.
        "A szövetkezetekről szóló 2006. évi X. törvény (a továbbiakban: Szövtv.) I. és II. Fejezete helyébe a következő I. és II. Fejezet lép:",
        "                         [                  ]                                                                                        ",
        [],
        ["2006. évi X. törvény"],
    ),
    (
        "Semmis az alapszabály olyan rendelkezése, amely a vagyoni hozzájárulásokkal kapcsolatban az e §-ban meghatározottnál későbbi teljesítési határidőt ír elő.",
        None,
        None,
        None,
    ),
    (
        # This will be a title reference later
        "A Ctv. I. Fejezete a következő 6–8. címmel egészül ki:",
        "  [  ]                                                ",
        [],
        ["Ctv."],
    ),
    (
        # Appendix reference
        "A Ctv. 1–3. számú melléklete az 1. melléklet szerint módosul.",
        "  [  ]                                                       ",
        [],
        ["Ctv."],
    ),
    (
        # Subtitle + article reference
        "A Cnytv. a következő 5/A. alcímmel, valamint 18. §-sal és 18/A. §-sal egészül ki:",
        "  [    ]                                     <       >    <         >            ",
        [
            ref(None, "18"),
            ref(None, "18/A"),
        ],
        ["Cnytv."],
    ),
    (
        # Test that quoted references are not parsed
        "Az Flt. 30. § (1) bekezdés a) pontjában az „a 25. § (1) bekezdésének c)–d) pontjában” szövegrész helyébe az „a 25. § (1) bekezdésének d) pontjában” szöveg lép.",
        "   [  ] <                             >                                                                                                                        ",
        [ref("Flt.", "30", '1', 'a'), ],
        ["Flt.", ],
    ),
    (
        "A Ptk. 3:222. § (1) bekezdése a következő szöveggel lép hatályba:",
        "  [  ] <                    >                                    ",
        [ref("Ptk.", "3:222", "1")],
        ["Ptk."],
    ),
    (
        "E törvény az Alaptörvény P) cikk (2) bekezdése alapján sarkalatosnak minősül.",
        None, None, None
        # TODO: FIXME
        # Should be left blank on purpose, since Constitution references are not supported by the
        # rest of the code, and we don't want to have spurious paragraph references
        # "                                                                             ",
        # [],
        # [],
    ),
    (
        "E szolgáltatások fedezetéről szóló 1997. évi LXXX. törvény végrehajtásáról szóló 195/1997. (XI. 5.) Kormányrendelet (a továbbiakban: Tbj. vhr.) 7/B. §-a szerint kell igazolni.",
        None, None, None
    ),
    (
        "Ha az egyesülő jogi személyek közül egyes jogok (pl. részvénykibocsátás joga) nem mindegyik jogi személyt illetik meg.",
        None,
        None,
        None,
    ),
    (
        "Az 1986. évi 14. törvényerejű rendelettel kihirdetett, A Gyermekek Jogellenes Külföldre Vitelének Polgári Jogi Vonatkozásairól szóló,"
        "Hágában az 1980. évi október 25. napján kelt egyezmény alkalmazása szempontjából a Ptk. rendelkezéseit a Ptk. hatálybalépését követően"
        "külföldre vitt vagy ott visszatartott gyermekek tekintetében kell alkalmazni.",
        None,
        None,
        None,
    ),
    (
        "A Foglalkozások Egységes Osztályozási Rendszeréről szóló, 2012. január 1-jén hatályos KSH-közlemény (FEOR-08):"
        "6. főcsoport 61. csoportjába tartozó, a 7. főcsoport 7333 számú foglalkozásából a mezőgazdasági gép"
        "(motor) karbantartója, javítója munkakörben és a 8. főcsoport 8421 számú foglalkozás szerinti munkakörben"
        "(a továbbiakban együtt: mezőgazdasági munkakör).",
        None, None, None
    ),
    (
        "Aki 2011. december 31-én – a társadalombiztosítási nyugellátásról szóló törvény alapján megállapított –"
        "I., II., vagy III. csoportos rokkantsági, baleseti rokkantsági nyugdíjra volt jogosult, azzal most nem foglalkozunk.",
        None, None, None
    ),
    (
        "A jogi személynek a Ptk. rendelkezéseit a (2) bekezdés szerinti döntéstől, ennek hiányában 2015. március 15-étől kell alkalmaznia"
        "(ezen alcím alkalmazásában a továbbiakban együtt: a Ptk. rendelkezéseivel összhangban álló továbbműködés időpontja).",
        "                    [  ]                  <          >                                                                           "
        "                                                    [  ]                                                            ",
        [ref(paragraph="2")],
        ["Ptk.", "Ptk."],
    ),
    (
        # Multiple sentences
        "A tesztekről szóló 2337. évi I. törvény nem létezik. Egy második mondattól meg parse-olni sem lehet.",
        "                   [                  ]                                                             ",
        [],
        ["2337. évi I. törvény"],
    ),
    (
        "E törvény rendelkezéseit a Polgári Törvénykönyvről szóló 2013. évi V. törvénnyel (a továbbiakban: Ptk.) együtt kell alkalmazni.",
        "                                                         [                     ]                                               ",
        [],
        ["2013. évi V. törvény"],
    ),
    (
        "Hatályát veszti a Tv. 8/A. §–8/B. §-a, 16/A. §–16/B. §-a, és 17/A. § (1) és (3) bekezdése.",
        "                  [ ] <             >  <               >     <         >    <           > ",
        [
            ref("Tv.", ("8/A", "8/B")),
            ref("Tv.", ("16/A", "16/B")),
            ref("Tv.", "17/A", "1"),
            ref("Tv.", "17/A", "3"),
        ],
        ["Tv."],
    ),
    (
        "Hatályát veszti az ingatlan-nyilvántartásról szóló 1997. évi CXLI. törvény 16/A. §-a és 91. § (2) bekezdése.",
        "                                                   [                     ] <       >    <                 > ",
        [
            ref("1997. évi CXLI. törvény", "16/A"),
            ref("1997. évi CXLI. törvény", "91", "2"),
        ],
        ["1997. évi CXLI. törvény"],
    ),
    (
        "A polgári törvénykönyvről szóló 2013. évi V. tv. 3:319. § (5) bekezdése a következő szöveggel lép hatályba:",
        "                                [              ] <                    >                                    ",
        [
            ref("2013. évi V. törvény", "3:319", "5"),
        ],
        ["2013. évi V. törvény"],
    ),
    (
        "A Btk. 283. § (2) és (2a) bekezdése helyébe",
        "  [  ] <                          >        ",
        [
            ref("Btk.", "283", ("2", "2a")),
        ],
        ["Btk."]
    ),
    (
        "A Büntető Törvénykönyvről szóló 1978. évi IV. törvény (a továbbiakban: 1978. évi IV. törvény) 316. § (4) bekezdése csak úgy.",
        "                                [                   ]                                         <                  >          ",
        [
            ref("1978. évi IV. törvény", "316", "4"),
        ],
        ["1978. évi IV. törvény"]
    ),
    (
        "A Büntető Törvénykönyvről szóló 1978. évi IV. törvény (a továbbiakban: 1978. évi IV. törvény) 316. § (4) bekezdése a következő c) ponttal egészül ki:",
        "                                [                   ]                                         <                                         >            ",
        [
            ref("1978. évi IV. törvény", "316", "4", "c"),
        ],
        ["1978. évi IV. törvény"]
    ),
    (
        "Az 1–30. §, a 31. § (1) és (3)−(5) bekezdése, a 32–34. §, a 35. § (1) és (3)–(5) bekezdése, a 36. §, a 37. § "
        "(1) és (3)–(5) bekezdése, a 38. §, a 39. § (1) és (3)–(5) bekezdése, a 40–59. §, a 60. § (1) bekezdése, a 61. § (1), (2) "
        "és (7) bekezdése, 62–66. §, a 67. § (5) bekezdés a)–d) és g) pontja, a 68. § (1)–(3), (10) és (12)–(15) bekezdése, "
        "a 68. § (17) bekezdés 1., 2., 4., 6–8., 10–13., 15., 16., 18–20. és 25. pontja, a 69–76. §, a 77. § (3) és (4) bekezdése, a 78–82. §, "
        "a 181. és 182. §, a 192. § a)–b), valamint d)–n) pontja és a 193. § 2014. március 15-én lép hatályba.",
        "   <     >    <       >    <               >    <      >    <       >    <               >    <   >    <     "
        "  >    <               >    <   >    <       >    <               >    <      >    <                 >    <            > "
        "   <           >  <      >    <                      >    <       >    <           >  <  >    <                 >  "
        "  <                        >  <>  <  >  <    >  <      >  <    >    <        >    <      >    <                        >    <      >  "
        "  <            >    <          >           <          >      <    >                                  ",
        [
            ref(None, ('1', '30')),
            ref(None, '31', '1'),
            ref(None, '31', ('3', '5')),
            ref(None, ('32', '34')),
            ref(None, '35', '1'),
            ref(None, '35', ('3', '5')),
            ref(None, '36'),
            ref(None, '37', '1'),
            ref(None, '37', ('3', '5')),
            ref(None, '38'),
            ref(None, '39', '1'),
            ref(None, '39', ('3', '5')),
            ref(None, ('40', '59')),
            ref(None, '60', '1'),
            ref(None, '61', ('1', '2')),
            ref(None, '61', '7'),
            ref(None, ('62', '66')),
            ref(None, '67', '5', ('a', 'd')),
            ref(None, '67', '5', 'g'),
            ref(None, '68', ('1', '3')),
            ref(None, '68', '10'),
            ref(None, '68', ('12', '15')),
            ref(None, '68', '17', ('1', '2')),
            ref(None, '68', '17', '4'),
            ref(None, '68', '17', ('6', '8')),
            ref(None, '68', '17', ('10', '13')),
            ref(None, '68', '17', ('15', '16')),
            ref(None, '68', '17', ('18', '20')),
            ref(None, '68', '17', '25'),
            ref(None, ('69', '76')),
            ref(None, '77', ('3', '4')),
            ref(None, ('78', '82')),
            ref(None, ('181', '182')),
            ref(None, '192', None, ('a', 'b')),
            ref(None, '192', None, ('d', 'n')),
            ref(None, '193'),
        ],
        [],
    ),
    (
        "A 229. §, a 231. §, a 233. § (1) bekezdés a) és c) pontja, (2) bekezdés d) és f) pontja, a 256. §, a 314. "
        "§ és a 318. § 2013. február 1-jén lép hatályba.",
        "  <    >    <    >    <                    >    <       >  <             >    <       >    <    >    <    "
        ">      <    >                                  ",
        [
            ref(None, '229'),
            ref(None, '231'),
            ref(None, '233', '1', 'a'),
            ref(None, '233', '1', 'c'),
            ref(None, '233', '2', 'd'),
            ref(None, '233', '2', 'f'),
            ref(None, '256'),
            ref(None, '314'),
            ref(None, '318'),
        ],
        [],
    ),
    (
        "A 229. §, a 231. §, a 233. § (1) bekezdés a) és c) pontja, (2) bekezdés d) és f) pontja, a 256. §, a 314. "
        "§ és a 318. § direkt nem egy hatályba helyező mondat.",
        "  <    >    <    >    <                    >    <       >  <             >    <       >    <    >    <    "
        ">      <    >                                        ",
        [
            ref(None, '229'),
            ref(None, '231'),
            ref(None, '233', '1', 'a'),
            ref(None, '233', '1', 'c'),
            ref(None, None, '2', 'd'),
            ref(None, None, '2', 'f'),
            ref(None, '256'),
            ref(None, '314'),
            ref(None, '318'),
        ],
        [],
    ),
    (
        "A 228. §, a 230. §, a 232. §, a 233. § (1) bekezdés b) pontja és (2) bekezdés a)–c) és e) pontja, a "
        "235–255. §, a 257–260. §, a 261. § (2)–(5) bekezdése és (6) bekezdés b)–d) pontja, a 262–290. §, a 291. § "
        "(1), (2), és (4)–(10) bekezdése, a 292–313. § és a 315–317. § sem hatálybahelyező mondat.",
        "  <    >    <    >    <    >    <                           >    <                >    <       >    "
        "<        >    <        >    <                      >    <                       >    <        >    <      "
        "       >     <                >    <        >      <        >                            ",
        [
            ref(None, '228'),
            ref(None, '230'),
            ref(None, '232'),
            ref(None, '233', '1', 'b'),
            ref(None, None, '2', ('a', 'c')),
            ref(None, None, '2', 'e'),
            ref(None, ('235', '255')),
            ref(None, ('257', '260')),
            ref(None, '261', ('2', '5')),
            ref(None, None, '6', ('b', 'd')),
            ref(None, ('262', '290')),
            ref(None, '291', ('1', '2')),
            ref(None, '291', ('4', '10')),
            ref(None, ('292', '313')),
            ref(None, ('315', '317')),
        ],
        [],
    ),
]


@pytest.mark.parametrize("s,positions,refs,act_refs", CASES)  # type: ignore
def test_parse_results_are_correct(s: str, positions: Optional[str], refs: Optional[List[Reference]], act_refs: Optional[List[str]]) -> None:
    parsed = GrammaticalAnalyzer().analyze(s, print_result=True)
    if refs is None:
        return
    parsed_refs = []
    parsed_act_refs = []
    parsed_pos_chars = [" "] * len(s)
    for reference in parsed.element_references:
        parsed_pos_chars[reference.start_pos] = '<'
        parsed_pos_chars[reference.end_pos - 1] = '>'
        parsed_refs.append(reference.reference)

    for reference in parsed.act_references:
        parsed_pos_chars[reference.start_pos] = '['
        parsed_pos_chars[reference.end_pos - 1] = ']'
        parsed_act_refs.append(reference.reference.act)

    parsed_pos_string = "".join(parsed_pos_chars)
    assert refs == parsed_refs
    assert act_refs == parsed_act_refs
    if positions is not None:
        assert positions == parsed_pos_string
