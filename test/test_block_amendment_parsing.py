# Copyright 2019 Alex Badics <admin@stickman.hu>
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

from hun_law.utils import IndentedLine, IndentedLinePart, object_to_dict_recursive


from hun_law.structure import Reference, OutgoingReference, Article, Paragraph, AlphabeticPoint, AlphabeticSubpoint, NumericPoint
from hun_law.parsers.structure_parser import ActStructureParser
from hun_law.parsers.semantic_parser import ActBlockAmendmentParser

import pytest
import json


def absref(act=None, article=None, paragraph=None, point=None, subpoint=None):
    return Reference(act, article, paragraph, point, subpoint)


def ref(article=None, paragraph=None, point=None, subpoint=None):
    return Reference(None, article, paragraph, point, subpoint)


def quick_parse_structure(act_text):
    lines = []
    for l in act_text.split('\n'):
        parts = []
        skip_spaces = True
        for char in l:
            if char == ' ' and skip_spaces:
                continue
            skip_spaces = False
            parts.append(IndentedLinePart(5, char))
        lines.append(IndentedLine(parts))
    act = ActStructureParser.parse("2345 évi 1. törvény", "About testing", lines)
    act = ActBlockAmendmentParser.parse(act)
    print(json.dumps(object_to_dict_recursive(act), indent='  ', ensure_ascii=False))
    return act


def test_simple_block_amendment_1():
    act_text = """
        1. §      (1)  A devizakölcsönök törlesztési árfolyamának rögzítéséről és a lakóingatlanok kényszerértékesítésének
                       rendjéről szóló 2011. évi LXXV. törvény (a továbbiakban: Tv.) 1. § (1) bekezdés 1. pont c) alpontja
                       helyébe a következő rendelkezés lép:
                       (E törvényben és az e törvény felhatalmazása alapján kiadott
                       jogszabályban: 1. devizakölcsön: a természetes személy mint adós vagy adóstárs és a pénzügyi intézmény
                       között létrejött olyan kölcsönszerződés alapján fennálló tartozás, amelynél)
                       „c) a kölcsön fedezete a Magyar Köztársaság területén lévő lakóingatlanon alapított zálogjog vagy a Magyar
                       Köztársaság 2005. évi költségvetéséről szóló 2004. évi CXXXV. törvény 44. §-a alapján vállalt állami készfizető
                       kezesség;”
                  (2)  A Tv. 1. § (1) bekezdés 4. pontja helyébe a következő rendelkezés lép:
                       (E törvényben és az e törvény felhatalmazása alapján kiadott jogszabályban:)
                       „4. gyűjtőszámlahitel: gyűjtőszámlahitelre vonatkozó hitelkeret-szerződés alapján a devizakölcsön törlesztése során
                       a rögzített árfolyam alkalmazása miatt a hiteladós által meg nem fizetett törlesztőrészlet-hányad finanszírozására,
                       a devizakölcsön tekintetében hitelezőnek minősülő pénzügyi intézmény által a hiteladósnak forintban,
                       a devizakölcsön ingatlanfedezetével azonos ingatlanra érvényesíthető jelzálogjog vagy a Magyar Köztársaság
                       2005. évi költségvetéséről szóló 2004. évi CXXXV. törvény 44. §-a alapján vállalt állami készfizető kezesség fedezete
                       mellett a rögzített árfolyam alkalmazásának időszaka alatt folyósított kölcsön;”
    """
    resulting_structure = quick_parse_structure(act_text)

    assert resulting_structure.article("1").paragraph("1").intro.endswith("a következő rendelkezés lép:"), \
        "Intro is correctly split into 'actual intro' and 'context for amendment'"

    amended_structure = resulting_structure.article("1").paragraph("1").block_amendment()
    assert amended_structure.intro.startswith("E törvényben és")
    assert amended_structure.intro.endswith("tartozás, amelynél")

    assert amended_structure.children_type is AlphabeticSubpoint
    assert len(amended_structure.children) == 1
    assert amended_structure.children[0].identifier == "c"
    assert amended_structure.children[0].text.startswith("a kölcsön fedezete")
    assert amended_structure.children[0].text.endswith("készfizető kezesség;")

    amended_structure = resulting_structure.article("1").paragraph("2").block_amendment()
    assert amended_structure.children_type is NumericPoint
    assert len(amended_structure.children) == 1
    assert amended_structure.children[0].identifier == "4"
    assert amended_structure.children[0].text.startswith("gyűjtőszámlahitel:")
    assert amended_structure.children[0].text.endswith("folyósított kölcsön;")


