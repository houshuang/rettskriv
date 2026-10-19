"""Opt-in, experimental dependency evidence for reviewed historical verb families.

No downloads or parser imports occur during ordinary normalization. Both parsers
see the conservative text before any dependency-based replacements are applied.
The lexical gate is independent: a finite parse cannot select a historical sense.
"""
from dataclasses import dataclass

from .historical_verbs import candidates, infinitives


@dataclass(frozen=True)
class Node:
    span: tuple[int, int] | None
    upos: str
    feats: frozenset[str]
    relation: str
    head: tuple[int, int] | None
    children: tuple[tuple[str, tuple[int, int] | None], ...]


def finite(node):
    return (node.upos == 'VERB' and {'VerbForm=Fin', 'Tense=Past', 'Mood=Ind'} <= node.feats
            and 'Voice=Pass' not in node.feats)


def witness(nodes, span, finite_anchors=frozenset()):
    """Return the exact finite coordination path and its single subject head."""
    path = []
    seen = set()
    while span in nodes and span not in seen and len(path) < 5:
        seen.add(span)
        node = nodes[span]
        if not finite(node) or node.relation not in {'root', 'conj', 'advcl', 'ccomp', 'acl:relcl'}:
            return None
        if any(rel.startswith(('aux', 'cop', 'nsubj:pass')) for rel, _ in node.children):
            return None
        if node.relation == 'conj':
            governor = nodes.get(node.head)
            if (governor is None or not finite(governor)
                    or any(rel.startswith(('aux', 'cop', 'nsubj:pass')) for rel, _ in governor.children)):
                return None
        path.append(span)
        subjects = [child for rel, child in node.children if rel == 'nsubj']
        if subjects:
            if len(subjects) != 1 or subjects[0] not in nodes:
                return None
            subject = nodes[subjects[0]]
            if (subject.upos not in {'NOUN', 'PROPN', 'PRON'}
                    or any(rel == 'case' for rel, _ in subject.children)):
                return None
            if span in finite_anchors:
                return tuple(path), subjects[0], ()
            objects = [child for rel, child in node.children if rel == 'obj']
            if (not objects or any(child not in nodes or nodes[child].upos not in {'NOUN', 'PROPN', 'PRON'}
                                   or any(rel == 'case' for rel, _ in nodes[child].children)
                                   for child in objects)):
                return None
            return tuple(path), subjects[0], tuple(sorted(objects))
        if node.relation != 'conj':
            return None
        span = node.head
    return None


def agreement(danish, bokmal, span, finite_anchors=frozenset()):
    a, b = danish.get(span), bokmal.get(span)
    if not a or not b or a.relation != b.relation:
        return False
    # Even a coordinated predicate with its own subject needs the same governor.
    if a.relation == 'conj' and (a.head is None or a.head != b.head):
        return False
    wa, wb = witness(danish, span, finite_anchors), witness(bokmal, span, finite_anchors)
    return wa is not None and wa == wb


def independent_finite(engine, tokens):
    """Finite anchors from original morphology, never from a proposed edit."""
    from .engine import MINOR_TAGS, MODALS
    anchors = set()
    auxiliaries = MODALS | {'have', 'havde', 'hadde', 'har', 'være', 'var', 'bleve', 'blev', 'ble', 'blive'}
    for t in tokens:
        if (not t.word or t.lower.endswith('ede') or t.lower in auxiliaries
                or t.reason == 'protected' or engine.subject_name(t)
                or any(entry.keep for entry in engine.lexicon.get(t.lower, []))):
            continue
        original = engine.bank.tags(t.lower) - MINOR_TAGS
        modern = engine.modern_lower(t.lower)
        if modern is None or modern in auxiliaries:
            continue
        if original == {'verb:pret'} or (not original and modern and engine.bank.tags(modern) - MINOR_TAGS == {'verb:pret'}):
            anchors.add((t.start, t.start + len(t.text)))
    return frozenset(anchors)


def aligned_nodes(document, mapping):
    """Map parser words to exact original spans; splits/merges stay unaligned."""
    nodes = {}
    for sentence in document.sentences:
        spans = {}
        for token in sentence.tokens:
            if len(token.words) == 1:
                spans[token.words[0].id] = mapping.get((token.start_char, token.end_char))
        for word in sentence.words:
            span = spans.get(word.id)
            if span is None:
                continue
            if span in nodes:
                raise ValueError('Parser supplied a duplicate source span')
            nodes[span] = Node(span, word.upos, frozenset((word.feats or '').split('|')),
                               word.deprel, spans.get(word.head), tuple(
                                   (child.deprel, spans.get(child.id))
                                   for child in sentence.words if child.head == word.id))
    return nodes


class DependencyResolver:
    """Experimental second pass. Construct explicitly with installed local models.

    Pass as ``eng.modernise(text, resolver=resolver)``. Model initialization errors
    are explicit; per-text parse failures preserve every output and enter errors.
    Default normalization, verse, other languages, lexicon decisions, names and
    protected spans are never overridden.
    """
    def __init__(self, models, *, processors=None):
        if processors is None:
            import stanza
            if stanza.__version__ != '1.15.0':
                raise RuntimeError('Dependency evidence was evaluated with Stanza 1.15.0; install the dependency-parser extra')
            processors = {lang: stanza.Pipeline(
                lang=lang, dir=str(models), package='default_fast',
                processors='tokenize,pos,lemma,depparse', use_gpu=False,
                download_method=None, verbose=False) for lang in ('da', 'nb')}
        self.processors = processors
        self.errors = []
        self.last_nodes = None

    def apply(self, engine, tokens, *, verse=False):
        self.last_nodes = None
        if verse or engine.lang != 'nob':
            return
        eligible = {}
        for index, t in enumerate(tokens):
            if (not t.word or t.out != t.text or t.reason not in {'archaic-unresolved', 'unknown', 'ambiguous', 'pending'}
                    or t.lower in engine.lexicon or engine.is_name(t)):
                continue
            identity = infinitives(t.lower[:-2]) if t.lower.endswith('ede') else None
            if not identity:
                continue
            following = ''.join(x.text for x in tokens[index + 1:index + 9])
            lexical = candidates(engine.bank, t.lower[:-2], following=following)
            if len(lexical) != 1:
                continue
            past = engine.weak_past(t.lower, following)
            if past and past in lexical[0].forms:
                eligible[(t.start, t.start + len(t.text))] = (t, past)
        if not eligible:
            return
        source, normal, source_map, normal_map = [], [], {}, {}
        offset = 0
        for t in tokens:
            source.append(t.text)
            out = t.out if t.word else t.text
            normal.append(out)
            if t.word:
                span = t.start, t.start + len(t.text)
                source_map[span] = span
                normal_map[(offset, offset + len(out))] = span
            offset += len(out)
        try:
            da = aligned_nodes(self.processors['da'](''.join(source)), source_map)
            nb = aligned_nodes(self.processors['nb'](''.join(normal)), normal_map)
        except Exception as exc:
            # External parsing/alignment is an optional evidence source. Keep
            # cancellation/interrupts visible and internal decision bugs outside
            # this boundary, but never partially apply a failed parser response.
            self.errors.append(f'{type(exc).__name__}: {exc}')
            return
        self.last_nodes = da, nb
        # Make every decision against the same frozen pair of parses.
        anchors = independent_finite(engine, tokens)
        accepted = [(token, past) for span, (token, past) in eligible.items() if agreement(da, nb, span, anchors)]
        for token, past in accepted:
            token.out = engine.case(token, past)
            token.reason = 'dependency:reviewed-lemma-finite-agreement'
