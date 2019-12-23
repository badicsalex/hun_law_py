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


from hun_law.structure import \
    Article, Paragraph, AlphabeticPoint, NumericPoint, AlphabeticSubpoint, NumericSubpoint

from .utils import quick_parse_structure


def test_simple_block_amendment_1() -> None:
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
    resulting_structure = quick_parse_structure(act_text, parse_block_amendments=True)

    intro = resulting_structure.article("1").paragraph("1").intro
    assert intro is not None
    assert intro.endswith("a következő rendelkezés lép:"), \
        "Intro is correctly split into 'actual intro' and 'context for amendment'"

    amended_structure = resulting_structure.article("1").paragraph("1").block_amendment()
    assert amended_structure.intro is not None
    assert amended_structure.intro.startswith("E törvényben és")
    assert amended_structure.intro.endswith("tartozás, amelynél")

    assert amended_structure.children_type is AlphabeticSubpoint
    assert amended_structure.children is not None
    assert len(amended_structure.children) == 1
    assert isinstance(amended_structure.children[0], AlphabeticSubpoint)
    assert amended_structure.children[0].identifier == "c"
    assert amended_structure.children[0].text is not None
    assert amended_structure.children[0].text.startswith("a kölcsön fedezete")
    assert amended_structure.children[0].text.endswith("készfizető kezesség;")

    amended_structure = resulting_structure.article("1").paragraph("2").block_amendment()
    assert amended_structure.children_type is NumericPoint
    assert amended_structure.children is not None
    assert len(amended_structure.children) == 1
    assert isinstance(amended_structure.children[0], NumericPoint)
    assert amended_structure.children[0].identifier == "4"
    assert amended_structure.children[0].text is not None
    assert amended_structure.children[0].text.startswith("gyűjtőszámlahitel:")
    assert amended_structure.children[0].text.endswith("folyósított kölcsön;")


def test_simple_block_amendment_2() -> None:
    act_text = """
    4. §  (1)  Az Atv. 14. § (1) bekezdése helyébe a következő rendelkezés lép:
               „(1) Az atomenergia-felügyeleti szerv jogszabályban meghatározott esetekben és feltételek szerint az engedélyes
               kérelmére összevont engedélyt, előzetes típusengedélyt, valamint atomerőmű esetén az eltérő fűtőelemkötegek
               alkalmazását célzó átalakításhoz előzetes elvi átalakítási engedélyt, vagy átalakítási engedélyt adhat ki.”
    """
    resulting_structure = quick_parse_structure(act_text, parse_block_amendments=True)
    amended_structure = resulting_structure.article("4").paragraph("1").block_amendment()
    assert amended_structure.children_type is Paragraph
    assert amended_structure.children is not None
    assert len(amended_structure.children) == 1
    assert isinstance(amended_structure.children[0], Paragraph)
    assert amended_structure.children[0].identifier == "1"


def test_complex_block_amendment_1() -> None:
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
    resulting_structure = quick_parse_structure(act_text, parse_block_amendments=True)
    amended_structure = resulting_structure.article("3").paragraph().block_amendment()

    assert amended_structure.children_type is Article
    assert amended_structure.children is not None
    assert len(amended_structure.children) == 1
    assert isinstance(amended_structure.children[0], Article)
    text = amended_structure.children[0].paragraph("2").text
    assert text is not None
    assert text.startswith("A nukleáris létesítmény")

    text = amended_structure.children[0].paragraph("3").text
    assert text is not None
    assert text.startswith("A (2) bekezdéstől eltérően")
    assert text.endswith("a kérelmezőt terheli.")


