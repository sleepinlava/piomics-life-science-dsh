#!/usr/bin/env python3
"""eQTL Catalogue client (HTTPS downloads, tabix index, ELIXIR-Estonia credible sets).

The EBI REST API that this skill used (https://www.ebi.ac.uk/eqtl/api) was retired: every path now
answers HTTP 410 "This API is no longer available". The catalogue itself is still published, so this
client uses the access routes the project documents on
https://www.ebi.ac.uk/eqtl/Data_access/ instead:

  datasets      resolve study / tissue / quantification method to a QTD dataset identifier using the
                static inventory published in the eQTL-Catalogue-resources repository
  credible_set  query the unauthenticated ELIXIR-Estonia credible-set REST API
  region        read a region straight out of a summary-statistics file over HTTPS, using the tabix
                index and HTTP range requests (no tabix binary and no pysam required)

Actions:
  {"action":"datasets","study":"BLUEPRINT","tissue":"monocyte"}
  {"action":"credible_set","field":"rsid","query":"rs2413583"}
  {"action":"region","dataset":"QTD000021","region":"20:46120612-46120613"}

EBI asks that tabix-style range requests stay infrequent: each region query issues one index
request (cached per process) plus one ranged data request, and heavy use should switch to
downloading the summary-statistics files instead.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import zlib
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError as exc:  # pragma: no cover
    requests = None
    REQUESTS_IMPORT_ERROR = exc
else:
    REQUESTS_IMPORT_ERROR = None

FTP_BASE = "https://ftp.ebi.ac.uk/pub/databases/spot/eQTL"
SUMSTATS_BASE = f"{FTP_BASE}/sumstats"
INVENTORY_URL = (
    "https://raw.githubusercontent.com/eQTL-Catalogue/eQTL-Catalogue-resources/master/"
    "tabix/tabix_ftp_paths.tsv"
)
CREDIBLE_SET_BASE = "https://elixir.ut.ee/eqtl/api"
DEFAULT_TIMEOUT_S = 120
DEFAULT_MAX_RESULTS = 10
BGZF_EOF_MARKER = b"\x1f\x8b\x08\x04"

_index_cache: dict[str, "TabixIndex"] = {}
_inventory_cache: dict[str, list[dict[str, str]]] = {}
_header_cache: dict[str, list[str]] = {}


def _unique_raw_path(raw_output_path: str | None, prefix: str, suffix: str) -> Path:
    """Return the caller's path, or a unique file under the system temporary directory."""
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


# --------------------------------------------------------------------------------------
# BGZF and tabix
# --------------------------------------------------------------------------------------


def bgzf_blocks(data: bytes) -> list[tuple[int, bytes]]:
    """Split a BGZF stream into (block file offset, uncompressed bytes) pairs.

    Trailing bytes that are not a complete block are ignored, which makes a truncated HTTP range
    safe to process.
    """
    blocks: list[tuple[int, bytes]] = []
    position = 0
    while position + 18 <= len(data):
        if data[position : position + 2] != b"\x1f\x8b":
            break
        extra_length = int.from_bytes(data[position + 10 : position + 12], "little")
        extra = data[position + 12 : position + 12 + extra_length]
        block_size = None
        cursor = 0
        while cursor + 4 <= len(extra):
            subfield_id = extra[cursor : cursor + 2]
            subfield_length = int.from_bytes(extra[cursor + 2 : cursor + 4], "little")
            if subfield_id == b"BC" and subfield_length == 2:
                block_size = int.from_bytes(extra[cursor + 4 : cursor + 6], "little") + 1
            cursor += 4 + subfield_length
        if not block_size or position + block_size > len(data):
            break
        try:
            blocks.append((position, zlib.decompress(data[position : position + block_size], 16 + zlib.MAX_WBITS)))
        except zlib.error:
            break
        position += block_size
    return blocks


