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

from hun_law.parsers.grammatical_analyzer import GrammaticalAnalyzer
from hun_law.structure import Reference


import pytest


def ref(act=None, article=None, paragraph=None, point=None, subpoint=None):
    return Reference(act, article, paragraph, point, subpoint)


ABBREVIATIONS = {
    "Flt.": "1991. évi IV. törvény",
}

CASES = [
    (
        "A hegyközségekről szóló 2012. évi CCXIX. törvény (a továbbiakban: Hktv.) 28. §-a helyébe a következő rendelkezés lép:",
        "                        [                      ]                         <     >                                     ",
        [ref("2012. évi CCXIX. törvény", '28')],
        ["2012. évi CCXIX. törvény"],
    ),
    (
        "A Magyarország 2013. évi központi költségvetéséről szóló 2012. évi CCIV. törvény 44/B. és 44/C. §-a helyébe a következő rendelkezés lép:",
        "                                                         [                     ] <   >    <       >                                     ",
        [
            ref("2012. évi CCIV. törvény", "44/B"),
            ref("2012. évi CCIV. törvény", "44/C"),
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
        None,
        None,
        None,
    ),
    (
        "Az adás-vételnek nem minősülő, a föld tulajdonjogának átruházásáról szóló szerződést (ezen alcímben a továbbiakban: szerződés) – annak létrejöttétől számított 8 napon belül – a tulajdonjogot szerző félnek (csere esetén a cserepartnerek valamelyikének) a mezőgazdasági igazgatási szerv részére kell megküldeni jóváhagyás céljából.",
        None,
        None,
        None,
    ),
    (
        # Note the abbreviation without the rigid referenc to the Act.
        "A haszonbérletre e törvény rendelkezései mellett a Polgári Törvénykönyv (a továbbiakban: Ptk.), valamint a földről szóló törvény haszonbérletre vonatkozó szabályait is alkalmazni kell.",
        None,
        None,
        None,
    ),
    (
        "Ha az (1) és a (2) bekezdésben meghatározott előzetes.",
        "      < >      <             >                        ",
        [
            ref(None, None, "1"),
            ref(None, None, "2"),
        ],
        []
    ),
    (
        "Ha létrejött adás-vételi szerződést a 23. § (4) bekezdésének a) vagy b) pontjában foglalt esetek fennállása alapján jóváhagyja.",
        "                                      <                       >      <          >                                              ",
        [
            ref(None, "23", "4", "a"),
            ref(None, "23", "4", "b"),
        ],
        []
    ),
    (
        # Test that quoted references are not parsed
        "Az Flt. 30. § (1) bekezdés a) pontjában az „a 25. § (1) bekezdésének c)–d) pontjában” szövegrész helyébe az „a 25. § (1) bekezdésének d) pontjában” szöveg lép.",
        "   [  ] <                             >                                                                                                                        ",
        [ref("1991. évi IV. törvény", "30", '1', 'a'), ],
        ["1991. évi IV. törvény", ],
    ),
    (
        # Ptk purposefully left out of ABBREVIATIONS to test missing abbreviations.
        "A Ptk. 3:222. § (1) bekezdése a következő szöveggel lép hatályba:",
        "       <                    >                                    ",
        [ref(None, "3:222", "1")],
        [],
    ),
    (
        "Az 1–30. §, a 31. § (1) és (3)−(5) bekezdése, a 32–34. §, a 35. § (1) és (3)–(5) bekezdése, a 36. §, a 37. § "
        "(1) és (3)–(5) bekezdése, a 38. §, a 39. § (1) és (3)–(5) bekezdése, a 40–59. §, a 60. § (1) bekezdése, a 61. § (1), (2) "
        "és (7) bekezdése, 62–66. §, a 67. § (5) bekezdés a)–d) és g) pontja, a 68. § (1)–(3), (10) és (12)–(15) bekezdése, "
        "a 68. § (17) bekezdés 1., 2., 4., 6–8., 10–13., 15., 16., 18–20. és 25. pontja, a 69–76. §, a 77. § (3) és (4) bekezdése, a 78–82. §, "
        "a 181. §, a 182. §, a 192. § a)–b), valamint d)–n) pontja és a 193. § 2014. március 15-én lép hatályba.",
        "   <     >    <       >    <               >    <      >    <       >    <               >    <   >    <     "
        "  >    <               >    <   >    <       >    <               >    <      >    <                 >    <       >  < > "
        "   <           >  <      >    <                      >    <       >    <           >  <  >    <                 >  "
        "  <                    >  <>  <>  <  >  <    >  < >  < >  <    >    <        >    <      >    <       >    <           >    <      >  "
        "  <    >    <    >    <          >           <          >      <    >                                  ",
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
            ref(None, '61', '1'),
            ref(None, '61', '2'),
            ref(None, '61', '7'),
            ref(None, ('62', '66')),
            ref(None, '67', '5', ('a', 'd')),
            ref(None, '67', '5', 'g'),
            ref(None, '68', ('1', '3')),
            ref(None, '68', '10'),
            ref(None, '68', ('12', '15')),
            ref(None, '68', '17', '1'),
            ref(None, '68', '17', '2'),
            ref(None, '68', '17', '4'),
            ref(None, '68', '17', ('6', '8')),
            ref(None, '68', '17', ('10', '13')),
            ref(None, '68', '17', '15'),
            ref(None, '68', '17', '16'),
            ref(None, '68', '17', ('18', '20')),
            ref(None, '68', '17', '25'),
            ref(None, ('69', '76')),
            ref(None, '77', '3'),
            ref(None, '77', '4'),
            ref(None, ('78', '82')),
            ref(None, '181'),
            ref(None, '182'),
            ref(None, '192', None, ('a', 'b')),
            ref(None, '192', None, ('d', 'n')),
            ref(None, '193'),
        ],
        [],
    ),
]


