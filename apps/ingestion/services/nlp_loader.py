import spacy
from django.conf import settings

_nlp = None


def load_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load(
            settings.SPACY_MODEL,
            disable=["ner"],
        )
    return _nlp
