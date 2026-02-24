import datetime
import re
from typing import ClassVar

from dateparser import parse
from presidio_analyzer import Pattern, PatternRecognizer


class WordMatchHandler:
    # Entities to be detected as PII
    _PII_ENTITIES: ClassVar[set[str]] = {"PATIENT_DATA"}

    # Define a pattern template for matching PII values
    # Explanation:
    # •	(?i): case-insensitive, (?x): allow comments and whitespace
    # •	\b{value}\b: matches the value as a whole word
    # •	(?<=\n|\t){value}(?=\n|\t): matches the value at the start of a line or after a tab
    # •	(?<=\W){value}(?=\W): matches the value surrounded by non-word characters
    _PATTERN_TEMPLATE: ClassVar[str] = r"""(?ix)
                (
                    \b{value}\b
                    |
                    (?<=\n|\t){value}(?=\n|\t)
                    |
                    (?<=\W){value}(?=\W)
                )
                """

    def __init__(self, 
                 pii_cols: list[str] | None = None, 
                 min_word_length: int | None = None,
                 split_characters: str | None = None, 
                 **kwargs: dict) -> None:
        """Initialize the Presidio Handler.

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


    def _get_pii_values(self, line: dict) -> list[str]:
        """Get the PII values from a line.

        Args:
        ----
            line (dict): The line to extract the PII values from

        Returns:
        -------
            list[str]: The PII values

        """
        return [
            pii_value
            for col in self.pii_cols
            if (pii_value := str(line.get(col)).strip())
            and (pii_value not in self.allow_list)
        ]

    def _get_pattern_date(self, line: str | datetime.datetime) -> str:
        """Get the date pattern from a line.

        Args:
        ----
            line (str | datetime.datetime): The line to extract the date from

        Returns:
        -------
            str: The date pattern

        """
        patterns = []

        try:
            # Parse the line as a date
            date = parse(line)
        except Exception:
            return patterns

        # Create patterns for different date formats
        patterns.extend([
            Pattern(
                self._PII_ENTITIES,
                regex=self._PATTERN_TEMPLATE.format(
                    value=re.escape(date.strftime("%d-%m-%Y"))
                ),
                score=0.8,
            ),
            Pattern(
                self._PII_ENTITIES,
                regex=self._PATTERN_TEMPLATE.format(
                    value=re.escape(date.strftime("%Y-%m-%d"))
                ),
                score=0.8,
            ),
            Pattern(
                self._PII_ENTITIES,
                regex=self._PATTERN_TEMPLATE.format(
                    value=re.escape(date.strftime("%d.%m.%Y"))
                ),
                score=0.8,
            ),
            Pattern(
                self._PII_ENTITIES,
                regex=self._PATTERN_TEMPLATE.format(
                    value=re.escape(date.strftime("%Y/%m/%d"))
                ),
                score=0.8,
            ),
            Pattern(
                self._PII_ENTITIES,
                regex=self._PATTERN_TEMPLATE.format(
                    value=re.escape(date.strftime("%d/%m/%Y"))
                ),
                score=0.8,
            ),
            Pattern(
                self._PII_ENTITIES,
                regex=self._PATTERN_TEMPLATE.format(
                    value=re.escape(date.strftime("%m/%d/%Y"))
                ),
                score=0.8,
            ),
        ])
        return patterns

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
            # TODO: hyphen, comma as hyperparameters
            for word in re.split(self.split_characters, v):
                word = word.strip()
                if len(word) < self.min_word_length:
                    continue
                patterns.append(
                    Pattern(
                        self._PII_ENTITIES, 
                        regex=self._PATTERN_TEMPLATE.format(value=re.escape(word)), 
                        score=0.8
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
