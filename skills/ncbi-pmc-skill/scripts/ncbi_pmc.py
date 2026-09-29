#!/usr/bin/env python3
"""Compact NCBI PMC full-text helper (BioC API).

NCBI retired the PMC Open Access Web Service (oa.fcgi) on 2026-02-12; it now answers HTTP 404.
The documented replacement used here is the PMC BioC API, which serves full text for the Open
Access Subset and the Author Manuscript Collection:

    https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_{json|xml}/{PMCID|PMID}/{encoding}

The API reports "no result" as HTTP 200 with an HTML body, so success is decided by the response
content type and body, never by the status code alone.
"""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET
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

BIOC_BASE = "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi"
VALID_FORMATS = {"json", "xml"}
VALID_ENCODINGS = {"unicode", "ascii"}
DEFAULT_MAX_TEXT_CHARS = 20000
NO_RESULT_MARKER = "[Error]"
JSON_CONTENT_TYPES = ("application/json", "text/json")
XML_CONTENT_TYPES = ("text/xml", "application/xml")


def _unique_raw_path(raw_output_path: str | None, prefix: str, suffix: str) -> Path:
    """Return the caller's path, or a unique file under the system temporary directory.

    A fixed default name made repeated or concurrent runs overwrite each other and ignored the
    caller's working directory. The generated path is reported back in ``raw_output_path``.
    """
    if raw_output_path:
        return Path(raw_output_path)
    handle, name = tempfile.mkstemp(prefix=f"{prefix}-", suffix=f".{suffix}")
    os.close(handle)
    return Path(name)


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


