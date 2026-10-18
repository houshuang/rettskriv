"""Experimental candidate policy; never authorizes production normalisations.

Guarded proposals retain all valid past paradigms instead of one frequent surface
form. Narrow, documented safeguards address observed foreign phrases, footnoted
unknown forms and two historical lexical readings. This is not language detection.
"""
import re
from rettskriv.text import WORD


def propose(eng, token, tokens, index, text):
    source = token.text
    choices = {source, token.out}
    notes = []
    uncertain = token.reason in {'pending','ambiguous','lexicon-nomatch','archaic-unresolved','unknown'}
    if uncertain:
        choices.update(eng.case(token,s) for s in token.meta.get('candidates','').split('|') if s)
        past = eng.weak_past(token.lower)
        if past:
            choices.add(eng.case(token,past))
    choices = {s for s in choices if s and WORD.fullmatch(s)}
    if not uncertain:
        return choices, notes

    # A word glued to a footnote number may be an explained dialect form/name.
    # Only block experimental additions; baseline handling is untouched.
    following = text[token.start+len(source):]
    if re.match(r'\d+\s*\)', following):
        return {source}, ['footnoted-unknown: editorial review required']
    for match in re.finditer(r'\bmixed\s+drops\b',text,re.I):
        if match.start() <= token.start < match.end():
            return {source}, ['known-foreign-phrase: mixed drops']

    word_indices = [i for i,t in enumerate(tokens) if t.word]
    prev,nxt = eng.neighbours(tokens,index,word_indices)
    if eng.lang == 'nob' and token.lower == 'vejret' and prev and prev.lower == 'i':
        return {source,eng.case(token,'været')}, ['historical-expression: i vejret -> i været']
    if eng.lang == 'nob' and token.lower in {'plejede','pleiede'} and nxt and nxt.lower in {'at','å'}:
        return {source,eng.case(token,'pleide')}, ['habitual-pleie: pleide; not care/tend pleiet']

    if eng.lang == 'nob' and token.lower.endswith('ede') and len(source) >= 6:
        # A possessive + historical -ede + noun can be an attributive
        # participle. Finite-verb candidates do not establish its agreement.
        # Require adjacent words (no intervening punctuation) and a recognised
        # noun; preserve even if this also withholds a legitimate modern form.
        possessives = {'min', 'mit', 'mitt', 'mine', 'din', 'dit', 'ditt', 'dine',
                       'sin', 'sit', 'sitt', 'sine', 'hans', 'hendes', 'hennes',
                       'dens', 'dets', 'vor', 'vort', 'vore', 'vår', 'vårt',
                       'våre', 'deres', 'eders'}
        if (prev and nxt and prev.lower in possessives
                and text[prev.start + len(prev.text):token.start].isspace()
                and text[token.start + len(source):nxt.start].isspace()
                and 'subst' in eng.bank.tags(nxt.out.lower())):
            return {source}, ['attributive-past-form: editorial review required']
        stem = token.lower[:-2]
        infinitives = {stem}
        modern = eng.modern_lower(stem)
        if modern:
            infinitives.add(modern)
        # Do not respell an already valid infinitive into another lexeme:
        # klage -> klake adds unrelated past forms klaka/klaket.
        if not any('verb:inf' in eng.bank.tags(form) for form in infinitives):
            rule = eng.rule_target(stem)
            if isinstance(rule,tuple):
                infinitives.add(rule[0])
            elif rule.startswith('ambiguous:'):
                infinitives.update(rule.split(':',1)[1].split('|'))
        past_forms = set()
        for infinitive in infinitives:
            past_forms.update(eng.bank.inflect(infinitive,'verb:inf','verb:pret'))
        if past_forms:
            # Rank only finite readings here. Adjectival historical contexts must
            # preserve the source, not select a past tense merely for fluency.
            choices = {source} | {eng.case(token,p) for p in past_forms}
            notes.append('past-paradigms: preserve if this occurrence is adjectival')
    return choices, notes
