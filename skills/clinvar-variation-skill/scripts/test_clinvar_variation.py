"""Regression tests for clinvar_variation.py.

Covers a pre-existing upstream defect: `parse_input` was called outside the error handler, so a
non-object stdin payload escaped as an uncaught ValueError instead of the documented
`invalid_input` error object. The defect reproduces on the unmodified upstream snapshot
(life-science-research 1.0.3, clinvar-variation-skill/scripts/clinvar_variation.py line 115).
"""

import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

import requests

MODULE_PATH = Path(__file__).with_name("clinvar_variation.py")
SPEC = importlib.util.spec_from_file_location("clinvar_variation", MODULE_PATH)
clinvar_variation = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(clinvar_variation)


class _FakeResponse:
    def __init__(self, status_code: int, body) -> None:
        self.status_code = status_code
        self._body = body
        self.text = json.dumps(body)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error", response=self)

    def json(self):
        return self._body


class InvalidInputTests(unittest.TestCase):
    """Invalid payloads must return a JSON error object, never raise."""

    def assert_invalid_input(self, payload) -> None:
        result = clinvar_variation.execute(payload)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_input")
        self.assertTrue(result["error"]["message"])

    def test_non_object_payload_reports_invalid_input(self) -> None:
        # Upstream raised ValueError here because parse_input ran before the try block.
        self.assert_invalid_input([])

    def test_string_payload_reports_invalid_input(self) -> None:
        self.assert_invalid_input("VCV000013080")

    def test_missing_action_reports_invalid_input(self) -> None:
        self.assert_invalid_input({})

    def test_unknown_action_reports_invalid_input(self) -> None:
        self.assert_invalid_input({"action": "bogus"})

    def test_search_without_terms_reports_invalid_input(self) -> None:
        self.assert_invalid_input({"action": "search"})

    def test_vcv_without_identifier_reports_invalid_input(self) -> None:
        self.assert_invalid_input({"action": "vcv"})


class OfflineSuccessPathTests(unittest.TestCase):
    """A mocked Clinical Tables response exercises the success path without network access."""

    def test_search_returns_compacted_records(self) -> None:
        body = [
            2,
            ["VCV000013080", "VCV000013081"],
            ["Gene", "Condition"],
            [["VCV000013080", "BRCA1", "breast cancer"], ["VCV000013081", "BRCA2", "breast cancer"]],
        ]
        fake = _FakeResponse(200, body)
        with mock.patch.object(clinvar_variation.requests, "get", return_value=fake) as get:
            result = clinvar_variation.execute({"action": "search", "terms": "BRCA1", "max_items": 1})

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["source"], "clinvar-clinicaltables")
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["record_count_returned"], 1)
        self.assertEqual(result["record_count_available"], 2)
        self.assertEqual(len(result["display_rows"]), 1)
        # Pre-existing semantics kept as is: `truncated` compares the returned page against the
        # upstream total, not against `max_items`. Callers detect the max_items cut by comparing
        # record_count_returned with record_count_available.
        self.assertFalse(result["truncated"])
        self.assertIsNone(result["raw_output_path"])
        self.assertEqual(get.call_args.kwargs["params"]["terms"], "BRCA1")


if __name__ == "__main__":
    unittest.main()
