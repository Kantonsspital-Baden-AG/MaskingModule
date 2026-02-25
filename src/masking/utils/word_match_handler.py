import re
import unicodedata

from presidio_analyzer import Pattern, PatternRecognizer

from .string_match_handler import StringMatchHandler


class WordMatchHandler(StringMatchHandler):

    # Umlaut mappings (both directions)
    _DIGRAPH_TO_UMLAUT = {
        "ue": "ü", "Ue": "Ü",
        "oe": "ö", "Oe": "Ö",
        "ae": "ä", "Ae": "Ä",
    }

    _UMLAUT_TO_DIGRAPH = {
        "ü": "ue", "Ü": "Ue",
        "ö": "oe", "Ö": "Oe",
        "ä": "ae", "Ä": "Ae",
    }

    def __init__(
        self,
        pii_cols: list[str] | None = None,
        min_word_length: int | None = None,
        split_characters: str | None = None,
        **kwargs: dict,
    ) -> None:
        r"""Initialize the Presidio Handler.

        Args:
        ----
            pii_cols (list[str]): list of PII columns
            min_word_length (int): minimum length of a word to be considered for matching
            split_characters (str): regex pattern for characters to split words (default: r"[\s,\-]+")
                                    Default: split on whitespace, comma, and hyphen
            **kwargs: The keyword arguments

        """
        super().__init__(**kwargs)

        self.pii_cols = pii_cols or []
        self.min_word_length = min_word_length or 4
        self.split_characters = split_characters or r"[\s,\-]+"

    def _get_umlaut_variants(self, text: str) -> list[str]:
        """Get all umlaut variants of a text.

        Returns both the digraph→umlaut and umlaut→digraph versions.

        Args:
        ----
            text (str): The text to convert

        Returns:
        -------
            list[str]: List of unique variants (excluding the original)

        """
        # digraph → umlaut
        to_umlaut = text
        for source, target in self._DIGRAPH_TO_UMLAUT.items():
            to_umlaut = to_umlaut.replace(source, target)

        # umlaut → digraph
        to_digraph = text
        for source, target in self._UMLAUT_TO_DIGRAPH.items():
            to_digraph = to_digraph.replace(source, target)

        return [v for v in {to_umlaut, to_digraph} if v != text]
    

    def _get_ascii_variant(self, text: str) -> str | None:
        """Remove diacritics/accents from text.
        
        E.g. 'Karaarduç' → 'Karaarduc', 'René' → 'Rene'
        """
        normalized = unicodedata.normalize('NFD', text)
        ascii_variant = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        return ascii_variant if ascii_variant != text else None

    def _get_pattern_recognizer(self, pii_values: list) -> PatternRecognizer | None:
        # Expand PII values with umlaut variants
        expanded = []
        for v in pii_values:
            expanded.append(v)
            expanded.extend(self._get_umlaut_variants(v))
            ascii_variant = self._get_ascii_variant(v)
            if ascii_variant:
                expanded.append(ascii_variant)

        regex_set = set()
        for v in expanded:
            if not v:
                continue

            # Full value
            regex_set.add(self._PATTERN_TEMPLATE.format(value=re.escape(v)))

            # Words
            for word in re.split(self.split_characters, v):
                word = word.strip() # noqa: PLW2901
                if len(word) < self.min_word_length:
                    continue
                regex_set.add(self._PATTERN_TEMPLATE.format(value=re.escape(word)))

            # Dates
            try:
                ps = self._get_pattern_date(v)
                if ps:
                    for p in ps:
                        regex_set.add(p.regex)
            except Exception:
                pass

        if not regex_set:
            return None

        patterns = [
            Pattern(self._PII_ENTITIES, regex=r, score=0.8)
            for r in regex_set
        ]

        return PatternRecognizer(
            supported_entity=next(iter(self._PII_ENTITIES)), patterns=patterns
        )