def test_simple_block_amendment_2():
    act_text = """
    4. §  (1)  Az Atv. 14. § (1) bekezdése helyébe a következő rendelkezés lép:
               „(1) Az atomenergia-felügyeleti szerv jogszabályban meghatározott esetekben és feltételek szerint az engedélyes
               kérelmére összevont engedélyt, előzetes típusengedélyt, valamint atomerőmű esetén az eltérő fűtőelemkötegek
               alkalmazását célzó átalakításhoz előzetes elvi átalakítási engedélyt, vagy átalakítási engedélyt adhat ki.”
    """
    resulting_structure = quick_parse_structure(act_text)
    amended_structure = resulting_structure.article("4").paragraph("1").block_amendment()
    assert amended_structure.children_type is Paragraph
    assert amended_structure.children[0].identifier == "1"


def test_complex_block_amendment_1():
    act_text = """
    3. §      Az Atv. 13. § helyébe a következő rendelkezés lép:
               „13. § (1) A nukleáris létesítménnyel összefüggő hatósági engedélyezési eljárás során biztosítani kell a szakértőként
               eljáró személyek vagy szervezetek függetlenségét. Az egyes eljárásokban kirendelt, illetve felkért szakértők vagy
               szakértő szervezetek egymással nem állhatnak semmilyen függőségi viszonyban, nem lehetnek az eljárásban
               érintett ügyfelek hozzátartozói, nem állhatnak semmilyen közvetlen vagy közvetett gazdasági kapcsolatban
               a kérelmezővel, továbbá a hatósági eljárásban megjelölt technológia-szállítójával vagy annak versenytársával.
               (2) A nukleáris létesítmény nukleáris biztonságára lényeges hatással levő tevékenység engedélyezése esetében
               a kérelmet megalapozó dokumentációt független szakértői értékelésnek kell alávetni. A független szakértői
               értékelést a kérelmező a hatósági eljárásban, az arra vonatkozó nukleáris biztonsági követelmények szerint nyújtja
               be az atomenergia-felügyeleti szervhez.
               (3) A (2) bekezdéstől eltérően új nukleáris létesítmény létesítési engedélyezési eljárásában a független műszaki
               szakértői véleményeztetés nem előfeltétele az engedélyezési eljárásnak. Ha a kérelmező nem vagy nem teljes
               körűen nyújt be független szakértői véleményt, akkor az atomenergia felügyeleti szerv azt hivatalból készítteti el,
               amelynek költsége a kérelmezőt terheli.”
    """
    resulting_structure = quick_parse_structure(act_text)
    amended_structure = resulting_structure.article("3").paragraph().block_amendment()

    assert amended_structure.children_type is Article
    assert len(amended_structure.children) == 1
    assert amended_structure.children[0].paragraph(2).text.startswith("A nukleáris létesítmény")
    assert amended_structure.children[0].paragraph(3).text.startswith("A (2) bekezdéstől eltérően")
    assert amended_structure.children[0].paragraph(3).text.endswith("a kérelmezőt terheli.")