class TabixIndex:
    """Minimal tabix (.tbi) reader for region lookups."""

    def __init__(self, raw: bytes) -> None:
        if raw[:4] != b"TBI\x01":
            raise ValueError("Not a tabix index (missing TBI magic).")
        offset = 4
        self.n_ref, self.format, self.col_seq, self.col_beg, self.col_end, self.meta, self.skip, l_nm = (
            int.from_bytes(raw[offset + 4 * i : offset + 4 * i + 4], "little", signed=True) for i in range(8)
        )
        offset += 32
        names = raw[offset : offset + l_nm].split(b"\x00")
        self.names = [name.decode("utf-8", "replace") for name in names if name]
        offset += l_nm
        self.bins: list[dict[int, list[tuple[int, int]]]] = []
        self.linear: list[list[int]] = []
        for _ in range(self.n_ref):
            (n_bin,) = (int.from_bytes(raw[offset : offset + 4], "little", signed=True),)
            offset += 4
            bin_map: dict[int, list[tuple[int, int]]] = {}
            for _ in range(n_bin):
                bin_id = int.from_bytes(raw[offset : offset + 4], "little")
                n_chunk = int.from_bytes(raw[offset + 4 : offset + 8], "little", signed=True)
                offset += 8
                chunks = []
                for _ in range(n_chunk):
                    chunk_beg = int.from_bytes(raw[offset : offset + 8], "little")
                    chunk_end = int.from_bytes(raw[offset + 8 : offset + 16], "little")
                    offset += 16
                    chunks.append((chunk_beg, chunk_end))
                bin_map[bin_id] = chunks
            self.bins.append(bin_map)
            (n_intv,) = (int.from_bytes(raw[offset : offset + 4], "little", signed=True),)
            offset += 4
            intervals = []
            for _ in range(n_intv):
                intervals.append(int.from_bytes(raw[offset : offset + 8], "little"))
                offset += 8
            self.linear.append(intervals)

    def ref_id(self, chrom: str) -> int | None:
        for candidate in (chrom, chrom.removeprefix("chr")):
            if candidate in self.names:
                return self.names.index(candidate)
        return None

    def chunks(self, ref_id: int, beg: int, end: int) -> list[tuple[int, int]]:
        collected: list[tuple[int, int]] = []
        bin_map = self.bins[ref_id]
        for bin_id in reg2bins(beg, end):
            collected.extend(bin_map.get(bin_id, []))
        if not collected:
            return []
        collected.sort()
        merged: list[list[int]] = []
        for chunk_beg, chunk_end in collected:
            if merged and chunk_beg <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], chunk_end)
            else:
                merged.append([chunk_beg, chunk_end])
        # The linear index lets us drop chunks that cannot contain the requested start.
        intervals = self.linear[ref_id]
        if intervals:
            index = beg >> 14
            if index < len(intervals):
                minimum = intervals[index]
                merged = [[b, e] for b, e in merged if e > minimum]
                if merged:
                    merged[0][0] = max(merged[0][0], minimum)
        return [(b, e) for b, e in merged]


def reg2bins(beg: int, end: int) -> list[int]:
    """Bins overlapping [beg, end) using the UCSC/tabix binning scheme (0-based, half-open)."""
    end -= 1
    bins = [0]
    bins.extend(range(1 + (beg >> 26), 1 + (end >> 26) + 1))
    bins.extend(range(9 + (beg >> 23), 9 + (end >> 23) + 1))
    bins.extend(range(73 + (beg >> 20), 73 + (end >> 20) + 1))
    bins.extend(range(585 + (beg >> 17), 585 + (end >> 17) + 1))
    bins.extend(range(4681 + (beg >> 14), 4681 + (end >> 14) + 1))
    return bins


def parse_region(region: str) -> tuple[str, int, int]:
    """Parse 'chr:beg-end' (1-based inclusive) into (chrom, beg0, end0) half-open 0-based."""
    if ":" not in region:
        raise ValueError("`region` must look like chr:beg-end, for example 20:46120612-46120613.")
    chrom, _, span = region.partition(":")
    span = span.replace(",", "")
    if "-" in span:
        beg_text, _, end_text = span.partition("-")
    else:
        beg_text = end_text = span
    try:
        beg = int(beg_text)
        end = int(end_text)
    except ValueError as exc:
        raise ValueError(f"Could not parse the region coordinates in {region!r}.") from exc
    if beg < 1 or end < beg:
        raise ValueError("`region` coordinates must be 1-based and end must not precede begin.")
    return chrom.strip(), beg - 1, end


