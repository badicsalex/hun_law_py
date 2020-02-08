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
from hun_law.structure import \
    Reference, ActIdAbbreviation, BlockAmendmentMetadata, \
    Article, Paragraph, NumericPoint, AlphabeticPoint, AlphabeticSubpoint, \
    StructuralReference, SubtitleReferenceArticleRelative, RelativePosition, \
    Subtitle

from .utils import ref

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


ABBREVIATION_CASES: Tuple[Tuple[str, List[ActIdAbbreviation]], ...] = (
    (
        "A hegyközségekről szóló 2012. évi CCXIX. törvény (a továbbiakban: Hktv.) 28. §-a helyébe a következő rendelkezés lép:",
        [ActIdAbbreviation('Hktv.', '2012. évi CCXIX. törvény')]
    ),
    (
        "A pénzügyi tranzakciós illetékről szóló 2012. évi CXVI. törvény (a továbbiakban: Pti. törvény) 7. § (1) bekezdése helyébe a következő rendelkezés lép:",
        [ActIdAbbreviation('Pti.', '2012. évi CXVI. törvény')]
    ),
    (
        "A víziközmű-szolgáltatásról szóló 2011. évi CCIX. törvény (a továbbiakban: Víziközmű tv.) 2. §-a a következő 31. ponttal egészül ki:",
        [ActIdAbbreviation("Víziközmű tv.", "2011. évi CCIX. törvény")],
    ),
    (
        "Az európai részvénytársaságról szóló 2004. évi XLV. törvény (a továbbiakban: Eurt.tv.) 2. §-a helyébe a következő rendelkezés lép:",
        [ActIdAbbreviation("Eurt.tv.", "2004. évi XLV. törvény")],
    ),
    (
        "E törvény rendelkezéseit a Polgári Törvénykönyvről szóló 2013. évi V. törvénnyel (a továbbiakban: Ptk.) együtt kell alkalmazni.",
        [ActIdAbbreviation("Ptk.", "2013. évi V. törvény")],
    ),
    (
        # Abbreviation used in the text itself
        "Nem kell módosítani, ha a szövetkezetekről szóló 2006. évi X. törvény (a továbbiakban: Sztv.) rendelkezéseire utal "
        "Amennyiben azonban az alapszabály egyéb okból módosul, a szövetkezet köteles az Sztv.-re utalást is módosítani.",
        [ActIdAbbreviation("Sztv.", "2006. évi X. törvény")],
    ),
    (
        # No colon
        "A fogyasztóvédelmi hatósága fogyasztóvédelemrõl szóló 1997. évi CLV. törvény (a továbbiakban Fgytv.) szabályai szerint jár el.",
        [ActIdAbbreviation("Fgytv.", "1997. évi CLV. törvény")],
    ),
    (
        "A szabálysértésekről és egyebekről szóló 2012. évi I. törvény (a továbbiakban: Szabs. tv.) 29. § (2) bekezdés e) pontja helyébe a következő rendelkezés lép:",
        [ActIdAbbreviation("Szabs. tv.", "2012. évi I. törvény")]
    ),
    (
        "A Magyarország 2013. évi központi költségvetéséről szóló 2012. évi CCIV. törvény 44/B. és 44/C. §-a helyébe a következő rendelkezés lép:",
        []
    ),
    (
        "A Kvtv. 72. §-a a következő (9)–(12) bekezdésekkel egészül ki:",
        []
    ),
    (
        "A Büntető Törvénykönyvről szóló 1978. évi IV. törvény (a továbbiakban: 1978. évi IV. törvény) 316. § (4) bekezdése csak úgy.",
        []
    ),
    (
        "A Büntető Törvénykönyvről szóló 1978. évi IV. törvény (a továbbiakban: 1978. évi IV. törvény) 316. § (4) bekezdése a következő c) ponttal egészül ki:",
        []
    ),
)