def test_complex_block_amendment_2():
    act_text = """
    8. §      (1)  Az Atv. 67. § s) pontja helyébe a következő rendelkezés lép: (Felhatalmazást kap a Kormány, hogy
               rendeletben szabályozza)
                    „s) az atomenergia alkalmazása körében eljáró
                    sa) független műszaki szakértői tevékenység folytatásának szabályait, végzésének feltételeit, a vonatkozó
                    összeférhetetlenségi szabályokat, a szakértői szakterületeket, az e tevékenységre jogosító engedély kiadásának
                    rendjét, a tevékenységre jogosító engedély iránti kérelmezési eljárásban részt vevő minősítő bizottságok tagjaira
                    és összeférhetetlenségére vonatkozó feltételeket, a szakvélemény tartalmi elemeit és elkészítésére irányadó
                    szabályokat, a szakértői tevékenységre jogszabályban vagy hatósági határozatban előírt kötelezettségek be
                    nem tartása esetén alkalmazandó jogkövetkezményeket, valamint a külföldi szakértőre vonatkozó, az EGT-állam
                    állampolgár szakértőitől eltérő szabályait;
                    sb) műszaki szakértő szervezet minősítésének, nyilvántartásának, működésének és alkalmazásának szabályait.”
    """
    resulting_structure = quick_parse_structure(act_text)
    amended_structure = resulting_structure.article("8").paragraph("1").block_amendment()

    assert amended_structure.children_type is AlphabeticPoint
    assert len(amended_structure.children) == 1
    assert amended_structure.children[0].intro == "az atomenergia alkalmazása körében eljáró"
    assert amended_structure.children[0].subpoint("sa").text.startswith("független műszaki szakértői")
    assert amended_structure.children[0].subpoint("sa").text.endswith("eltérő szabályait;")
    assert amended_structure.children[0].subpoint("sb").text.endswith("működésének és alkalmazásának szabályait.")


def test_complex_block_amendment_ptk1():
    act_text = """
    8. §       (1)  A Ptk. 6:130. §-a a következő szöveggel lép hatályba:
                    „6:130. § [Pénztartozás teljesítésének ideje]
                    (1) Ha a felek a szerződésben a pénztartozás teljesítésének idejét nem határozták meg, a pénztartozást a jogosult
                    fizetési felszólításának vagy számlájának kézhezvételétől számított harminc napon belül kell teljesíteni. Ha
                    a pénztartozás fizetésére kötelezett szerződő hatóság, a szerződő hatóságnak nem minősülő vállalkozással kötött
                    szerződése esetén pénztartozását a jogosult fizetési felszólításának vagy számlájának kézhezvételétől számított
                    harminc napon belül köteles teljesíteni, ebben az esetben a számla kézhezvételének napja nem képezheti a felek
                    között érvényes megállapodás tárgyát.
                    (2) A jogosult teljesítésétől számított harminc napon belül kell teljesíteni a pénztartozást, ha
                    a) a jogosult fizetési felszólításának vagy számlájának kézhezvétele a jogosult teljesítését (vállalkozási szerződés
                    esetén az átadás-átvételi eljárás befejezését) megelőzte;
                    b) nem állapítható meg egyértelműen a jogosult fizetési felszólítása vagy számlája kézhezvételének időpontja; vagy
                    c) a kötelezettnek fizetési felszólítás vagy számla bevárása nélkül teljesítenie kell fizetési kötelezettségét.
                    (3) Vállalkozások közötti szerződés esetén az e § rendelkezéseitől a jóhiszeműség és tisztesség követelményének
                    megsértésével egyoldalúan és indokolatlanul a jogosult hátrányára eltérő szerződési feltételt – mint tisztességtelen
                    kikötést – a jogosult megtámadhatja. Pénztartozás fizetésére kötelezett szerződő hatóságnak szerződő
                    hatóságnak nem minősülő vállalkozással kötött szerződése esetén a pénztartozás teljesítésére kikötött idő az
                    (1)–(2) bekezdésben meghatározott határidőket csak akkor haladhatja meg, ha a szerződésben a felek
                    a pénztartozás halasztott teljesítésében állapodtak meg, feltéve hogy a szerződés jellege miatt ez tényszerűen
                    indokolt; a pénztartozás teljesítésére kikötött idő ebben az esetben sem haladhatja meg a hatvan napot.
                    Pénztartozás fizetésére kötelezett szerződő hatóságnak szerződő hatóságnak nem minősülő vállalkozással kötött
                    szerződése esetén a pénztartozás teljesítésére kikötött idő a hatvan napot meghaladó részében semmis.
                    (4) Vállalkozások közötti szerződés esetén az ellenkező bizonyításáig tisztességtelen kikötésnek kell tekinteni
                    a jóhiszeműség és tisztesség követelményének megsértésével egyoldalúan és indokolatlanul a jogosult hátrányára
                    eltérő olyan szerződési feltételt, amely a pénztartozás teljesítésére az (1) és (2) bekezdésben foglaltaktól eltérő,
                    hatvan napnál hosszabb határidőt határoz meg. Pénztartozás fizetésére kötelezett szerződő hatóságnak szerződő
                    hatóságnak nem minősülő vállalkozással kötött szerződése esetén a pénztartozás teljesítésére az (1)–(2) bekezdés
                    rendelkezéseitől eltérően, a jóhiszeműség és tisztesség követelményének megsértésével egyoldalúan és
                    indokolatlanul a jogosult hátrányára kikötött olyan határidőt, amely a hatvan napot nem haladja meg – mint
                    tisztességtelen kikötést –, a jogosult megtámadhatja.”
    """
    resulting_structure = quick_parse_structure(act_text)
    amended_structure = resulting_structure.article("8").paragraph("1").block_amendment()

    assert amended_structure.children_type is Article
    assert len(amended_structure.children) == 1
    article = amended_structure.children[0]

    assert article.title == "Pénztartozás teljesítésének ideje"
    assert len(article.children) == 4
    assert article.paragraph("2").point("b").text.startswith("nem állapítható meg")
    assert article.paragraph("3").text.startswith("Vállalkozások közötti szerződés")
    assert "(1)–(2)" in article.paragraph("3").text
    assert article.paragraph("3").text.endswith("részében semmis.")


