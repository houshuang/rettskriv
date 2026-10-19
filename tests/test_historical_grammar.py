"""Real-book repairs plus counterexamples to tempting syntactic shortcuts."""
import unittest
import json
from pathlib import Path
from rettskriv import book_engine, modernise


class HistoricalGrammar(unittest.TestCase):
    def test_reviewed_book_sentences(self):
        cases = json.loads((Path(__file__).parent / 'fixtures/historical-grammar.json').read_text())
        for case in cases:
            with self.subTest(case=case['id']):
                eng = book_engine([case['original']], lang=case['lang'], year=case['year'], nouncaps=case['nouncaps'])
                eng.names.update(case['names'])  # learned from the complete source book
                result = eng.modernise(case['original'])
                token = next(t for t in result.tokens if t.start == case['at'] and t.word)
                self.assertEqual(token.text, case['word'])
                self.assertEqual(token.out, case['expected'])

    def word(self, text, word, lang='nob', nouncaps=True):
        engine = book_engine([text], lang=lang, nouncaps=nouncaps)
        result = engine.modernise(text)
        return next(t.out for t in result.tokens if t.text == word)

    def test_faye_passive_inflections_are_not_finite_past(self):
        # Faye1852 pieces003,008,016: printed plural participles after blive.
        for text, word, expected in [
            ('mange Slag bleve leverede', 'leverede', 'levert'),
            ('Buxer, der bleve snørede om Benene', 'snørede', 'snørt'),
            ('Disse Slotte bleve imidlertid tappert forsvarede.', 'forsvarede', 'forsvart'),
        ]:
            with self.subTest(text=text):
                self.assertEqual(self.word(text, word), expected)

    def test_passive_infinitives_keep_voice_and_restore_marker(self):
        for text in ['fortjener at bevares', 'fortjene iøvrigt at erindres', 'fortjener at nævnes']:
            self.assertEqual(self.word(text, 'at'), 'å')
        self.assertEqual(self.word('No bad han dei um aa forlikast', 'aa', lang='nno'), 'å')
        self.assertEqual(modernise('de bruges til Smykker', nouncaps=True), 'de brukes til smykker')
        self.assertEqual(self.word('I dettes sted indførtes', 'I', nouncaps=False), 'I')

    def test_same_lemma_agreeing_forms(self):
        self.assertEqual(self.word('sin adopterede Søn Carl Johan', 'adopterede'), 'adopterte')
        self.assertEqual(self.word('Skindet af det slagtede Kid', 'slagtede'), 'slaktede')
        self.assertEqual(self.word('Hendes opkastede Læbe viste Spor', 'opkastede'), 'oppkastede')

    def test_raeder_regressions_are_preserved(self):
        for text, word in [
            ('Kristina havde udmerkede evner', 'udmerkede'),
            ('de blev fremmede for sine folk', 'fremmede'),
            ('Fra den tid af udvidede Rom sig', 'udvidede'),
            ('men trods dette egtede Maria ham', 'egtede'),
            ('under den udmerkede presten Kjel Stub sig', 'udmerkede'),
            ('Dette bevægede Karl til at forlade Sjælland', 'bevægede'),
            ('Alt dette svækkede Polen', 'svækkede'),
        ]:
            with self.subTest(text=text):
                self.assertEqual(self.word(text, word, nouncaps=False), word)

    def test_names_are_not_automatically_subjects(self):
        for text in ['Han gav Olaf udmærkede Gaver.', 'Tak, udmærkede Peter!',
                     'Du, udmærkede Peter, hjalp os.']:
            self.assertEqual(self.word(text, 'udmærkede'), 'udmærkede')

    def test_demonstratives_are_not_automatically_determiners(self):
        for text, word in [('De udmærkede Soldater for deres Mod.', 'udmærkede'),
                           ('De forøgede Antallet.', 'forøgede'),
                           ('De unge forøgede Antallet.', 'forøgede'),
                           ('Det forøgede Antallet.', 'forøgede')]:
            self.assertEqual(self.word(text, word), word)

    def test_shared_form_does_not_cross_a_passive_coordination(self):
        for text in ['Børnene bleve vaskede, klædte og forsynede med Mad.',
                     'Børnene bleve efter mange lange Dage og Nætter i den meget store Sal vaskede, klædte og forsynede med Mad.']:
            self.assertEqual(self.word(text, 'forsynede'), 'forsynede')

    def test_resultative_object_predicates_are_not_past_tense(self):
        for text in ['Han fik Brevene besvarede.', 'Han ønskede Brevene besvarede.',
                     'At faa Brevene besvarede var vigtigt.']:
            self.assertEqual(self.word(text, 'besvarede'), 'besvarede')

    def test_existing_ambiguous_and_dialect_preservation(self):
        for text, word in [('Han voksede Bordet.', 'voksede'),
                           ('Kaliko kantede og forede Tøjstykke', 'kantede'),
                           ('Tjærebrede!', 'Tjærebrede'),
                           ('vi var saa bedrøvede', 'bedrøvede')]:
            self.assertEqual(self.word(text, word), word)
