---
name: proteomexchange-skill
description: Submit compact ProteomeXchange PROXI requests for datasets, libraries, peptidoforms, proteins, PSMs, spectra, and USI examples. Use when a user wants concise PROXI summaries
---

## Operating rules
- Use `scripts/rest_request.py` for all ProteomeXchange PROXI calls.
- Use `base_url=https://proteomecentral.proteomexchange.org/api/proxi/v0.1`.
- Collection endpoints are better with `max_items=10`; targeted identifier lookups usually do not need `max_items`.
- Keep requests narrow by identifier, spectrum, or dataset whenever possible.
- Re-run the query when fresh data is needed instead of reusing earlier results.
- Compacted output is controlled by `max_items` and `max_depth`; set `save_raw=true` when the full payload is required.

## Execution behavior
- Return concise markdown summaries from the script JSON by default.
- Prefer these paths: `datasets`, `datasets/<identifier>`, `libraries`, `peptidoforms`, `proteins`, `psms`, `spectra`, and `usi_examples`.
- If the user needs the full payload, set `save_raw=true` and report the saved file path.

## Input
- Read one JSON object from stdin.
- Required fields: `base_url`, `path`
- Optional fields: `method`, `params`, `headers`, `json_body`, `form_body`, `record_path`, `response_format`, `max_items`, `max_depth`, `timeout_sec`, `save_raw`, `raw_output_path`
- Common PROXI patterns:
  - `{"base_url":"https://proteomecentral.proteomexchange.org/api/proxi/v0.1","path":"datasets","max_items":10}`
  - `{"base_url":"https://proteomecentral.proteomexchange.org/api/proxi/v0.1","path":"datasets/PXD000001"}`
  - `{"base_url":"https://proteomecentral.proteomexchange.org/api/proxi/v0.1","path":"usi_examples","max_items":10}`

## Output
- Success returns `ok`, `source`, `path`, `method`, `status_code`, `warnings`, and either compact `records` or a compact `summary`.
- Use `raw_output_path` when `save_raw=true`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"base_url":"https://proteomecentral.proteomexchange.org/api/proxi/v0.1","path":"datasets","max_items":10}' | "$PY" "$SKILL_DIR/scripts/rest_request.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/rest_request.py`.
