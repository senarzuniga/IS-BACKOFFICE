"""Entity extraction (heuristic, dependency-free).

This module provides simple rule-based extraction used for tests and
architecture validation. Replace with `spaCy` or an LLM pipeline in
production.
"""

import re
from typing import List, Dict


def extract_entities(text: str) -> List[Dict[str, str]]:
    """Return a list of entity dicts found in `text`.

    Heuristics:
    - sequences of capitalized words (2+ tokens) are treated as ORG
    - appearance of known company tokens is also flagged
    """
    ents = []
    for m in re.finditer(r'([A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+)+)', text):
        ents.append({'text': m.group(0), 'type': 'ORG'})

    for token in ('Ingecart', 'DGM', 'PARA', 'FUNCEN'):
        if token in text and not any(e['text'] == token for e in ents):
            ents.append({'text': token, 'type': 'ORG'})

    return ents
