import unittest
from rettskriv import book_engine
from tools.ranker_candidates import propose
from tools.context_ranker import keyed_packet,decode_keyed,apply


class CandidateSafeguards(unittest.TestCase):
    def choices(self,text,word):
        eng=book_engine([text],nouncaps=True)
        result=eng.modernise(text)
        i=next(i for i,t in enumerate(result.tokens) if t.text==word)
        return propose(eng,result.tokens[i],result.tokens,i,text)[0]

    def test_habitual_versus_care_reading(self):
        self.assertEqual(self.choices('de plejede at strides','plejede'),{'plejede','pleide'})
        self.assertEqual(self.choices('hun plejede den syge','plejede'), {'plejede'})

    def test_past_forms_not_adjectival_homograph(self):
        choices=self.choices('og skrævede med en Ed','skrævede')
        self.assertIn('skrevet',choices)
        self.assertIn('skrevde',choices)
        self.assertNotIn('skrevede',choices)

    def test_possessive_participle_is_not_ranked_as_finite_verb(self):
        self.assertEqual(self.choices('Hendes opkastede Læbe viste Spor', 'opkastede'),
                         {'opkastede'})
        self.assertIn('oppkastet', self.choices('han opkastede en Vold', 'opkastede'))

    def test_real_attributive_and_coordinated_forms_preserve(self):
        # Elster Tora Trondal block 46; Skram Sjur Gabriel block 15 (MeMo).
        for text, word in [('den fint krusede Flade', 'krusede'),
                           ('Kaliko kantede og forede Tøjstykke', 'kantede')]:
            self.assertEqual(self.choices(text, word), {word})
        self.assertIn('kruset', self.choices('hun krusede sit Haar', 'krusede'))

    def test_real_noun_homographs_unknown_compounds_and_nominal_forms(self):
        # Lie block 109; Kielland blocks 28/109/329, second unseen round.
        for text, word in [('dagede det Passerede op', 'Passerede'),
                           ('den bugtede Strand', 'bugtede'),
                           ('Det lille grumsede Bundfald', 'grumsede'),
                           ('hendes velsignede Smil', 'velsignede'),
                           ('Den krænkede , forskudte Kvinde', 'krænkede')]:
            self.assertEqual(self.choices(text, word), {word})
        self.assertIn('skrevet', self.choices('og skrævede med en Ed', 'skrævede'))

    def test_ocr_form_does_not_become_imperative_after_auxiliary(self):
        # Lie block 34: keep the suspect OCR rather than guess what was printed.
        self.assertEqual(self.choices('Blandingen er flet med den svage Finlap', 'flet'), {'flet'})
        self.assertIn('Flett', self.choices('Flet Haaret!', 'Flet'))
        self.assertIn('Flett', self.choices('Det er. Flet Haaret!', 'Flet'))

    def test_unfootnoted_dialect_ending_preserves(self):
        # Skram block 42 has both forms without attached footnote markers.
        for word in ['Væræ', 'Reisæ']:
            self.assertEqual(self.choices('uti ' + word + ' sett', word), {word})

    def test_initial_command_is_not_assumed_to_be_past(self):
        # Kielland Garman og Worse block 297.
        self.assertEqual(self.choices('raabte : Tjærebrede , tjære .', 'Tjærebrede'),
                         {'Tjærebrede'})
        self.assertEqual(self.choices('Tjærebrede!', 'Tjærebrede'), {'Tjærebrede'})
        self.assertIn('Klaget', self.choices('Klagede han højt?', 'Klagede'))

    def test_ambiguous_verb_lemmas_do_not_mix_dare_and_dry(self):
        self.assertEqual(self.choices('og tørrede sig af paa Forklædet', 'tørrede'),
                         {'tørrede'})

    def test_valid_infinitive_is_not_respelled_to_another_lemma(self):
        choices=self.choices('Melodier der klagede saa saart','klagede')
        self.assertIn('klagde',choices)
        self.assertNotIn('klaka',choices)
        self.assertNotIn('klaket',choices)

    def test_expression_does_not_propose_road_right(self):
        self.assertEqual(self.choices('Ben i Vejret','Vejret'),{'Vejret','været'})

    def test_known_foreign_phrase_blocks_addition_only_in_phrase(self):
        self.assertEqual(self.choices("som mixed drops'",'mixed'),{'mixed'})
        self.assertIn('mikset',self.choices('han mixed noget','mixed'))

    def test_footnoted_unknown_is_preserved(self):
        self.assertEqual(self.choices('men Væræ1 ) æ beisk','Væræ'),{'Væræ'})
        self.assertEqual(self.choices('men Væræ æ beisk','Væræ'), {'Væræ'})


class LandsmalSafeguards(unittest.TestCase):
    def test_auxiliary_i_forms_are_not_assumed_to_be_nouns(self):
        for text, word in [('paa Kyrkjegolve hadde dei stadi No. 1', 'stadi'),
                           ('det hadde han loti lova', 'loti')]:
            eng = book_engine([text], lang='nno', nouncaps=True)
            result = eng.modernise(text)
            i = next(i for i, t in enumerate(result.tokens) if t.text == word)
            self.assertEqual(propose(eng, result.tokens[i], result.tokens, i, text)[0], {word})
        text = 'dei saag Ropingi'
        eng = book_engine([text], lang='nno', nouncaps=True)
        result = eng.modernise(text)
        i = next(i for i, t in enumerate(result.tokens) if t.text == 'Ropingi')
        self.assertIn('ropinga', propose(eng, result.tokens[i], result.tokens, i, text)[0])


class KeyedAnswers(unittest.TestCase):
    def setUp(self):
        self.cases=[dict(id='a',book='a',author='a',split='dev',lang='nob',original='han gik',
                        rank_targets=[dict(at=4,**{'from':'gik'},candidates=['gik','gikk'])])]

    def test_schema_and_decoder_enforce_per_target_options(self):
        _,schema,_=keyed_packet(self.cases)
        self.assertEqual(set(schema['properties']['t0000']['enum']),{'gik','gikk','__KEEP__'})
        answers=decode_keyed(self.cases,{'t0000':'gikk'})
        self.assertEqual(apply(self.cases,[dict(id='a',changes=[])],answers)[0]['changes'],
                         [dict(at=4,**{'from':'gik'},to='gikk')])
        for values in [{},{'t0000':'gikk','extra':'x'},{'t0000':'Gikk'},{'t0000':None}]:
            with self.assertRaises(ValueError):decode_keyed(self.cases,values)

    def test_protected_enum_only_permits_preservation(self):
        self.cases[0]['protected']=[(4,7)]
        _,schema,_=keyed_packet(self.cases)
        self.assertEqual(set(schema['properties']['t0000']['enum']),{'gik','__KEEP__'})
        with self.assertRaises(ValueError):decode_keyed(self.cases,{'t0000':'gikk'})
