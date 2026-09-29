---
name: clinvar-variation-skill
description: Submit compact ClinVar Clinical Tables and NCBI Variation requests for search, VCV, RCV, SCV, and RefSNP lookups. Use when a user wants variant-level summaries or identifier mapping
---

## Operating rules
- Use `scripts/clinvar_variation.py` for all ClinVar and NCBI Variation work.
- The script accepts `max_items`; for `action=search`, start around `max_items=10`.
- For `refsnp`, omit `max_items` unless you need to trim nested arrays in the summary.
- Re-run the query when fresh data is needed instead of reusing earlier results.
- Compacted output is controlled by `max_items` and `max_depth`; set `save_raw=true` when the full payload is required.
- If the user asks for full JSON, set `save_raw=true` and report the saved file path instead of printing the payload.

## Execution behavior
- Return concise markdown summaries from the script JSON by default.
- Return the JSON verbatim only if the user explicitly asks for machine-readable output.
- Use `action=search` for the Clinical Tables endpoint.
- Use `action=refsnp` for NCBI Variation RefSNP lookups.
- Current service state (checked 2026-09-28): `action=search` and `action=refsnp` work. `action=vcv|rcv|scv` call ClinVar routes on the NCBI Variation service that no longer exist (HTTP 404); ClinVar records are now served through E-utilities `esummary` with `db=clinvar`. Report those actions as unavailable instead of presenting a 404 as a negative finding.

## Input
- Read one JSON object from stdin.
- Required field: `action`
- Action-specific required fields:
  - `search`: `terms`
  - `vcv`: `vcv`
  - `rcv`: `rcv`
  - `scv`: `scv`
  - `refsnp`: `refsnp`
- Optional fields: `params`, `max_items`, `max_depth`, `timeout_sec`, `save_raw`, `raw_output_path`

## Output
- `search` returns `total`, `identifiers`, `display_rows`, `extra_fields`, and truncation metadata.
- `vcv|rcv|scv|refsnp` return a compact `summary` and optional `top_keys`.
- Use `raw_output_path` when `save_raw=true`.
- Failures return `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"action":"search","terms":"VCV000013080","max_items":10}' | "$PY" "$SKILL_DIR/scripts/clinvar_variation.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/clinvar_variation.py`.