def test_complex_block_amendment_ptk2():
    # The main part here is the "junk" EMPTY line between the article header and
    # its contents.
    act_text = """
    8. §   (1) A Ptk. 3:305. §-a a következő szöveggel lép hatályba:
               „3:305. § [Kötvény helyett részvény igénylése és a kötvény részvénnyé történő átváltozása]

                (1) Az átváltoztatható kötvény tulajdonosa a kötvény futamidején belül, a közgyűlés által meghatározott időtartam
                alatt írásban – nyomdai úton előállított kötvények esetén a kötvényeknek az igazgatóság részére történő
                benyújtásával – kötvényei helyébe részvényt igényelhet.
                (2) Az átváltoztatható kötvény átváltoztatásáról szóló nyilatkozat megtételével, az átváltozó kötvény átváltozására
                előírt feltétel bekövetkeztével a kötvénytulajdonos jogosulttá válik részvényutalványra.
                (3) Az (1) bekezdés szerinti bejelentés megtételére rendelkezésre álló időtartam lejártát vagy az átváltozó kötvény
                átváltozására előírt feltétel bekövetkeztét követően az igazgatóság – az átváltozó kötvény esetén a feltétel
                bekövetkeztének megállapítása mellett – haladéktalanul intézkedik az alaptőke-emelés nyilvántartásba történő
                bejegyzése iránt azzal, hogy az alapszabály módosítására nincs szükség. Az alaptőke-emelés során a nyilvántartásba
                vételre és a részvény kiadására, jóváírására vonatkozó rendelkezéseket megfelelően alkalmazni kell.”
    """

    resulting_structure = quick_parse_structure(act_text)
    amended_structure = resulting_structure.article("8").paragraph("1").block_amendment()

    assert amended_structure.children_type is Article
    assert len(amended_structure.children) == 1
    assert len(amended_structure.children[0].children) == 3
