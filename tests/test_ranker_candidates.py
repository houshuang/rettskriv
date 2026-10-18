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
        self.assertIn('pleiet',self.choices('hun plejede den syge','plejede'))

    def test_past_forms_not_adjectival_homograph(self):
        choices=self.choices('og skrævede med en Ed','skrævede')
        self.assertIn('skrevet',choices)
        self.assertIn('skrevde',choices)
        self.assertNotIn('skrevede',choices)

    def test_possessive_participle_is_not_ranked_as_finite_verb(self):
        self.assertEqual(self.choices('Hendes opkastede Læbe viste Spor', 'opkastede'),
                         {'opkastede'})
        self.assertIn('oppkastet', self.choices('han opkastede en Vold', 'opkastede'))

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
        self.assertIn('være',self.choices('men Væræ æ beisk','Væræ'))


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
