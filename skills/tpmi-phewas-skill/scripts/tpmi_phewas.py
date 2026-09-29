#!/usr/bin/env python3
"""tpmi-phewas

Fetch TPMI PheWAS associations for one variant input.
Input JSON on stdin:
  - {"grch38":"6:160540105-T-C"}
  - {"grch37":"6:162447146:T:C","max_results":25}
  - {"rsid":"rs9273363","max_results":25,"save_raw":true}
  - "6:160540105-T-C"
Output JSON on stdout.
"""

from __future__ import annotations

import json
import re
import ssl
import sys
from pathlib import Path
from typing import Any

import requests
import os
import tempfile
from requests.adapters import HTTPAdapter
from variant_resolution import (
    VariantResolutionError,
    extract_variant_input,
    resolve_query_variant,
)


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


def build_ssl_context() -> ssl.SSLContext:
    """Standard certificate verification without OpenSSL's optional strict profile.

    pheweb.ibms.sinica.edu.tw chains to the TWCA Global Root CA, a legacy but still valid trust
    anchor that carries no Subject Key Identifier extension. Python 3.13+ turns on
    VERIFY_X509_STRICT by default, so chain building stops at that root with
    "Missing Subject Key Identifier" while curl and browsers accept the same chain. Clearing only
    the strict flag keeps CERT_REQUIRED, hostname checking, and validation against the normal
    system trust store; certificate verification is not disabled.

    Remove this once the site serves a chain that satisfies the strict profile.
    """
    context = ssl.create_default_context()
    strict_flag = getattr(ssl, "VERIFY_X509_STRICT", 0)
    if strict_flag:
        context.verify_flags &= ~strict_flag
    return context


class _TrustAdapter(HTTPAdapter):
    """Mount a prepared SSL context; HTTPAdapter has no ssl_context constructor argument."""

    def __init__(self, context: ssl.SSLContext, **kwargs: Any) -> None:
        self._ssl_context = context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args: Any, **kwargs: Any) -> Any:
        kwargs["ssl_context"] = self._ssl_context
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args: Any, **kwargs: Any) -> Any:
        kwargs["ssl_context"] = self._ssl_context
        return super().proxy_manager_for(*args, **kwargs)


def make_session() -> requests.Session:
    session = requests.Session()
    session.mount(TPMI_BASE, _TrustAdapter(build_ssl_context()))
    session.headers["Accept"] = "application/json"
    session.headers["User-Agent"] = USER_AGENT
    return session

TPMI_BASE = "https://pheweb.ibms.sinica.edu.tw"
USER_AGENT = "tpmi-phewas-skill/1.0 (+requests)"
DEFAULT_TIMEOUT_S = 20
DEFAULT_MAX_RESULTS = 10
SAFE_PATH_RE = re.compile(r"[^A-Za-z0-9._-]+")


def error(code: str, message: str, warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {"code": code, "message": message},
        "warnings": warnings or [],
    }


def parse_input(payload: Any) -> tuple[str, str, int, bool, str | None, float]:
    if isinstance(payload, str):
        return "grch38", payload.strip(), DEFAULT_MAX_RESULTS, False, None, DEFAULT_TIMEOUT_S

    if not isinstance(payload, dict):
        raise ValueError("Input must be a JSON string or object.")

    input_type, variant = extract_variant_input(payload, default_build_key="grch38")

    max_results = payload.get("max_results", DEFAULT_MAX_RESULTS)
    if not isinstance(max_results, int) or max_results <= 0:
        raise ValueError("`max_results` must be a positive integer when provided.")

    save_raw = payload.get("save_raw", False)
    if not isinstance(save_raw, bool):
        raise ValueError("`save_raw` must be a boolean when provided.")

    raw_output_path = payload.get("raw_output_path")
    if raw_output_path is not None:
        if not isinstance(raw_output_path, str) or not raw_output_path.strip():
            raise ValueError("`raw_output_path` must be a non-empty string when provided.")
        raw_output_path = raw_output_path.strip()

    timeout_sec = payload.get("timeout_sec", DEFAULT_TIMEOUT_S)
    if not isinstance(timeout_sec, (int, float)) or timeout_sec <= 0:
        raise ValueError("`timeout_sec` must be a positive number when provided.")

    return input_type, variant, max_results, save_raw, raw_output_path, float(timeout_sec)


def fetch_tpmi_variant(
    session: requests.Session,
    variant_str: str,
    timeout_sec: float,
) -> tuple[Any | None, int | None]:
    encoded = requests.utils.quote(variant_str, safe=":-")
    url = f"{TPMI_BASE}/api/variant/{encoded}"

    resp = session.get(url, timeout=timeout_sec)
    if resp.status_code in (403, 404):
        return None, resp.status_code
    resp.raise_for_status()
    return resp.json(), resp.status_code


