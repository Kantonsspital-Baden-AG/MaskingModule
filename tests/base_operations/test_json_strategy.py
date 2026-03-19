import json
import unittest

from masking.base_operations.operation_string_match_dict import StringMatchDictOperationBase


class TestStringMatchDictOperation(StringMatchDictOperationBase):
    """Concrete subclass for testing (abstract methods need implementation)."""
    def _mask_data(self, data):
        pass


class TestJsonStrategy(unittest.TestCase):
    """Test that _handle_masking_paths handles None leaf values gracefully."""

    FIRST_NAME = "Valentina"
    LAST_NAME = "Schnurrenberger-Bächli"
    FULL_NAME = f"{LAST_NAME} {FIRST_NAME}"
    DOB = "07.11.1978"

    def setUp(self):
        self.pii_cols = ["_pii_values__name", "_pii_values__vorname", "_pii_values__gebdat"]
        self.op = TestStringMatchDictOperation(
            col_name="json_col",
            pii_cols=self.pii_cols,
            masking_function=lambda x: "<MASKED>",
            allow_list=[],
            deny_keys=[],
            allow_keys=[],
            path_separator=".[$].",
        )
        self.additional_values = {
            "_pii_values__name": self.FULL_NAME,
            "_pii_values__vorname": self.FIRST_NAME,
            "_pii_values__gebdat": self.DOB,
        }

    def _run_masking(self, input_dict):
        """Helper: parse JSON, get paths, call _handle_masking_paths."""
        parsed = self.op._parse_line(json.dumps(input_dict, ensure_ascii=False))
        leaf_to_mask, leaf_to_deny = self.op._get_undenied_and_denied_paths(parsed)
        return self.op._handle_masking_paths(
            line=parsed,
            leaf_to_mask=leaf_to_mask,
            additional_values=self.additional_values,
        )

    def test_null_leaves_do_not_crash(self):
        """Reproduces the TypeError: object of type 'NoneType' has no len()."""
        input_dict = {
            "reason": "Prostatahyperplasie",
            "PATNR": None,
            "comments": f"Patient {self.FULL_NAME}, {self.DOB}",
            "findings": None,
            "diagnosis": "",
        }
        result = self._run_masking(input_dict)
        self.assertIsInstance(result, dict)
        self.assertIsNone(result.get("PATNR"))
        self.assertIsNone(result.get("findings"))

    def test_pii_values_are_masked(self):
        """Verify that actual PII in leaf values gets masked."""
        input_dict = {
            "comments": f"Patient {self.FULL_NAME}, {self.DOB}",
            "reason": "Prostatahyperplasie",
        }
        result = self._run_masking(input_dict)
        self.assertNotIn(self.FIRST_NAME, result.get("comments", ""))
        self.assertNotIn(self.LAST_NAME, result.get("comments", ""))

    def test_all_null_leaves(self):
        """Edge case: all values are None."""
        input_dict = {"a": None, "b": None, "c": None}
        result = self._run_masking(input_dict)
        self.assertIsInstance(result, dict)
        self.assertIsNone(result.get("a"))

    def test_empty_string_leaves(self):
        """Empty strings should not crash."""
        input_dict = {"a": "", "b": "", "c": f"{self.FIRST_NAME} {self.LAST_NAME}"}
        result = self._run_masking(input_dict)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("a"), "")

    def test_nested_null_leaves(self):
        """Nested JSON with null values at various depths."""
        input_dict = {
            "patient": {
                "name": None,
                "info": {"details": f"{self.FIRST_NAME} {self.LAST_NAME}, {self.DOB}"},
            },
            "status": "active",
        }
        result = self._run_masking(input_dict)
        self.assertIsInstance(result, dict)
        self.assertIsNone(result["patient"]["name"])


if __name__ == "__main__":
    unittest.main()