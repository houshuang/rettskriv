"""Real-book repairs plus counterexamples to tempting syntactic shortcuts."""
import unittest
import json
from pathlib import Path
from rettskriv import book_engine, modernise


class HistoricalGrammar(unittest.TestCase):
    def test_finite_syntax_does_not_resolve_historical_lexical_sense(self):
        # Erichsen 1 piece048: a genuine finite verb, but modern vandet means
        # rejected/disliked, not watered. Do not silently select that homograph.
        self.assertEqual(self.word('du vandede blomsten', 'vandede'), 'vandede')
        self.assertEqual(self.word('Han vandede Maden.', 'vandede'), 'vandede')

    def test_reviewed_book_sentences(self):
        fixtures = Path(__file__).parent / 'fixtures'
        cases = json.loads((fixtures / 'historical-grammar.json').read_text())
        cases += json.loads((fixtures / 'historical-recovery.json').read_text())
        cases += json.loads((fixtures / 'historical-clauses.json').read_text())
        cases += json.loads((fixtures / 'historical-final.json').read_text())
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

    def test_reporting_relative_and_adjective_evidence(self):
        for text, word, expected in [
            ('„Er hun her,“ svarede Finn.', 'svarede', 'svarte'),
            ('„Inden Du bliver færdig,“ erklærede Gyvra.', 'erklærede', 'erklærte'),
            ('tvende Konger, der beilede til hende.', 'beilede', 'beilet'),
            ('Grumhed, der stundom udartede til oprørende Grumhed.', 'udartede', 'utartet'),
            ('vare blevne ansporede til at angribe ham.', 'ansporede', 'ansporet'),
            ('Den slet forsynede og desuden slet anførte norske Hær maatte vige.', 'forsynede', 'forsynte'),
        ]:
            with self.subTest(text=text):
                self.assertEqual(self.word(text, word), expected)

    def test_recovery_does_not_assume_relative_der_or_quoted_speech(self):
        for text, word in [
            ('Han fandt her simple Folk, der udmærkede Mænd.', 'udmærkede'),
            ('Han fandt her simple Folk, der udmærkede.', 'udmærkede'),
            ('Han sagde, at de besvarede en efter en blev lagt bort.', 'besvarede'),
            ('Han sagde, at de besvarede et Øjeblik laa paa Bordet.', 'besvarede'),
            ('et Sted, der udmærkede Mænd boede.', 'udmærkede'),
            ('Han betragtede dem som udmærkede Mænd.', 'udmærkede'),
            ('Han roste røde og udmærkede Gaver.', 'udmærkede'),
            ('De vare blevne fremmede for deres Folk.', 'fremmede'),
            ('De vare blevne udmærkede Soldater.', 'udmærkede'),
            ('Han kaldte dem „Venner“ erklærede Fjender.', 'erklærede'),
        ]:
            with self.subTest(text=text):
                self.assertEqual(self.word(text, word), word)

    def test_locative_der_keeps_agreement(self):
        self.assertEqual(self.word('Vi saa der udmærkede Mænd.', 'udmærkede'), 'utmerkede')

    def test_complete_clause_frames(self):
        for text, word, expected in [
            ('Island, hvor de oprettede en Fristat.', 'oprettede', 'opprettet'),
            ('de troede, at Guden selv fortærede.', 'fortærede', 'fortærte'),
            ('Uagtet de kom fra Norge, bevarede de dog deres Frihed.', 'bevarede', 'bevarte'),
            ('De sloge eller adsplittede Fienden.', 'adsplittede', 'adsplittet'),
            ('Istedetfor Langeldr, bleve Ovnstuer indrettede, og Halm blev strøet.', 'indrettede', 'innrettet'),
            ('Da de kom, forenede Peder sig med dem.', 'forenede', 'forente'),
        ]:
            with self.subTest(text=text):
                self.assertEqual(self.word(text, word), expected)

    def test_clause_proofs_require_complete_unambiguous_constituents(self):
        for text, word in [
            ('Han sagde, at de besvarede en efter en.', 'besvarede'),
            ('Han sagde, at de besvarede et Øjeblik laa paa Bordet.', 'besvarede'),
            ('Han saae dem og udmærkede Mænd.', 'udmærkede'),
            ('Han malede sig og udmærkede Mænd.', 'udmærkede'),
            ('Han ønskede Brevene besvarede og forseglede.', 'besvarede'),
            ('De havde elleve Langskibe samlede.', 'samlede'),
            ('De bleve fremmede.', 'fremmede'),
            ('bleve store ukjendte Mænd udmærkede.', 'udmærkede'),
        ]:
            with self.subTest(text=text):
                self.assertEqual(self.word(text, word), word)

    def test_relative_complete_subjects_and_objects(self):
        for text, word, expected in [
            ('Uroligheder, som hans mange allerede voxne Sønner foraarsagede.', 'foraarsagede', 'forårsaket'),
            ('Det gjaldt Landet, da udvortes Fiender afværgede en Borgerkrig.', 'afværgede', 'avverget'),
            ('en Hær, som dog intet udrettede, da Folket stod imod.', 'udrettede', 'utrettet'),
            ('Hakon røbede tidlig megen Forstand.', 'røbede', 'røpet'),
            ('som hans mange allerede besvarede Breve laa.', 'besvarede', 'besvarte'),
            ('Da Krigen kom, svigtede ei hans Kjæmper.', 'svigtede', 'sviktet'),
            ('en Konge, der erobrede Jerusalem 1099.', 'erobrede', 'erobret'),
            ('Paa samme Tid udmærkede en norsk Mand Cort Axelsson sig.', 'udmærkede', 'utmerket'),
            ('Da Krigen kom, forenede Frederik sig med dem.', 'forenede', 'forente'),
            ('For at vinde Krigen, forpligtede Rusland sig til dette.', 'forpligtede', 'forpliktet'),
        ]:
            with self.subTest(text=text):
                self.assertEqual(self.word(text, word), expected)

    def test_relative_and_name_evidence_cannot_skip_verb_or_object_predicate(self):
        for text, word in [
            ('at faa Breve besvarede', 'besvarede'),
            ('Han ved, at en elsker fremmede.', 'fremmede'),
            ('Han ved, at en elsker forlovede.', 'forlovede'),
            ('at få Brevene besvarede', 'besvarede'),
            ('Han gav Hakon udmærkede Gaver.', 'udmærkede'),
            ('med Frederik udmærkede Gaver', 'udmærkede'),
            ('Han bad Olaf og Frederik forenede om Hjælp.', 'forenede'),
        ]:
            with self.subTest(text=text):
                self.assertEqual(self.word(text, word), word)

    def test_genitive_subject_and_reporting_clause_require_full_evidence(self):
        for text, word, expected in [
            ('Frederikshalds Indvaanere vanslægtede ei heller fra deres Fædre.', 'vanslægtede', 'vanslektet'),
            ('Asbjørn reiste sig nu og erklærede i en kraftfuld Tale, at Bønderne ei vilde forsage Troen.', 'erklærede', 'erklærte'),
            ('Han ønskede Kongens Breve besvarede ikke blot hurtigt, men grundigt.', 'besvarede', 'besvarede'),
            ('Han roste sig nu og udmærkede Mænd.', 'udmærkede', 'udmærkede'),
            ('Han vaskede sig nu og saarede Soldater.', 'saarede', 'saarede'),
        ]:
            with self.subTest(text=text):
                self.assertEqual(self.word(text, word), expected)