def test_complex_block_amendment_2() -> None:
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
    resulting_structure = quick_parse_structure(act_text, parse_block_amendments=True)
    amended_structure = resulting_structure.article("8").paragraph("1").block_amendment()

    assert amended_structure.children_type is AlphabeticPoint
    assert amended_structure.children is not None
    assert len(amended_structure.children) == 1
    assert isinstance(amended_structure.children[0], AlphabeticPoint)
    assert amended_structure.children[0].intro == "az atomenergia alkalmazása körében eljáró"

    text = amended_structure.children[0].subpoint("sa").text
    assert text is not None
    assert text.startswith("független műszaki szakértői")
    assert text.endswith("eltérő szabályait;")

    text = amended_structure.children[0].subpoint("sb").text
    assert text is not None
    assert text.endswith("működésének és alkalmazásának szabályait.")


def test_complex_block_amendment_ptk1() -> None:
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
    resulting_structure = quick_parse_structure(act_text, parse_block_amendments=True)
    amended_structure = resulting_structure.article("8").paragraph("1").block_amendment()

    assert amended_structure.children_type is Article
    assert amended_structure.children is not None
    assert len(amended_structure.children) == 1
    assert isinstance(amended_structure.children[0], Article)
    article = amended_structure.children[0]

    assert article.title == "Pénztartozás teljesítésének ideje"
    assert len(article.children) == 4

    text = article.paragraph("2").point("b").text
    assert text is not None
    assert text.startswith("nem állapítható meg")

    text = article.paragraph("3").text
    assert text is not None
    assert text.startswith("Vállalkozások közötti szerződés")

    text = article.paragraph("3").text
    assert text is not None
    assert "(1)–(2)" in text
    assert text.endswith("részében semmis.")


def test_complex_block_amendment_ptk2() -> None:
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

    resulting_structure = quick_parse_structure(act_text, parse_block_amendments=True)
    amended_structure = resulting_structure.article("8").paragraph("1").block_amendment()

    assert amended_structure.children_type is Article
    assert amended_structure.children is not None
    assert len(amended_structure.children) == 1
    assert isinstance(amended_structure.children[0], Article)
    assert amended_structure.children[0].children is not None
    assert len(amended_structure.children[0].children) == 3


def test_block_amendment_range() -> None:
    # Note that this is modified text, the paragraph ids are different in the original
    act_text = """
    1. §  (1)   A Gyvt. 102. §-a a következő (5)–(8) bekezdéssel egészül ki:
                „(5) A hivatásos gondnok egyidejűleg 30 gondnokolt érdekében járhat el, kivéve ha
                a) az adott gondnokoltak igényeinek figyelembevétele alapján a gondnoki feladatok ellátását legfeljebb
                35 gondnokolt egyidejű ellátása nem veszélyezteti, vagy
                b) a hivatásos gondnoki feladatokat kormányzati szolgálati jogviszonyban álló személy látja el.
                (6) Az (1a) bekezdés b) pontjában meghatározott személy egyidejűleg legfeljebb 45 gondnokolt érdekében
                járhat el.
                (7) Ha a hivatásos gondnok hivatásos támogatói feladatokat is ellát, a gondnokoltjainak és támogatott
                személyeinek száma együttesen sem haladhatja meg az (1a) és (1b) bekezdésben foglalt létszámot.
                (8) Ha a hivatásos gondnok tevékenységét munkavégzésre irányuló egyéb jogviszonyban látja el, díjazását úgy
                kell megállapítani, hogy annak összege gondnokoltanként – a gondnoki feladatok mértéke alapján – az öregségi
                nyugdíj mindenkori legkisebb összegének legalább 10%-át elérje.”
    """
    resulting_structure = quick_parse_structure(act_text, parse_block_amendments=True)
    amended_structure = resulting_structure.article("1").paragraph("1").block_amendment()

    assert amended_structure.children_type is Paragraph
    assert amended_structure.children is not None
    assert len(amended_structure.children) == 4
    assert isinstance(amended_structure.children[0], Paragraph)

    assert amended_structure.children[0].children is not None
    assert len(amended_structure.children[0].children) == 2

    assert amended_structure.children[0].identifier == "5"
    assert amended_structure.children[3].identifier == "8"