@pytest.fixture(scope="module")
def analyzer():
    return GrammaticalAnalyzer()


@pytest.mark.parametrize("s,positions,refs,act_refs", CASES)
def test_parse_results_are_stable(analyzer, s, positions, refs, act_refs):
    first_result = analyzer.analyze(s)
    for i in range(3):
        other_result = analyzer.analyze(s)
        assert first_result == other_result, ("Parsing always yields  the same result", s)


@pytest.mark.parametrize("s,positions,refs,act_refs", CASES)
def test_parse_results(analyzer, s, positions, refs, act_refs):
    if refs is None:
        return
    parsed = analyzer.analyze(s)
    parsed.indented_print()
    parsed_refs = []
    parsed_act_refs = []
    parsed_pos_string = [" "] * len(s)
    for ref, start, stop in parsed.get_references(ABBREVIATIONS):
        parsed_pos_string[start] = '<'
        parsed_pos_string[stop] = '>'
        parsed_refs.append(ref)
    for act_ref, start, stop in parsed.get_act_references(ABBREVIATIONS):
        parsed_pos_string[start] = '['
        parsed_pos_string[stop] = ']'
        parsed_act_refs.append(act_ref)
    parsed_pos_string = "".join(parsed_pos_string)
    assert refs == parsed_refs
    assert act_refs == parsed_act_refs
    if positions is not None:
        assert positions == parsed_pos_string


ABBREVIATION_CASES = (
    (
        "A hegyközségekről szóló 2012. évi CCXIX. törvény (a továbbiakban: Hktv.) 28. §-a helyébe a következő rendelkezés lép:",
        [('Hktv.', '2012. évi CCXIX. törvény')]
    ),
    (
        "A pénzügyi tranzakciós illetékről szóló 2012. évi CXVI. törvény (a továbbiakban: Pti. törvény) 7. § (1) bekezdése helyébe a következő rendelkezés lép:",
        [('Pti.', '2012. évi CXVI. törvény')]
    ),
    (
        "A Magyarország 2013. évi központi költségvetéséről szóló 2012. évi CCIV. törvény 44/B. és 44/C. §-a helyébe a következő rendelkezés lép:",
        []
    ),
    (
        "A Kvtv. 72. §-a a következő (9)–(12) bekezdésekkel egészül ki:",
        []
    ),
)


@pytest.mark.parametrize("s,abbrevs", ABBREVIATION_CASES)
def test_new_abbreviations(analyzer, s, abbrevs):
    parsed = analyzer.analyze(s)
    new_abbrevs = list(parsed.get_new_abbreviations())
    assert new_abbrevs == abbrevs
