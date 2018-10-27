from law_tools.hun_law.structure import Act

from . import Extractor
from .magyar_kozlony import MagyarKozlonyLawRawText


@Extractor(MagyarKozlonyLawRawText)
def MagyarKozlonyLawClassifier(raw):
    # TODO: assert for 10. § (2)(c) c): 'a cím utolsó szavához a „-ról”, „-ről” rag kapcsolódjon.'
    yield Act(raw.identifier, raw.subject, raw.body)