# --------------------------------------------------------------------------------------
# Actions
# --------------------------------------------------------------------------------------


def fetch_inventory(session: requests.Session, timeout: int) -> list[dict[str, str]]:
    if "rows" in _inventory_cache:
        return _inventory_cache["rows"]
    response = session.get(INVENTORY_URL, timeout=timeout)
    response.raise_for_status()
    lines = response.text.splitlines()
    if not lines:
        raise ValueError("The eQTL Catalogue inventory table was empty.")
    header = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        values = line.split("\t")
        rows.append({header[i]: (values[i] if i < len(values) else "") for i in range(len(header))})
    _inventory_cache["rows"] = rows
    return rows


def dataset_paths(row: dict[str, str]) -> list[str]:
    """Build the HTTPS sumstats paths for one inventory row."""
    study = row.get("study_id", "")
    dataset = row.get("dataset_id", "")
    if not study or not dataset:
        return []
    prefix = f"{SUMSTATS_BASE}/{study}/{dataset}/{dataset}"
    return [f"{prefix}.all.tsv.gz", f"{prefix}.cc.tsv.gz"]


def action_datasets(session: requests.Session, config: dict[str, Any]) -> dict[str, Any]:
    rows = fetch_inventory(session, config["timeout_sec"])
    wanted = {
        key: str(config[key]).lower()
        for key in ("study", "tissue", "dataset", "quant_method", "sample_group", "condition")
        if config.get(key)
    }
    matched = []
    for row in rows:
        haystack = {key: (value or "").lower() for key, value in row.items()}
        if all(needle in " ".join(haystack.values()) for needle in wanted.values()):
            matched.append(row)
    limited = matched[: config["max_items"]]
    datasets = []
    for row in limited:
        paths = dataset_paths(row)
        datasets.append(
            {
                "study_id": row.get("study_id"),
                "dataset_id": row.get("dataset_id"),
                "study_label": row.get("study_label"),
                "tissue_label": row.get("tissue_label"),
                "sample_group": row.get("sample_group"),
                "condition_label": row.get("condition_label"),
                "quant_method": row.get("quant_method"),
                "sample_size": row.get("sample_size"),
                "summary_stats_url": paths[0] if paths else "",
                "tabix_index_url": f"{paths[0]}.tbi" if paths else "",
            }
        )
    return {
        "ok": True,
        "source": "eqtl-catalogue-ftp",
        "action": "datasets",
        "filters": wanted,
        "record_count_returned": len(datasets),
        "record_count_available": len(matched),
        "truncated": len(matched) > len(datasets),
        "datasets": datasets,
        "inventory_url": INVENTORY_URL,
        "warnings": [],
    }


def action_credible_set(session: requests.Session, config: dict[str, Any]) -> dict[str, Any]:
    params = {"q": config["query"], "field": config["field"]}
    if config["limit"]:
        params["limit"] = config["limit"]
    response = session.get(f"{CREDIBLE_SET_BASE}/subset", params=params, timeout=config["timeout_sec"])
    response.raise_for_status()
    try:
        data = response.json()
    except ValueError as exc:
        raise ValueError(f"The credible-set endpoint returned non-JSON content: {exc}") from exc
    if isinstance(data, dict):
        # The ELIXIR-Estonia endpoint answers {"n": <total>, "q": ..., "field": ..., "page": [rows]}.
        rows = data.get("page") or data.get("data") or data.get("results") or []
        total = data.get("n")
        if not isinstance(total, int):
            total = data.get("total") or data.get("count") or len(rows)
    elif isinstance(data, list):
        rows = data
        total = len(rows)
    else:
        raise ValueError("Unexpected credible-set payload shape.")
    if not isinstance(rows, list):
        raise ValueError("The credible-set payload did not contain a list of rows.")
    limited = rows[: config["max_items"]]
    return {
        "ok": True,
        "source": "eqtl-catalogue-elixir",
        "action": "credible_set",
        "query": config["query"],
        "field": config["field"],
        "record_count_returned": len(limited),
        "record_count_available": total,
        "truncated": total > len(limited),
        "records": limited,
        "warnings": [],
    }


