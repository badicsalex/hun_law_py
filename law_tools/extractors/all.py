from . import pdf
from . import magyar_kozlony
from . import extractors_for_class

def do_extraction(to_be_processed_objects):
    """Processes all objects, and returns the end result processed objects."""
    global extractors_for_class
    queue = list(to_be_processed_objects) # simple copy, or listify if not list
    result = []
    while queue:
        data = queue.pop()
        if data.__class__ not in extractors_for_class:
            result.append(data)
        else:
            for extractor_fn in extractors_for_class[data.__class__]:
                for extracted in extractor_fn(data):
                    queue.append(extracted)
    return result