@pytest.mark.parametrize("s,abbrevs", ABBREVIATION_CASES)  # type: ignore
def test_new_abbreviations(s: str, abbrevs: List[ActIdAbbreviation]) -> None:
    parsed = GrammaticalAnalyzer().analyze(s, print_result=True)
    new_abbrevs = list(parsed.act_id_abbreviations)
    assert new_abbrevs == abbrevs


BLOCK_AMENDMENT_CASES: Tuple[Tuple[str, BlockAmendmentMetadata], ...] = (
    (
        "A hegyközségekről szóló 2012. évi CCXIX. törvény (a továbbiakban: Hktv.) 28. §-a helyébe a következő rendelkezés lép:",
        BlockAmendmentMetadata(
            expected_type=Article,
            expected_id_range=("28", "28"),
            position=ref("2012. évi CCXIX. törvény", '28'),
            replaces=(ref("2012. évi CCXIX. törvény", '28'),),
        )
    ),
    (
        "A szabálysértésekről és egyebekről szóló 2012. évi I. törvény (a továbbiakban: Szabs. tv.) 29. § (2) bekezdés e) pontja helyébe a következő rendelkezés lép:",
        BlockAmendmentMetadata(
            expected_type=AlphabeticPoint,
            expected_id_range=("e", "e"),
            position=ref("2012. évi I. törvény", "29", "2", "e"),
            replaces=(ref("2012. évi I. törvény", "29", "2", "e"),)
        )
    ),
    (
        "A Tv. 1. § 3. pontja helyébe a következő rendelkezés lép:",
        BlockAmendmentMetadata(
            expected_type=NumericPoint,
            expected_id_range=("3", "3"),
            position=ref('Tv.', "1", None, "3"),
            replaces=(ref('Tv.', "1", None, "3"),)
        )
    ),
    (
        "Az alpontok rendjéről szóló 2111. évi LXXV. törvény (a továbbiakban: Tv.) 1. § (1) bekezdés 1. pont c) alpontja helyébe a következő rendelkezés lép:",
        BlockAmendmentMetadata(
            expected_type=AlphabeticSubpoint,
            expected_id_range=("c", "c"),
            position=ref("2111. évi LXXV. törvény", "1", "1", "1", "c"),
            replaces=(ref("2111. évi LXXV. törvény", "1", "1", "1", "c"),),
        )
    ),
    (
        "A Batv. 1. § (2) bekezdés b)–f) pontja helyébe a következő rendelkezés lép:",
        BlockAmendmentMetadata(
            expected_type=AlphabeticPoint,
            expected_id_range=("b", "f"),
            position=ref("Batv.", "1", "2", "b"),
            replaces=(ref("Batv.", "1", "2", ("b", "f")),),

        )
    ),
    (
        "Az Eht. 188. §-a a következő 31/a. ponttal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=NumericPoint,
            expected_id_range=("31/a", "31/a"),
            position=ref("Eht.", "188", None, "31/a"),
        )
    ),
    (
        "A légiközlekedésről szóló 1995. évi XCVII. törvény 71. §-a a következő 3a. ponttal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=NumericPoint,
            expected_id_range=("3a", "3a"),
            position=ref("1995. évi XCVII. törvény", "71", None, "3a"),
        )
    ),
    (
        "A Víziközmű tv. 63. §-a a következő (5)–(7) bekezdéssel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("5", "7"),
            position=ref("Víziközmű tv.", "63", "5"),
        )
    ),
    (
        "A Ptk. 6:417. § (4) bekezdése a következő szöveggel lép hatályba:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("4", "4"),
            position=ref("Ptk.", "6:417", "4"),
            replaces=(ref("Ptk.", "6:417", "4"),),
        )
    ),
    (
        "A Ptk. 6:130. §-a a következő szöveggel lép hatályba:",
        BlockAmendmentMetadata(
            expected_type=Article,
            expected_id_range=("6:130", "6:130"),
            position=ref("Ptk.", "6:130"),
            replaces=(ref("Ptk.", "6:130"),),
        )
    ),
    (
        "A Ptk. 3:391. §-a a következő (3) bekezdéssel kiegészülve lép hatályba:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("3", "3"),
            position=ref("Ptk.", "3:391", "3"),
        )
    ),
    (
        "A Ptk. 3:278. § (1) bekezdés e) pontja a következő szöveggel lép hatályba:",
        BlockAmendmentMetadata(
            expected_type=AlphabeticPoint,
            expected_id_range=("e", "e"),
            position=ref("Ptk.", "3:278", "1", "e"),
            replaces=(ref("Ptk.", "3:278", "1", "e"),),
        )
    ),
    (
        "A polgári törvénykönyvről szóló 2013. évi V. tv. 3:319. § (5) bekezdése a következő szöveggel lép hatályba:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("5", "5"),
            position=ref("2013. évi V. törvény", "3:319", "5"),
            replaces=(ref("2013. évi V. törvény", "3:319", "5"),),
        )
    ),
    (
        "A Gyvt. 69/D. §-a a következő (1a) és (1b) bekezdéssel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("1a", "1b"),
            position=ref("Gyvt.", "69/D", "1a"),
        )
    ),
    (
        "A Ptk. 3:261. § (4) és (5) bekezdése a következő szöveggel lép hatályba:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("4", "5"),
            position=ref("Ptk.", "3:261", "4"),
            replaces=(ref("Ptk.", "3:261", ("4", "5")),),
        )
    ),
    (
        "A Kkt. 49. § (2) bekezdés i) pontja helyébe a következő rendelkezés lép, és a bekezdés a következő j) ponttal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=AlphabeticPoint,
            expected_id_range=("i", "j"),
            position=ref("Kkt.", "49", "2", "i"),
            replaces=(ref("Kkt.", "49", "2", "i"),)
        )
    ),
    (
        "Az Elszámolási tv. 35. § (4) bekezdése helyébe a következő rendelkezés lép, és a § a következő (5) bekezdéssel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("4", "5"),
            position=ref("Elszámolási tv.", "35", "4"),
            replaces=(ref("Elszámolási tv.", "35", "4"),),
        )
    ),
    (
        "A Ptk. 3:268. § (2) és (3) bekezdése helyébe a következő rendelkezések lépnek, és a § a következő (4) bekezdéssel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("2", "4"),
            position=ref("Ptk.", "3:268", "2"),
            replaces=(ref("Ptk.", "3:268", ("2", "3")),)
        )
    ),
    (
        "A Ptk. 8:6. § r) pontja helyébe a következő rendelkezés lép, és a § a következő s) ponttal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=AlphabeticPoint,
            expected_id_range=("r", "s"),
            position=ref("Ptk.", "8:6", None, "r"),
            replaces=(ref("Ptk.", "8:6", None, "r"),),
        )
    ),
    (
        "A Tv. 16. § (1) bekezdés f) pontja helyébe a következő rendelkezés lép, és a § a következő g) és h) pontokkal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=AlphabeticPoint,
            expected_id_range=("f", "h"),
            position=ref("Tv.", "16", "1", "f"),
            replaces=(ref("Tv.", "16", "1", "f"),),
        )
    ),
    (
        "Az Tv. 5/A. § (2a) bekezdése helyébe a következő rendelkezés lép, és a § a következő (2b)–(2f) bekezdéssel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("2a", "2f"),
            position=ref("Tv.", "5/A", "2a"),
            replaces=(ref("Tv.", "5/A", "2a"),),
        )
    ),
    (
        "Az Evt. 108. § (4) bekezdése helyébe a következő rendelkezés lép, valamint a következő (5)–(10) bekezdéssel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("4", "10"),
            position=ref("Evt.", "108", "4"),
            replaces=(ref("Evt.", "108", "4"),),
        )
    ),
    (
        "A Btk. 459. § (1) bekezdés 24. pontja helyébe a következő rendelkezés lép, valamint a 459. § (1) bekezdése a következő 24a. ponttal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=NumericPoint,
            expected_id_range=("24", "24a"),
            position=ref("Btk.", "459", "1", "24"),
            replaces=(ref("Btk.", "459", "1", "24"),),
        )
    ),
    (
        "Az egyszerűsített foglalkoztatásról szóló 2010. évi LXXV. törvény (a továbbiakban: Efotv.) a következő 1. § (1a) bekezdéssel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("1a", "1a"),
            position=ref("2010. évi LXXV. törvény", "1", "1a"),
        )
    ),
    (
        "A társadalombiztosítási nyugellátásról szóló 1997. évi LXXXI. törvény 96. § (2) bekezdés h) pontja helyébe a következő rendelkezés lép, egyidejűleg a bekezdés a következő i) ponttal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=AlphabeticPoint,
            expected_id_range=("h", "i"),
            position=ref("1997. évi LXXXI. törvény", "96", "2", "h"),
            replaces=(ref("1997. évi LXXXI. törvény", "96", "2", "h"),),
        )
    ),
    (
        "A Btk. 279. § (1) és (2) bekezdése helyébe a következő rendelkezések lépnek:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("1", "2"),
            position=ref("Btk.", "279", "1"),
            replaces=(ref("Btk.", "279", ("1", "2")),),
        )
    ),
    (
        "A Btk. 283. § (2) és (2a) bekezdése helyébe a következő rendelkezések lépnek:",
        BlockAmendmentMetadata(
            expected_type=Paragraph,
            expected_id_range=("2", "2a"),
            position=ref("Btk.", "283", "2"),
            replaces=(ref("Btk.", "283", ("2", "2a")),),
        )
    ),
    (
        "A Btk. XX. Fejezete a következő alcímmel és 212/A. §-sal kiegészülve lép hatályba:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("212/A", "212/A"),
            position=StructuralReference("Btk."),
        )
    ),
    (
        "A Btk. 349. §-a és a megelőző alcím helyébe a következő rendelkezés és alcím lép:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("349", "349"),
            position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "349")),
            replaces=(
                StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "349")),
                ref("Btk.", "349"),
            )
        )
    ),
    (
        "A Btk. a 300. §-t megelőzően a következő alcímmel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "300")),
        )
    ),
    (
        "A Btk. XXVII. Fejezete a következő alcímmel és 300/A. §-sal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("300/A", "300/A"),
            position=StructuralReference("Btk."),
        )
    ),
    (
        "A Btk. Terrorcselekmény alcíme a következő 316/A. §-sal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Article,
            expected_id_range=("316/A", "316/A"),
            position=ref("Btk.", "316/A"),
        ),
    ),
    (
        "A Btk. Terrorizmus finanszírozása alcíme a következő 318/A. és 318/B. §-sal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Article,
            expected_id_range=("318/A", "318/B"),
            position=ref("Btk.", "318/A"),
        ),
    ),
    (
        "A Btk. a 404. §-t követően a következő alcímmel és 404/A. §-sal kiegészülve lép hatályba:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("404/A", "404/A"),
            position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.AFTER, "404")),
        ),
    ),
    (
        "A Btk. a következő 226/A. §-sal és az azt megelőző alcímmel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("226/A", "226/A"),
            position=StructuralReference("Btk."),
        ),
    ),
    (
        "A Btk. „Új pszichoaktív anyaggal visszaélés” alcíme a következő 184/A–184/D. §-sal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Article,
            expected_id_range=("184/A", "184/D"),
            position=ref("Btk.", "184/A"),
        ),
    ),
    (
        "A Btk. XXIV. Fejezete a következő alcímmel és 261/A. §-sal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("261/A", "261/A"),
            position=StructuralReference("Btk."),
        ),
    ),
    (
        "A Btk. 388/A. §-a és az azt megelőző alcím helyébe a következő alcím és rendelkezés lép:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("388/A", "388/A"),
            position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "388/A")),
            replaces=(
                StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "388/A")),
                ref("Btk.", "388/A"),
            ),
        ),
    ),
    (
        "A Btk. a következő 352/A–352/C. §-sal és az azokat megelőző alcímekkel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("352/A", "352/C"),
            position=StructuralReference("Btk."),
        ),
    ),
    (
        "A Btk. a következő alcímmel és 410/A. §-sal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("410/A", "410/A"),
            position=StructuralReference("Btk."),
        ),
    ),
    (
        "A Btk. 411. §-át megelőző alcím címe és 411. §-a helyébe a következő rendelkezés lép:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("411", "411"),
            position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "411")),
            replaces=(
                StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "411")),
                ref("Btk.", "411"),
            ),
        ),
    ),
    (
        "A Btk. IX. Fejezete a 92/A. §-t követően a következő alcímmel egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.AFTER, "92/A")),
        ),
    ),
    (
        "A Btk. 83. §-t megelőző alcím helyébe a következő alcím lép:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "83")),
            replaces=(
                StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "83")),
            ),
        ),
    ),
    (
        "A Btk. a 124. §-t követően a következő alcímmel és 124/A. §-sal egészül ki:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("124/A", "124/A"),
            position=StructuralReference("Btk.", subtitle=SubtitleReferenceArticleRelative(RelativePosition.AFTER, "124")),
        ),
    ),
    (
        "Az elektronikus információszabadságról szóló 2005. évi XC. törvény (a továbbiakban: Einfotv.) 12. §-át megelőző alcíme helyébe a következő alcím lép:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            position=StructuralReference("2005. évi XC. törvény", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "12")),
            replaces=(
                StructuralReference("2005. évi XC. törvény", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "12")),
            ),
        )
    ),
    (
        "A Büntető Törvénykönyvről szóló 2012. évi C. törvény 350. §-a és az azt megelőző alcím-megjelölése helyébe a következő rendelkezés lép:",
        BlockAmendmentMetadata(
            expected_type=Subtitle,
            expected_id_range=("350", "350"),
            position=StructuralReference("2012. évi C. törvény", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "350")),
            replaces=(
                StructuralReference("2012. évi C. törvény", subtitle=SubtitleReferenceArticleRelative(RelativePosition.BEFORE, "350")),
                ref("2012. évi C. törvény", "350"),
            ),
        )
    ),


    # TODO:
    # (
    #     "A Ptk. Hatodik Könyv Ötödik Része helyébe a következő rész lép:",
    #     BlockAmendmentMetadata(
    #         expected_type=Part,
    #         position=StructuralReference("Ptk."),
    #         replaces=(StructuralReference("Ptk.", book="6", part="5"),),
    #     ),
    # ),
    # (
    #     "A Ptk. Harmadik Könyv VIII. Címének helyébe a következő cím lép:",
    #     BlockAmendmentMetadata(
    #         expected_type=Title,
    #         position=StructuralReference("Ptk."),
    #         replaces=(StructuralReference("Ptk.", book="3", title="8"),),
    #     ),
    # ),
)

# TODO:
# Other simultaneous amendment + insertion cases:
# Full articles: "Az R2. 7. §-a helyébe a következő rendelkezés lép, és az R2. a következő 7/A. §-sal egészül ki"
# "követően" constructs:
#   "A Tfvt. a 17/A. §-t követően a következő 17/B. és 17/C. §-sal egészül ki"
#   "Az Ngt. a 6/C. §-át követően a következő alcímmel és 6/D−K. §-sal egészül ki:"
#   "A helyi adókról szóló 1990. évi C. törvény (a továbbiakban: Htv.) a 11. §-t követően a következő 11/A. §-sal egészül ki"


@pytest.mark.parametrize("s,correct_metadata", BLOCK_AMENDMENT_CASES)  # type: ignore
def test_block_amendment_parsing(s: str, correct_metadata: BlockAmendmentMetadata) -> None:
    parsed = GrammaticalAnalyzer().analyze(s, print_result=True)
    parsed_metadata = parsed.semantic_data
    assert (correct_metadata, ) == parsed_metadata