def load_index(session: requests.Session, url: str, timeout: int) -> TabixIndex:
    if url in _index_cache:
        return _index_cache[url]
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    # The published .tbi files are themselves BGZF-compressed; fall back to the raw bytes so an
    # uncompressed index still parses.
    decompressed = b"".join(payload for _, payload in bgzf_blocks(response.content))
    index = TabixIndex(decompressed or response.content)
    _index_cache[url] = index
    return index


def load_header(session: requests.Session, url: str, timeout: int) -> list[str]:
    """Read the column header from the start of a summary-statistics file.

    The header sits in the first BGZF blocks, far from any indexed region, so it needs its own
    small range request. The result is cached per process.
    """
    if url in _header_cache:
        return _header_cache[url]
    response = session.get(url, headers={"Range": "bytes=0-131071"}, timeout=timeout)
    response.raise_for_status()
    text = b"".join(payload for _, payload in bgzf_blocks(response.content)).decode("utf-8", "replace")
    header: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip("#")
        if stripped and not stripped.startswith("##"):
            header = stripped.split("\t")
            break
    _header_cache[url] = header
    return header


def action_region(session: requests.Session, config: dict[str, Any]) -> dict[str, Any]:
    chrom, beg, end = parse_region(config["region"])
    url = config["url"]
    if not url:
        rows = fetch_inventory(session, config["timeout_sec"])
        match = next((row for row in rows if row.get("dataset_id") == config["dataset"]), None)
        if match is None:
            raise ValueError(
                f"Dataset {config['dataset']!r} is not in the eQTL Catalogue inventory. "
                "Run action=datasets to find a valid dataset_id."
            )
        paths = dataset_paths(match)
        if not paths:
            raise ValueError(f"Dataset {config['dataset']!r} has no summary-statistics path.")
        url = paths[0]

    index = load_index(session, f"{url}.tbi", config["timeout_sec"])
    ref_id = index.ref_id(chrom)
    if ref_id is None:
        return {
            "ok": True,
            "source": "eqtl-catalogue-tabix",
            "action": "region",
            "region": config["region"],
            "dataset": config["dataset"],
            "record_count_returned": 0,
            "record_count_available": 0,
            "truncated": False,
            "records": [],
            "warnings": [f"Chromosome {chrom!r} is not present in this dataset ({len(index.names)} sequences indexed)."],
        }

    chunks = index.chunks(ref_id, beg, end)
    if not chunks:
        return {
            "ok": True,
            "source": "eqtl-catalogue-tabix",
            "action": "region",
            "region": config["region"],
            "dataset": config["dataset"],
            "record_count_returned": 0,
            "record_count_available": 0,
            "truncated": False,
            "records": [],
            "warnings": [],
        }

    start_vo = chunks[0][0]
    end_vo = chunks[-1][1]
    start_offset = start_vo >> 16
    # One extra block covers the case where the requested end sits inside a block.
    end_offset = (end_vo >> 16) + 65536
    response = session.get(
        url, headers={"Range": f"bytes={start_offset}-{end_offset}"}, timeout=config["timeout_sec"]
    )
    response.raise_for_status()

    blocks = bgzf_blocks(response.content)
    if not blocks:
        raise ValueError("The ranged response did not contain a complete BGZF block.")

    # Map virtual offsets to positions in the decompressed stream. Block offsets from the ranged
    # response are relative to the range start, so shift them back to absolute file offsets.
    stream = bytearray()
    block_offsets: list[tuple[int, int, int]] = []  # (file offset, stream start, stream end)
    for relative_offset, payload in blocks:
        block_offsets.append((start_offset + relative_offset, len(stream), len(stream) + len(payload)))
        stream.extend(payload)

    def stream_position(virtual_offset: int) -> int | None:
        file_offset = virtual_offset >> 16
        for candidate_offset, stream_start, stream_end in block_offsets:
            if candidate_offset == file_offset:
                return stream_start + (virtual_offset & 0xFFFF)
        return None

    begin = stream_position(start_vo)
    finish = stream_position(end_vo)
    if begin is None:
        raise ValueError("The tabix index pointed outside the fetched byte range.")
    if finish is None:
        finish = len(stream)

    text = stream[begin:finish].decode("utf-8", "replace")
    records = []
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) < max(index.col_seq, index.col_beg, index.col_end):
            continue
        row_chrom = fields[index.col_seq - 1].removeprefix("chr")
        try:
            row_beg = int(fields[index.col_beg - 1])
        except ValueError:
            continue
        if row_chrom == chrom.removeprefix("chr") and beg <= row_beg - 1 < end:
            records.append(fields)

    columns = load_header(session, url, config["timeout_sec"])
    shaped = []
    for fields in records[: config["max_items"]]:
        if columns and len(columns) == len(fields):
            shaped.append(dict(zip(columns, fields)))
        else:
            shaped.append({"fields": fields})

    return {
        "ok": True,
        "source": "eqtl-catalogue-tabix",
        "action": "region",
        "region": config["region"],
        "dataset": config["dataset"],
        "file_url": url,
        "columns": columns,
        "record_count_returned": len(shaped),
        "record_count_available": len(records),
        "truncated": len(records) > len(shaped),
        "records": shaped,
        "warnings": [],
    }