def test_block_amend_pair() -> None:
    act_text = """
    1. §  (1)   A Gyvt. 69/D. §-a a következő (1a) és (1b) bekezdéssel egészül ki:
                „(1a) A közhasznú szervezet – a (3) bekezdésben foglalt kivétellel – azzal a vér szerinti szülővel és örökbe fogadni
                szándékozó személlyel, akik már ismerik egymást és együtt kérik a nyílt örökbefogadást elősegítő szolgáltatást
                a) megállapodást köt, vagy
                b) – ha a megállapodás megkötésére nem kerül sor – tájékoztatást nyújt, hogy a nyílt örökbefogadást elősegítő
                szolgáltatás a területi gyermekvédelmi szakszolgálatnál is igénybe vehető.
                (1b) Ha a közhasznú szervezet a (3) bekezdésben meghatározott okokról szerez tudomást, öt napon belül írásban
                értesíti az örökbefogadásra való alkalmasságot megállapító, valamint az örökbefogadás engedélyezésére illetékes
                gyámhatóságot.”
    """
    resulting_structure = quick_parse_structure(act_text, parse_block_amendments=True)
    amended_structure = resulting_structure.article("1").paragraph("1").block_amendment()

    assert amended_structure.children_type is Paragraph
    assert amended_structure.children is not None
    assert len(amended_structure.children) == 2
    assert isinstance(amended_structure.children[0], Paragraph)

    assert amended_structure.children[0].identifier == '1a'
    # TODO: point wrap-up detection is based on indentation. I don't know how to handle this case.
    # Maybe detect 'és' or 'vagy' in the previous point.
    # assert amended_structure.children[0].point('b').text.endswith('igénybe vehető.')
    assert isinstance(amended_structure.children[1], Paragraph)
    assert amended_structure.children[1].identifier == '1b'
    assert amended_structure.children[1].text is not None
    assert amended_structure.children[1].text.startswith('Ha a közhasznú szervezet a (3)')


def test_weird_amended_ids_1() -> None:
    act_text = """
        25. §   A légiközlekedésről szóló 1995. évi XCVII. törvény 71. §-a a következő 3a. ponttal egészül ki:
                (A törvény alkalmazásában)
                „3a. gazdálkodó szervezet: a polgári perrendtartásról szóló törvény szerinti gazdálkodó szervezet;”
    """
    resulting_structure = quick_parse_structure(act_text, parse_block_amendments=True)
    amended_structure = resulting_structure.article("25").paragraph().block_amendment()
    assert amended_structure.children_type is NumericPoint
    assert amended_structure.children is not None
    assert len(amended_structure.children) == 1
    assert amended_structure.children[0].identifier == '3a'


def test_weird_amended_ids_2() -> None:
    act_text = """
        1. §    (1) A Gyvt. 5. §-a a következő ny) ponttal egészül ki:
                    (E törvény alkalmazásában)
                    „ny) nevelőszülő: a Ptk. 4:122. § (2) bekezdése szerinti gyermekvédelmi nevelőszülő,”
                (2) A Gyvt. 5. §-a a következő sz) ponttal egészül ki:
                    (E törvény alkalmazásában)
                    „sz) családbafogadó gyám: az a gyámként kirendelt személy, akinél a gyámhatóság a gyermeket ideiglenes hatállyal
                    elhelyezte, vagy akinél a bíróság a gyermeket elhelyezte, vagy aki a gyermeket a gyámhatóság hozzájárulásával
                    családba fogadta, kivéve ha a gyermeket ideiglenes hatállyal nevelőszülőnél, gyermekotthonban vagy más
                    bentlakásos intézményben helyezték el,”
                (3) Az Eht. 188. §-a a következő 31/a. ponttal egészül ki:
                    (E törvény alkalmazásában:)
                    „31/a. Gazdálkodó szervezet: a polgári perrendtartásról szóló törvény szerinti gazdálkodó szervezet.”
"""
    resulting_structure = quick_parse_structure(act_text, parse_block_amendments=True)

    amended_structure = resulting_structure.article("1").paragraph("1").block_amendment()
    assert amended_structure.children_type is AlphabeticPoint
    assert amended_structure.children is not None
    assert amended_structure.children[0].identifier == 'ny'

    amended_structure = resulting_structure.article("1").paragraph("2").block_amendment()
    assert amended_structure.children_type is AlphabeticPoint
    assert amended_structure.children is not None
    assert amended_structure.children[0].identifier == 'sz'

    amended_structure = resulting_structure.article("1").paragraph("3").block_amendment()
    assert amended_structure.children_type is NumericPoint
    assert amended_structure.children is not None
    assert amended_structure.children[0].identifier == '31/a'


