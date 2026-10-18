import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rettskriv.engine import Engine  # noqa: E402

NOB = Engine("nob")
NNO = Engine("nno")


def modern(text: str, nouncaps: bool = True, verse: bool = False, engine: Engine = NOB) -> str:
    engine.nouncaps = nouncaps
    engine.names = set()
    return engine.modernise(text, verse=verse).text


class Spelling(unittest.TestCase):
    def test_reader_sentence(self):
        self.assertEqual(
            modern("Hvad har vi vel at gjøre, for at faa Herren til daglig Gjæst i vort Hjem?"),
            "Hva har vi vel å gjøre, for å få Herren til daglig gjest i vårt hjem?",
        )

    def test_printed_text_round_trips_when_nothing_changes(self):
        text = "Thi Bøn er Hjertets Opløftelse."
        result = NOB.modernise(text)
        self.assertTrue(result.text.startswith("Thi "))

    def test_offsets_map_into_modern_text(self):
        result = NOB.modernise("Han gik ud af Huset.")
        self.assertEqual(result.text, "Han gikk ut av huset.")
        self.assertEqual(result.map_offset(len("Han gik ud af ")), len("Han gikk ut av "))


class NeverChangeMeaning(unittest.TestCase):
    """Old forms whose rule output would be another word."""

    def test_word_substitutions_are_not_made(self):
        for word in ("thi", "ei", "blot", "atter", "stedse"):
            self.assertEqual(modern(f"og {word} saa"), f"og {word} så", word)

    def test_rule_traps(self):
        self.assertEqual(modern("han vil tage det"), "han vil ta det")
        self.assertEqual(modern("med Hovedet"), "med hodet")
        self.assertEqual(modern("i godt Veiret"), "i godt været")
        self.assertEqual(modern("de boede der"), "de bodde der")

    def test_svarede_is_the_verb_not_the_answer(self):
        self.assertEqual(modern("Han svarede ikke."), "Han svarte ikke.")

    def test_at_is_only_the_infinitive_marker_before_an_infinitive(self):
        self.assertEqual(modern("Jeg ved, at han kommer."), "Jeg vet, at han kommer.")
        self.assertEqual(modern("for at gjøre det"), "for å gjøre det")

    def test_kan_hende_stays(self):
        self.assertEqual(modern("det kan hende"), "det kan hende")
        self.assertEqual(modern("han gav hende Bogen"), "han ga henne boken")

    def test_capital_kunde_is_a_customer(self):
        self.assertEqual(modern("han kunde ikke"), "han kunne ikke")
        # left as printed, so the capital stays too
        self.assertEqual(modern("en god Kunde"), "en god Kunde")

    def test_noun_tag_and_verb_tag(self):
        self.assertEqual(modern("under Taget"), "under taket")
        self.assertEqual(modern("han har taget det"), "han har tatt det")

    def test_adjective_participle_stays(self):
        self.assertEqual(modern("den elskede Søn"), "den elskede sønn")
        self.assertEqual(modern("og Faderen elskede ham"), "og faren elsket ham")

    def test_pronoun_i(self):
        self.assertEqual(modern("Hvad have I gjort?"), "Hva har dere gjort?")
        self.assertEqual(modern("I Aar kom han."), "I år kom han.")


class Names(unittest.TestCase):
    def test_name_after_first_name_keeps_capital(self):
        NOB.nouncaps = False
        NOB.learn_book(["Jonas Lie skrev Bøger."])
        result = NOB.modernise("og Lie sagde").text
        self.assertEqual(result, "og Lie sa")


class Nynorsk(unittest.TestCase):
    def test_garborg(self):
        self.assertEqual(
            modern("Ho vardt aldri trøytt av aa sjaa detta livet", nouncaps=False, engine=NNO)[:36],
            "Ho vart aldri trøytt av å sjå detta ",
        )

    def test_never_bokmal(self):
        out = modern("han saag paa deg", nouncaps=False, engine=NNO)
        self.assertEqual(out, "han såg på deg")


if __name__ == "__main__":
    unittest.main()
