from collections import namedtuple

extractors_for_class = {}


def Extractor(extractable_class):
    """Decorator that registers an extractor function.

    Extractor functions can accept a parameter of type 'can_extract_from', and
    yield one or more result objects
    """
    def actual_decorator(fn):
        global extractors_for_class
        if extractable_class not in extractors_for_class:
            extractors_for_class[extractable_class] = []
        extractors_for_class[extractable_class].append(fn)
        return fn
    return actual_decorator