def _require_bool(name: str, value: Any, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(f"`{name}` must be a boolean.")
    return value


def _compact(value: Any, max_items: int, max_depth: int) -> Any:
    if isinstance(value, str):
        return value if len(value) <= 240 else value[:240] + "..."
    if max_depth <= 0:
        if isinstance(value, (dict, list)):
            return "..."
        return value
    if isinstance(value, list):
        out = [_compact(item, max_items, max_depth - 1) for item in value[:max_items]]
        if len(value) > max_items:
            out.append(f"... (+{len(value) - max_items} more)")
        return out
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        items = list(value.items())
        for key, item in items[:max_items]:
            out[str(key)] = _compact(item, max_items, max_depth - 1)
        if len(items) > max_items:
            out["_truncated_keys"] = len(items) - max_items
        return out
    return value


def _localname(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _collect_infons(element: ET.Element) -> dict[str, Any]:
    infons: dict[str, Any] = {}
    for child in element:
        if _localname(child.tag) == "infon":
            key = child.get("key")
            if key:
                infons[key] = (child.text or "").strip()
    return infons


def _passages_from_json(document: dict[str, Any]) -> list[dict[str, Any]]:
    passages = document.get("passages")
    if not isinstance(passages, list):
        return []
    out: list[dict[str, Any]] = []
    for passage in passages:
        if not isinstance(passage, dict):
            continue
        infons = passage.get("infons") if isinstance(passage.get("infons"), dict) else {}
        out.append(
            {
                "text": passage.get("text") if isinstance(passage.get("text"), str) else "",
                "type": infons.get("type", ""),
                "section_type": infons.get("section_type", ""),
                "offset": passage.get("offset"),
                # Keep the full infon map: the front-matter passage carries the article ids,
                # journal, year and author names.
                "infons": infons,
            }
        )
    return out


def _passages_from_xml(document: ET.Element) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for passage in document:
        if _localname(passage.tag) != "passage":
            continue
        infons = _collect_infons(passage)
        text = ""
        for child in passage:
            if _localname(child.tag) == "text":
                text = "".join(child.itertext()).strip()
                break
        out.append(
            {
                "text": text,
                "type": infons.get("type", ""),
                "section_type": infons.get("section_type", ""),
                "offset": None,
                "infons": infons,
            }
        )
    return out


def _normalize_json(text: str) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    payload = json.loads(text)
    collections = payload if isinstance(payload, list) else [payload]
    collection = collections[0] if collections else {}
    if not isinstance(collection, dict):
        raise ValueError("BioC JSON payload was not a collection object.")
    documents = collection.get("documents")
    documents = documents if isinstance(documents, list) else []
    normalized: list[dict[str, Any]] = []
    for document in documents:
        if not isinstance(document, dict):
            continue
        infons = document.get("infons") if isinstance(document.get("infons"), dict) else {}
        normalized.append({"infons": infons, "passages": _passages_from_json(document)})
    collection_infons = collection.get("infons") if isinstance(collection.get("infons"), dict) else {}
    return normalized, collection_infons, documents


def _normalize_xml(text: str) -> tuple[list[dict[str, Any]], dict[str, Any], list[ET.Element]]:
    root = ET.fromstring(text)
    collection_infons = _collect_infons(root)
    documents = [child for child in root if _localname(child.tag) == "document"]
    normalized = [
        {"infons": _collect_infons(document), "passages": _passages_from_xml(document)}
        for document in documents
    ]
    return normalized, collection_infons, documents

def _front_passage(document: dict[str, Any]) -> dict[str, Any] | None:
    """The first passage holds the article front matter (ids, journal, year, authors, title)."""
    for passage in document.get("passages", []):
        infons = passage.get("infons") or {}
        if infons.get("type") == "front" or infons.get("section_type") == "TITLE":
            return passage
    return None


def _author_names(infons: dict[str, Any]) -> list[str]:
    indexed = []
    for key, value in infons.items():
        if key.startswith("name_") and key[5:].isdigit():
            indexed.append((int(key[5:]), str(value)))
    authors = []
    for _, value in sorted(indexed):
        surname = ""
        given = ""
        for part in value.split(";"):
            if part.startswith("surname:"):
                surname = part[len("surname:") :].strip()
            elif part.startswith("given-names:"):
                given = part[len("given-names:") :].strip()
        authors.append(f"{given} {surname}".strip() or value)
    return authors


def _article_metadata(document: dict[str, Any], fallback_id: str) -> dict[str, Any]:
    document_infons = document.get("infons") or {}
    front = _front_passage(document)
    infons = (front or {}).get("infons") or {}
    title = ((front or {}).get("text") or "").strip()
    return {
        "pmcid": infons.get("article-id_pmc") or document.get("id") or fallback_id,
        "pmid": infons.get("article-id_pmid", ""),
        "doi": infons.get("article-id_doi", ""),
        "title": title or infons.get("alt-title", ""),
        "journal": infons.get("journal", "") or infons.get("source", ""),
        "year": infons.get("year", ""),
        "volume": infons.get("volume", ""),
        "issue": infons.get("issue", ""),
        "license": document_infons.get("license", "") or infons.get("license", ""),
        "authors": _author_names(infons),
    }


def parse_input(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Input must be one JSON object.")
    identifier = _require_str("id", payload.get("id"))
    pmid = _require_str("pmid", payload.get("pmid"))
    if not identifier and not pmid:
        raise ValueError("Provide `id` (PMCID, for example PMC3257301) or `pmid`.")
    result_format = (_require_str("format", payload.get("format")) or "json").lower()
    if result_format not in VALID_FORMATS:
        raise ValueError("`format` must be json or xml.")
    encoding = (_require_str("encoding", payload.get("encoding")) or "unicode").lower()
    if encoding not in VALID_ENCODINGS:
        raise ValueError("`encoding` must be unicode or ascii.")
    return {
        "identifier": identifier or pmid,
        "format": result_format,
        "encoding": encoding,
        "include_text": _require_bool("include_text", payload.get("include_text"), True),
        "max_text_chars": _require_int("max_text_chars", payload.get("max_text_chars"), DEFAULT_MAX_TEXT_CHARS),
        "max_items": _require_int("max_items", payload.get("max_items"), 10),
        "max_depth": _require_int("max_depth", payload.get("max_depth"), 3),
        "timeout_sec": _require_int("timeout_sec", payload.get("timeout_sec"), 60),
        "save_raw": _require_bool("save_raw", payload.get("save_raw"), False),
        "raw_output_path": _require_str("raw_output_path", payload.get("raw_output_path")),
    }


def build_url(config: dict[str, Any]) -> str:
    return f"{BIOC_BASE}/BioC_{config['format']}/{config['identifier']}/{config['encoding']}"


def _is_no_result(response: Any) -> bool:
    content_type = (response.headers.get("content-type") or "").lower()
    body = (response.text or "").lstrip()
    if any(content_type.startswith(value) for value in JSON_CONTENT_TYPES):
        return False
    return body.startswith(NO_RESULT_MARKER) or content_type.startswith("text/html")


def execute(payload: Any) -> dict[str, Any]:
    if requests is None:
        return error("missing_dependency", f"`requests` is required: {REQUESTS_IMPORT_ERROR}")
    try:
        config = parse_input(payload)
    except ValueError as exc:
        return error("invalid_input", str(exc))

    url = build_url(config)
    try:
        response = requests.get(
            url,
            headers={"Accept": "application/json" if config["format"] == "json" else "application/xml"},
            timeout=config["timeout_sec"],
        )
    except requests.RequestException as exc:
        return error("network_error", f"Request failed: {exc}")

    raw_output_path = (
        _save_raw_text(response.text, config["raw_output_path"], config["format"])
        if config["save_raw"]
        else None
    )

    if response.status_code == 429:
        return error(
            "rate_limited",
            (
                "PMC BioC API returned HTTP 429. PMC documents a ceiling of 3 requests per second and "
                "asks that scripts making more than 100 requests run outside US Eastern business hours. "
                "Wait before retrying; this client does not retry automatically."
            ),
        )
    if response.status_code == 404:
        return error(
            "not_found",
            f"PMC BioC API returned HTTP 404 for {config['identifier']}; check the identifier format.",
        )
    if response.status_code != 200:
        return error(
            "http_error",
            f"PMC BioC API returned HTTP {response.status_code} for {config['identifier']}.",
        )
    if _is_no_result(response):
        return error(
            "not_in_open_access_subset",
            (
                f"{config['identifier']} has no full text in the PMC Open Access Subset or the Author "
                "Manuscript Collection. This API only serves redistributable full text; the article may "
                "still exist in PMC. Use the NCBI ID Converter for identifier mapping, or fetch metadata "
                "through E-utilities esummary with db=pmc."
            ),
        )

    try:
        if config["format"] == "json":
            documents, collection_infons, raw_documents = _normalize_json(response.text)
        else:
            documents, collection_infons, raw_documents = _normalize_xml(response.text)
    except (json.JSONDecodeError, ET.ParseError, ValueError) as exc:
        return error("invalid_response", f"Could not parse the BioC {config['format']} payload: {exc}")

    if not documents:
        return error(
            "not_in_open_access_subset",
            f"The BioC payload for {config['identifier']} contained no documents.",
        )

    passages = documents[0]["passages"]
    full_text = "\n".join(passage["text"] for passage in passages if passage["text"]).strip()
    text_truncated = len(full_text) > config["max_text_chars"]
    if text_truncated:
        full_text = full_text[: config["max_text_chars"]]

    infons = documents[0]["infons"]
    output: dict[str, Any] = {
        "ok": True,
        "source": "ncbi-pmc-bioc",
        "identifier": config["identifier"],
        "format": config["format"],
        "document_count": len(documents),
        "passage_count": len(passages),
        "article": _article_metadata(documents[0], config["identifier"]),
        "passage_types": sorted({passage["section_type"] or passage["type"] for passage in passages if passage["type"] or passage["section_type"]}),
        "raw_output_path": raw_output_path,
        "warnings": [],
    }
    if config["include_text"]:
        output["text_chars"] = len(full_text)
        output["text_truncated"] = text_truncated
        output["full_text"] = full_text
    output["summary"] = {
        "collection_infons": _compact(collection_infons, config["max_items"], config["max_depth"]),
        "document_infons": _compact(infons, config["max_items"], config["max_depth"]),
        "passages": _compact(passages, config["max_items"], config["max_depth"]),
    }
    return output


def _save_raw_text(raw_text: str, raw_output_path: str | None, suffix: str) -> str:
    path = _unique_raw_path(raw_output_path, "ncbi-pmc", suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(raw_text, encoding="utf-8")
    return str(path)


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
