import re

from presidio_analyzer import Pattern, PatternRecognizer

from .string_match_handler import StringMatchHandler


class WordMatchHandler(StringMatchHandler):
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

    def _get_pattern_recognizer(self, pii_values: list) -> PatternRecognizer | None:
        """Get the pattern recognizer.

        Args:
        ----
            pii_values (list): The PII values

        Returns:
        -------
            PatternRecognizer: The pattern recognizer

        """
        patterns = []
        for v in pii_values:
            if not v:
                continue

            # Create patterns for string values
            patterns.append(
                # Create a pattern for the PII entity
                Pattern(
                    self._PII_ENTITIES,
                    regex=self._PATTERN_TEMPLATE.format(value=re.escape(v)),
                    score=0.8,
                )
            )

            # Words
            for word in re.split(self.split_characters, v):
                word = word.strip()  # noqa: PLW2901
                if len(word) < self.min_word_length:
                    continue
                patterns.append(
                    Pattern(
                        self._PII_ENTITIES,
                        regex=self._PATTERN_TEMPLATE.format(value=re.escape(word)),
                        score=0.8,
                    )
                )

            # Check if the value is a date and create patterns for it
            try:
                ps = self._get_pattern_date(v)
                if ps:
                    patterns.extend(ps)
            except Exception:  # noqa: S110
                pass

        if not patterns:
            return None

        return PatternRecognizer(
            supported_entity=next(iter(self._PII_ENTITIES)), patterns=patterns
        )
