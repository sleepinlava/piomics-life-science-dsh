#!/usr/bin/env python3
"""HMDB lookup with explicit handling of the site's bot protection.

HMDB publishes no public API (the API page asks academic and commercial groups to contact the team
by email) and serves a Cloudflare managed challenge to scripted clients on every path, including its
download tree. Checked 2026-09-28.

This client therefore does two things the generic REST helper cannot:

* it distinguishes a Cloudflare challenge from a network error or an empty result, and answers with
  an actionable `source_unavailable` error instead of a bare HTTP 403;
* it still performs the documented search request, so it works unchanged if the site later allows
  the client, or when it is run from a network the site does not challenge.

The licensed alternative is a local copy of the published archives: download
https://hmdb.ca/system/downloads/current/hmdb_metabolites.zip (MetaboCard XML, about 910 MB) or
structures.zip (SDF, about 92 MB) through a browser, then query the extracted file directly. HMDB
data is released under CC BY-NC 4.0; commercial use requires permission from the authors.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError as exc:  # pragma: no cover
    requests = None
    REQUESTS_IMPORT_ERROR = exc
else:
    REQUESTS_IMPORT_ERROR = None

HMDB_BASE = "https://hmdb.ca"
SEARCH_PATH = "unearth/q"
DOWNLOADS_URL = f"{HMDB_BASE}/system/downloads/current/"
LICENSE_NOTE = "HMDB data is CC BY-NC 4.0; commercial use needs permission from the authors."
CHALLENGE_MARKERS = ("just a moment", "cf-mitigated", "cf-chl", "attention required")
DEFAULT_TIMEOUT_S = 30
DEFAULT_MAX_RESULTS = 10


def error(code: str, message: str, warnings: list[str] | None = None) -> dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message}, "warnings": warnings or []}


def _require_str(name: str, value: Any, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise ValueError(f"`{name}` is required.")
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"`{name}` must be a non-empty string.")
    return value.strip()


def _require_int(name: str, value: Any, default: int) -> int:
    if value is None:
        return default
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"`{name}` must be a positive integer.")
    return value


def is_challenge(response: Any) -> bool:
    """True when the response is a bot-protection interstitial rather than HMDB content."""
    if response.status_code not in (403, 503):
        return False
    header_blob = " ".join(f"{key}: {value}" for key, value in response.headers.items()).lower()
    body = (response.text or "")[:2000].lower()
    return any(marker in header_blob or marker in body for marker in CHALLENGE_MARKERS)


def parse_input(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Input must be one JSON object.")
    return {
        "query": _require_str("query", payload.get("query"), required=True),
        "category": _require_str("category", payload.get("category")) or "metabolites",
        "max_items": _require_int("max_items", payload.get("max_items"), DEFAULT_MAX_RESULTS),
        "timeout_sec": _require_int("timeout_sec", payload.get("timeout_sec"), DEFAULT_TIMEOUT_S),
        "save_raw": payload.get("save_raw") is True,
        "raw_output_path": _require_str("raw_output_path", payload.get("raw_output_path")),
    }


def build_params(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "query": config["query"],
        "category": config["category"],
        "format": "json",
        "per_page": config["max_items"],
    }


def unavailable_error() -> dict[str, Any]:
    return error(
        "source_unavailable",
        (
            "HMDB answered with a Cloudflare bot-protection challenge instead of data (checked "
            "2026-09-28 on the search path and the download tree). HMDB publishes no public API; "
            "its API page asks academic and commercial groups to request access by email. "
            f"To use HMDB data legitimately, download {DOWNLOADS_URL}hmdb_metabolites.zip "
            "(MetaboCard XML, about 910 MB) through a browser and query the extracted file locally. "
            + LICENSE_NOTE
        ),
        ["No HMDB data was retrieved, so nothing about the queried compound is established here."],
    )


def execute(payload: Any) -> dict[str, Any]:
    if requests is None:
        return error("missing_dependency", f"`requests` is required: {REQUESTS_IMPORT_ERROR}")
    try:
        config = parse_input(payload)
    except ValueError as exc:
        return error("invalid_input", str(exc))

    url = f"{HMDB_BASE}/{SEARCH_PATH}"
    try:
        response = requests.get(
            url,
            params=build_params(config),
            headers={"Accept": "application/json"},
            timeout=config["timeout_sec"],
        )
    except requests.RequestException as exc:
        return error("network_error", f"Request failed: {exc}")

    if is_challenge(response):
        return unavailable_error()
    if response.status_code != 200:
        return error("http_error", f"HMDB returned HTTP {response.status_code} for {config['query']!r}.")

    raw_output_path = None
    if config["save_raw"]:
        handle, name = tempfile.mkstemp(prefix="hmdb-", suffix=".json")
        os.close(handle)
        path = Path(config["raw_output_path"]) if config["raw_output_path"] else Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(response.text, encoding="utf-8")
        raw_output_path = str(path)

    try:
        data = response.json()
    except ValueError:
        return error(
            "invalid_response",
            "HMDB returned a non-JSON body; the endpoint may be behind an interstitial.",
            [f"body started with: {(response.text or '')[:120]!r}"],
        )

    records = data if isinstance(data, list) else data.get("results") or data.get("metabolites") or []
    if not isinstance(records, list):
        records = []
    return {
        "ok": True,
        "source": "hmdb",
        "query": config["query"],
        "category": config["category"],
        "record_count_returned": len(records[: config["max_items"]]),
        "record_count_available": len(records),
        "truncated": len(records) > config["max_items"],
        "records": records[: config["max_items"]],
        "raw_output_path": raw_output_path,
        "warnings": [LICENSE_NOTE],
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception as exc:  # noqa: BLE001
        sys.stdout.write(json.dumps(error("invalid_json", f"Could not parse JSON input: {exc}")))
        return 2
    output = execute(payload)
    sys.stdout.write(json.dumps(output))
    if output.get("ok"):
        return 0
    return 2 if output.get("error", {}).get("code") == "invalid_input" else 1


if __name__ == "__main__":
    raise SystemExit(main())
