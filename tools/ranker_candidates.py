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

    if eng.lang == 'nob' and token.lower.endswith('æ'):
        return {source}, ['dialect-ending: final æ requires editorial review']

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
    if eng.lang == 'nno' and token.lower.endswith('i'):
        pos = word_indices.index(index)
        before = tokens[word_indices[pos - 2]] if pos >= 2 else None
        auxiliaries = {'har', 'hadde', 'hev', 'heve'}
        auxiliary = prev and prev.lower in auxiliaries
        if prev and prev.lower in {'eg', 'du', 'han', 'ho', 'me', 'vi', 'de', 'dei'}:
            auxiliary = before and before.lower in auxiliaries
        if auxiliary:
            start = before if prev.lower not in auxiliaries else prev
            gap = text[start.start + len(start.text):token.start]
            if not re.search(r'[.,;:!?]', gap):
                # Historical i can mark a participle as well as a definite noun.
                # Do not turn stadi/loti into unrelated noun-only stada/lota
                # just because a suffix substitution finds a modern bank form.
                if any(c != source and eng.bank.tags(c.lower()) == {'subst'} for c in choices):
                    return {source}, ['auxiliary-i-form: participle or noun unresolved']
    if (prev and prev.lower in {'er', 'var', 'blev', 'ble', 'blir', 'bliver', 'har', 'havde', 'hadde'}
            and text[prev.start + len(prev.text):token.start].isspace()):
        filtered = {c for c in choices if c == source or eng.bank.tags(c.lower()) != {'verb:imp'}}
        if filtered != choices:
            choices = filtered
            notes.append('auxiliary-context: excluded imperative-only candidates')
            if choices == {source}:
                return choices, notes
    if eng.lang == 'nob' and token.lower == 'vejret' and prev and prev.lower == 'i':
        return {source,eng.case(token,'været')}, ['historical-expression: i vejret -> i været']
    if eng.lang == 'nob' and token.lower in {'plejede','pleiede'} and nxt and nxt.lower in {'at','å'}:
        return {source,eng.case(token,'pleide')}, ['habitual-pleie: pleide; not care/tend pleiet']

    if eng.lang == 'nob' and token.lower.endswith('ede') and len(source) >= 6:
        # Finite paradigms alone cannot establish attributive agreement.
        # A nearby noun (possibly behind coordinated adjectives) is ambiguous
        # without a directly preceding personal subject. Preserve rather than
        # constructing a whole noun phrase or letting fluency choose its reading.
        subjects = {'jeg', 'du', 'han', 'hun', 'vi', 'man'}
        if (prev and prev.lower in {'det', 'den', 'de'}
                and (not nxt or nxt.lower not in subjects | {'de', 'dem', 'mig', 'dig', 'ham', 'hende', 'os', 'sig'})):
            return {source}, ['determiner-past-form: nominal or attributive reading unresolved']
        if not prev or prev.lower not in subjects:
            pos = word_indices.index(index)
            last = token
            for j in word_indices[pos + 1:pos + 5]:
                other = tokens[j]
                gap = text[last.start + len(last.text):other.start]
                if not re.fullmatch(r'[\s,]+', gap):
                    break
                tags = eng.bank.tags(other.out.lower())
                closed = {'prep', 'pron', 'konj', 'sbu', 'det', 'adv', 'interj'}
                readings = tags | eng.bank.tags(other.lower)
                noun = 'subst' in tags or (eng.nouncaps and other.capitalised)
                if noun and not readings & closed:
                    return {source}, ['attributive-past-form: editorial review required']
                if other.lower != 'og' and not tags & {'adj', 'adj:part', 'adv'}:
                    break
                last = other
        # An isolated/utterance-initial -ede may be a command or historical
        # infinitive. Only allow this expansion with an inverted subject.
        if token.initial and (not nxt or nxt.lower not in subjects | {'de'}):
            return {source}, ['initial-past-form: finite reading not established']
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
        lemmas = {a.lemma for infinitive in infinitives
                  for a in eng.bank.analyses(infinitive)
                  if {'verb', 'inf'} <= set(a.tags.split()) and 'pass' not in a.tags.split()}
        if len(lemmas) > 1:
            return {source}, ['multiple-verb-lemmas: historical sense unresolved']
        past_forms = set()
        for infinitive in infinitives:
            past_forms.update(eng.bank.inflect(infinitive,'verb:inf','verb:pret'))
        if past_forms:
            # Rank only finite readings here. Adjectival historical contexts must
            # preserve the source, not select a past tense merely for fluency.
            choices = {source} | {eng.case(token,p) for p in past_forms}
            notes.append('past-paradigms: preserve if this occurrence is adjectival')
    return choices, notes
