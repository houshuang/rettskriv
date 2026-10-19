"""Recognize complete nonfinite correlative adjuncts for optional parser evidence.

These source classifications never change spelling or authorize a replacement.
"""
import re

# ODS offer- lists Offergilde sb.: https://ordnet.dk/ods/ordbog?query=offer-
SOURCE_NOUNS = frozenset({'offergilde'})
# Faye1852 explicitly identifies the farm: "af Gaarden Hlade kaldtes Hladejarlen".
SOURCE_PLACES = frozenset({'hlade'})


def complete_pp(engine, phrase):
    words = phrase.split()
    if len(words) < 3 or words[0] != 'ved' or words[1] not in {'denne', 'dette', 'en', 'et'}:
        return False
    if any(w in {'paa', 'på'} for w in words[2:]):
        if len(words) < 5 or words[-2] not in {'paa', 'på'}:
            return False
        place = re.sub(r'\*\)$', '', words[-1])
        if not place.isalpha() or not place[0].isupper():
            return False
        if place.lower() not in SOURCE_PLACES and not engine.bank.proper_only(place):
            return False
        words = words[:-2]
    if not 3 <= len(words) <= 5 or not all(w.isalpha() for w in words):
        return False
    noun = engine.modern_lower(words[-1].lower())
    tags = engine.bank.tags(noun) if noun else frozenset()
    if words[-1].lower() not in SOURCE_NOUNS and ('subst' not in tags or any(t.startswith('verb') for t in tags)):
        return False
    return all((form := engine.modern_lower(w.lower())) and 'adj' in engine.bank.tags(form)
               for w in words[2:-1])


def certified_adjunct(engine, tokens, target):
    source = ''.join(t.text for t in tokens)
    match = re.search(
        r',\s+(?:saavel|såvel)\s+(?P<left>[^,;:.!?]+),\s+(?P<som>som)\s+'
        r'(?P<right>[^,;:.!?]+),\s*$', source[:target[0]])
    if not match or not all(complete_pp(engine, match.group(k)) for k in ('left', 'right')):
        return None
    if any(t.word and match.start() <= t.start < match.end() and t.reason == 'protected' for t in tokens):
        return None
    return (match.start(), match.end()), (match.start('som'), match.end('som'))


def reduced_view(tokens, cut, *, normal=False):
    """Remove the certified span in a parser-only copy, keeping exact source maps."""
    pieces, mapping, offset = [], {}, 0
    inserted = False
    for token in tokens:
        start, end = token.start, token.start + len(token.text)
        if start < cut[1] and end > cut[0]:
            if token.word:
                if not cut[0] <= start < end <= cut[1]:
                    raise ValueError('Adjunct boundary splits a word')
                continue
            before = token.text[:max(0, cut[0] - start)]
            after = token.text[max(0, cut[1] - start):] if end > cut[1] else ''
            middle = '' if inserted else ' '
            inserted = True
            part = before + middle + after
        else:
            part = token.out if normal and token.word else token.text
            if token.word:
                mapping[(offset, offset + len(part))] = (start, end)
        pieces.append(part)
        offset += len(part)
    return ''.join(pieces), mapping