def parse_input(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Input must be one JSON object.")
    action = _require_str("action", payload.get("action"), required=True)
    if action not in {"datasets", "credible_set", "region"}:
        raise ValueError("`action` must be one of: datasets, credible_set, region.")
    config: dict[str, Any] = {
        "action": action,
        "study": _require_str("study", payload.get("study")),
        "tissue": _require_str("tissue", payload.get("tissue")),
        "quant_method": _require_str("quant_method", payload.get("quant_method")),
        "sample_group": _require_str("sample_group", payload.get("sample_group")),
        "condition": _require_str("condition", payload.get("condition")),
        "dataset": _require_str("dataset", payload.get("dataset")),
        "field": (_require_str("field", payload.get("field")) or "rsid"),
        "query": _require_str("query", payload.get("query")),
        "region": _require_str("region", payload.get("region")),
        "url": _require_str("url", payload.get("url")),
        "limit": _require_int("limit", payload.get("limit"), 0) if payload.get("limit") else 0,
        "max_items": _require_int("max_items", payload.get("max_items"), DEFAULT_MAX_RESULTS),
        "timeout_sec": _require_int("timeout_sec", payload.get("timeout_sec"), DEFAULT_TIMEOUT_S),
        "save_raw": _require_bool("save_raw", payload.get("save_raw"), False),
        "raw_output_path": _require_str("raw_output_path", payload.get("raw_output_path")),
    }
    if action == "region" and not config["region"]:
        raise ValueError("`region` is required for action=region.")
    if action == "region" and not config["dataset"] and not config["url"]:
        raise ValueError("Provide `dataset` (with an optional release) or an explicit `url` for action=region.")
    if action == "credible_set" and not config["query"]:
        raise ValueError("`query` is required for action=credible_set.")
    return config


def execute(payload: Any) -> dict[str, Any]:
    if requests is None:
        return error("missing_dependency", f"`requests` is required: {REQUESTS_IMPORT_ERROR}")
    try:
        config = parse_input(payload)
    except ValueError as exc:
        return error("invalid_input", str(exc))

    with requests.Session() as session:
        try:
            if config["action"] == "datasets":
                output = action_datasets(session, config)
            elif config["action"] == "credible_set":
                output = action_credible_set(session, config)
            else:
                output = action_region(session, config)
        except ValueError as exc:
            return error("invalid_input", str(exc))
        except requests.RequestException as exc:
            return error("network_error", f"Request failed: {exc}")

    if config["save_raw"]:
        path = _unique_raw_path(config["raw_output_path"], "eqtl-catalogue", "json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        output["raw_output_path"] = str(path)
    return output


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
