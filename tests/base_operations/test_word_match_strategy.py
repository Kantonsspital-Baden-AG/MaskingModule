import sys
sys.path.insert(0, "src")

import re
import unittest

from masking.utils.word_match_handler import WordMatchHandler


class TestWordMatchHandler(unittest.TestCase):
    """Test WordMatchHandler PII pattern generation and matching."""

    FIRST_NAME = "Valentina"
    LAST_NAME = "Schnurrenberger-Bächli"
    FULL_NAME = f"{LAST_NAME} {FIRST_NAME}"
    DOB = "07.11.1978"

    def setUp(self):
        pii_examples = {
            "name": f"{self.FULL_NAME}, {self.DOB}",
            "name2": "Huengerbuhl test",
            "name3": "Müller",
            "name4": "Günthe&Karaarduç",
        }
        self.handler = WordMatchHandler(pii_cols=list(pii_examples.keys()))
        self.handler.allow_list = []
        pii_values = self.handler._get_pii_values(pii_examples)
        self.recognizer = self.handler._get_pattern_recognizer(pii_values)

    def _has_match(self, text: str) -> bool:
        """Check if any pattern matches the text."""
        return any(re.findall(p.regex, text) for p in self.recognizer.patterns)

    def _count_matches(self, text: str) -> int:
        """Count how many patterns match the text."""
        return sum(1 for p in self.recognizer.patterns if re.findall(p.regex, text))

    def test_recognizer_is_created(self):
        """Pattern recognizer should be created with patterns."""
        self.assertIsNotNone(self.recognizer)
        self.assertGreater(len(self.recognizer.patterns), 0)

    def test_exact_name_match(self):
        """Exact PII values should be detected."""
        self.assertTrue(self._has_match(f"Patient {self.FIRST_NAME} wurde entlassen"))
        self.assertTrue(self._has_match(f"Bericht für {self.LAST_NAME}"))

    def test_umlaut_to_digraph(self):
        """Umlaut variants (ü→ue, ä→ae) should be detected."""
        self.assertTrue(self._has_match("Patient Mueller wurde entlassen"))
        self.assertTrue(self._has_match("Bericht Baechli"))

    def test_digraph_to_umlaut(self):
        """Digraph variants (ue→ü) should be detected."""
        self.assertTrue(self._has_match("Hüngerbuhl wurde kontaktiert"))

    def test_ascii_stripping_full_value(self):
        """ASCII-stripped full value (ç→c) should be detected."""
        self.assertTrue(self._has_match("Kontakt mit Gunthe&Karaarduc"))

    def test_date_exact_format(self):
        """Date in original format should be detected."""
        self.assertTrue(self._has_match("geboren am 07.11.1978"))

    def test_word_splitting_hyphenated(self):
        """Individual words from hyphenated names should be detected."""
        self.assertTrue(self._has_match("Schnurrenberger hat angerufen"))
        self.assertTrue(self._has_match("Frau Bächli ist da"))

    def test_word_splitting_umlaut_variant(self):
        """Umlaut variant of split word should be detected."""
        self.assertTrue(self._has_match("Bachli wurde informiert"))

    def test_short_words_ignored(self):
        """Words shorter than min_word_length (3) should not generate patterns."""
        patterns_text = [p.regex for p in self.recognizer.patterns]
        # No pattern should match a 1-2 char standalone word
        for pt in patterns_text:
            matches = re.findall(r'\\b(.+?)\\b', pt)
            for m in matches:
                clean = m.replace('\\', '')
                if clean and not any(c in clean for c in ['|', '(', ')', '?']):
                    self.assertGreaterEqual(len(clean), 3, f"Short pattern found: {clean}")

    def test_no_match_on_clean_text(self):
        """Text without any PII should not match."""
        self.assertFalse(self._has_match("Anmeldung zur Zuweisung"))
        self.assertFalse(self._has_match("Prostatahyperplasie"))

    def test_no_match_on_partial_overlap(self):
        """Partial word overlap should not trigger a match."""
        self.assertFalse(self._has_match("Schnurrbartpflege"))

    def test_multiple_pii_in_one_text(self):
        """Text containing multiple PII values should match multiple patterns."""
        text = f"{self.FIRST_NAME} {self.LAST_NAME}, {self.DOB}, Müller, Huengerbuhl"
        self.assertGreater(self._count_matches(text), 3)


if __name__ == "__main__":
    unittest.main()