def test_alphabetic_alphabetic_subpoint() -> None:
    act_text = """
        75. §     (1)  A Büntető Törvénykönyvről szóló 2012. évi C. törvény (a továbbiakban: Btk.) 28. §-a a következő (1a)
                       bekezdéssel egészül ki:
                       „(1a) Ha az erős felindulásban elkövetett emberölés, a háromévi szabadságvesztésnél súlyosabban
                       büntetendő szándékos súlyos testi sértés, az emberrablás, az emberkereskedelem, a személyi
                       szabadság megsértése, illetve a nemi élet szabadsága és a nemi erkölcs elleni bűncselekmény
                       sértettje a bűncselekmény elkövetésekor a tizennyolcadik életévét még nem töltötte be, az
                       elévülés határidejébe nem számít be az a tartam, amíg a tizennyolcadik életévét be nem tölti,
                       vagy be nem töltötte volna.”
                  (2)  A Btk. 250. § (4) bekezdésében az „(1) bekezdés a) pontjában” szövegrész helyébe az „(1) bekezdésben”
                       szöveg lép.
                  (3)  A Btk. 398. § (3) bekezdés a) pont af) alpontja helyébe a következő rendelkezés lép:
                       [A (2) bekezdés b) pontja alkalmazása szempontjából
                       az alapanyag jelentős mennyiségű, ha]
                       „af) szárított dohány, fermentált dohány vagy vágott dohány esetén az 5 kilogrammot,”
                       (meghaladja.)
    """
    resulting_structure = quick_parse_structure(act_text, parse_block_amendments=True)
    amended_structure = resulting_structure.article("75").paragraph("1").block_amendment()
    assert amended_structure.children_type is Paragraph
    assert amended_structure.children is not None
    assert amended_structure.children[0].identifier == '1a'

    amended_structure = resulting_structure.article("75").paragraph("3").block_amendment()
    assert amended_structure.children_type is AlphabeticSubpoint
    assert amended_structure.children is not None
    assert amended_structure.children[0].identifier == 'af'


def test_numeric_subpoint() -> None:
    act_text = """
        29. § (1) A Magyar Fejlesztési Bank Részvénytársaságról szóló 2001. évi XX. törvény (a továbbiakban: MFB törvény) 3. §
                  (2) bekezdés d) pont 1. alpontja helyébe a következő rendelkezés lép:
                  [Az MFB Zrt. – az (1) bekezdésben meghatározott körben – az alábbi pénzügyi szolgáltatási tevékenységeket végezheti:
                  d) a 2. § b) és c) pontjában szereplő feladatához közvetlenül kapcsolódóan]
                  „1. pénzforgalmi szolgáltatások nyújtása – a pénzforgalmi számlavezetés kivételével – kizárólag jogi személy, egyéni
                  cég és egyéni vállalkozó részére,”
    """
    resulting_structure = quick_parse_structure(act_text, parse_block_amendments=True)

    amended_structure = resulting_structure.article("29").paragraph("1").block_amendment()
    assert amended_structure.children_type is NumericSubpoint
    assert amended_structure.children is not None
    assert amended_structure.children[0].identifier == '1'
