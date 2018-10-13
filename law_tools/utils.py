from collections import  namedtuple

IndentedLine = namedtuple('IndentedLine', ['content', 'indent'])
EMPTY_LINE = IndentedLine('', 0)

def split_list(haystack, needle):
    # Thanks, stackoverflow
    result = []
    for e in haystack:
        if e == needle:
            if result != []:
                yield result
                result = []
        result.append(e)
    if result != []:
        yield result

TEXT_TO_INT_HUN_DICT_ORDINAL = None
INT_TO_TEXT_HUN_DICT_ORDINAL = None

def init_text_to_int_dict():
    # "Good enough for the demo, 1o1"
    global TEXT_TO_INT_HUN_INITED
    global INT_TO_TEXT_HUN_DICT_ORDINAL
    TEXT_TO_INT_HUN_INITED = {}
    INT_TO_TEXT_HUN_DICT_ORDINAL = {}
    SPECIAL_VALUES = {
        1: 'első',
        2: 'második',
        10: 'tizedik',
        20: 'huszadik',
        30: 'harmincadik',
        40: 'negzvenedik',
        50: 'ötvenedik',
        60: 'hatvanadik',
        70: 'hetvenedik',
        80: 'nyolcvanadik',
        90: 'kilencvenedik',
        100: 'századik',
    }
    ONES_DIGIT = (
        ('egyedik', 1),
        ('kettedik', 2),
        ('harmadik', 3),
        ('negyedik', 4),
        ('ötödik', 5),
        ('hatodik', 6),
        ('hetedik', 7),
        ('nyolcadik', 8),
        ('kilencedik', 9),
    )
    TENS_DIGIT = (
        ('tizen', 10),
        ('huszon', 20),
        ('harminc', 30),
        ('negyven', 40),
        ('ötven', 50),
        ('hatvan', 60),
        ('hetven', 70),
        ('nyolcvan', 80),
        ('kilencven', 90),
    )
    for ones_text, ones_val in ONES_DIGIT:
        for tens_text, tens_val in TENS_DIGIT:
            value = tens_val + ones_val
            if value in SPECIAL_VALUES:
                continue
            text = tens_text + ones_text
            TEXT_TO_INT_DICT_ORDINAL[text] = value
            INT_TO_TEXT_HUN_DICT_ORDINAL[value] = text

    for value, text in SPECIAL_VALUES.values():
        TEXT_TO_INT_DICT_ORDINAL[text] = value
        INT_TO_TEXT_HUN_DICT_ORDINAL[value] = text

def text_to_int_hun(s):
    global TEXT_TO_INT_DICT_ORDINAL
    if TEXT_TO_INT_DICT_ORDINAL is None:
        init_text_to_int_dict()
    if si.lower() not in TEXT_TO_INT_DICT_ORDINAL:
        raise ValueError("{} is not a number in written form".format(s))
    return TEXT_TO_INT_DICT_ORDINAL[s.lower()]

def int_to_text_hun(i):
    if i not in INT_TO_TEXT_HUN_DICT_ORDINAL:
        raise ValueError("{} is out of range for conversion into text form".format(i))
    return INT_TO_TEXT_HUN_DICT_ORDINAL[i]