def extract_associations(data: Any) -> list[Any]:
    if data is None:
        return []
    if isinstance(data, dict) and isinstance(data.get("phenos"), list):
        return data["phenos"]
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        return data["results"]
    if isinstance(data, list):
        return data
    return []


def resolve_raw_output_path(canonical_variant: str, raw_output_path: str | None) -> Path:
    if raw_output_path:
        return Path(raw_output_path).expanduser()

    safe_variant = SAFE_PATH_RE.sub("_", canonical_variant).strip("._") or "variant"
    return _unique_raw_path(None, f"tpmi-phewas-{safe_variant}", "json")


def write_raw_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def main() -> int:
    warnings: list[str] = []

    try:
        payload = json.load(sys.stdin)
    except Exception as exc:  # noqa: BLE001
        sys.stdout.write(json.dumps(error("invalid_json", f"Could not parse JSON input: {exc}")))
        return 2

    try:
        input_type, input_variant, max_results, save_raw, raw_output_path, timeout_sec = (
            parse_input(payload)
        )
    except ValueError as exc:
        sys.stdout.write(json.dumps(error("invalid_input", str(exc))))
        return 2

    try:
        resolution = resolve_query_variant(
            input_type=input_type,
            input_value=input_variant,
            target_build="GRCh38",
        )
        parsed = dict(resolution["query_variant"])
        warnings.extend(resolution["warnings"])
    except VariantResolutionError as exc:
        sys.stdout.write(json.dumps(error(exc.code, exc.message, exc.warnings)))
        return 1
    except requests.RequestException as exc:
        sys.stdout.write(json.dumps(error("network_error", f"Variant resolution failed: {exc}")))
        return 1

    session = make_session()
    try:
        data, status_code = fetch_tpmi_variant(session, parsed["canonical"], timeout_sec)
    except requests.RequestException as exc:
        sys.stdout.write(json.dumps(error("network_error", f"TPMI request failed: {exc}")))
        return 1
    except ValueError as exc:
        sys.stdout.write(json.dumps(error("invalid_response", f"TPMI returned non-JSON: {exc}")))
        return 1

    variant_url = f"{TPMI_BASE}/variant/{parsed['canonical']}"
    saved_raw_output_path: str | None = None
    if save_raw and data is not None:
        raw_path = resolve_raw_output_path(parsed["canonical"], raw_output_path)
        try:
            write_raw_json(raw_path, data)
        except OSError as exc:
            sys.stdout.write(json.dumps(error("write_error", f"Could not write raw output: {exc}")))
            return 1
        saved_raw_output_path = str(raw_path)

    if status_code == 403:
        sys.stdout.write(
            json.dumps(
                error(
                    "blocked_by_edge_rule",
                    "TPMI PheWeb answered HTTP 403 for this client. The site blocks some automated "
                    "clients at its edge, so this is a policy block rather than a missing variant. "
                    "Retry later, or ask tpmi@ibms.sinica.edu.tw about automated access.",
                    warnings,
                )
            )
        )
        return 1

    if status_code == 404 or data is None:
        warnings.append("Variant not found in TPMI PheWAS API (the API returns JSON null for variants absent from the release).")
        output = {
            "ok": True,
            "source": "tpmi",
            "input": resolution["input"],
            "query_variant": parsed,
            "max_results_applied": max_results,
            "association_count": 0,
            "association_count_total": 0,
            "truncated": False,
            "associations": [],
            "variant": None,
            "variant_url": variant_url,
            "raw_output_path": None,
            "warnings": warnings,
        }
        sys.stdout.write(json.dumps(output))
        return 0

    associations = extract_associations(data)
    total = len(associations)
    if total > max_results:
        associations = associations[:max_results]
    truncated = len(associations) < total

    variant_info = None
    if isinstance(data, dict):
        variant_info = {
            "chrom": data.get("chrom"),
            "pos": data.get("pos"),
            "ref": data.get("ref"),
            "alt": data.get("alt"),
            "rsids": data.get("rsids"),
            "variant_name": data.get("variant_name"),
            "nearest_genes": data.get("nearest_genes"),
        }

    output = {
        "ok": True,
        "source": "tpmi",
        "input": resolution["input"],
        "query_variant": parsed,
        "max_results_applied": max_results,
        "association_count": len(associations),
        "association_count_total": total,
        "truncated": truncated,
        "associations": associations,
        "variant": variant_info,
        "variant_url": variant_url,
        "raw_output_path": saved_raw_output_path,
        "warnings": warnings,
    }
    sys.stdout.write(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
