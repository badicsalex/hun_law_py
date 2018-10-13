from collections import namedtuple

from . import Extractor
from .magyar_kozlony import MagyarKozlonyLawRawText

HungarianRawLaw = namedtuple('HungarianRawLaw', ['identifier', 'subject', 'body'])
HungarianRawAmendment = namedtuple('HungarianRawAmendment', ['identifier', 'subject', 'body'])

@Extractor(MagyarKozlonyLawRawText)
def MagyarKozlonyLawClassifier(raw):
    if raw.subject.endswith('módosításáról'):
        yield HungarianRawAmendment(raw.identifier, raw.subject, raw.body)
    else:
        yield HungarianRawLaw(raw.identifier, raw.subject, raw.body)
