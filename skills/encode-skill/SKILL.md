---
name: encode-skill
description: Submit compact ENCODE REST API requests for object lookups, portal-style search, and metadata retrieval. Use when a user wants concise ENCODE summaries
---

## Operating rules
- Use `scripts/rest_request.py` for all ENCODE API calls.
- Use `base_url=https://www.encodeproject.org`.
- Object lookups usually do not need `max_items`; portal-style search endpoints are better with `limit=10` and `max_items=10`.
- Send `Accept: application/json` in `headers` and add `format=json` in `params` when needed.
- Keep request volume modest and avoid large unfiltered searches.
- Re-run the query when fresh data is needed instead of reusing earlier results.
- Compacted output is controlled by `max_items` and `max_depth`; set `save_raw=true` when the full payload is required.

## Execution behavior
- Return concise markdown summaries from the script JSON by default.
- Prefer accession paths such as `biosamples/<accession>/` and search paths such as `search/`.
- If the user needs the full payload, set `save_raw=true` and report the saved file path.

## Input
- Read one JSON object from stdin.
- Required fields: `base_url`, `path`
- Optional fields: `method`, `params`, `headers`, `json_body`, `form_body`, `record_path`, `response_format`, `max_items`, `max_depth`, `timeout_sec`, `save_raw`, `raw_output_path`
- Common ENCODE patterns:
  - `{"base_url":"https://www.encodeproject.org","path":"biosamples/ENCBS000AAA/","params":{"frame":"object","format":"json"},"headers":{"Accept":"application/json"}}`
  - `{"base_url":"https://www.encodeproject.org","path":"search/","params":{"type":"Experiment","assay_term_name":"RNA-seq","limit":10,"format":"json"},"record_path":"@graph","headers":{"Accept":"application/json"},"max_items":10}`

## Output
- Success returns `ok`, `source`, `path`, `method`, `status_code`, `warnings`, and either compact `records` or a compact `summary`.
- Use `raw_output_path` when `save_raw=true`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"base_url":"https://www.encodeproject.org","path":"search/","params":{"type":"Experiment","assay_term_name":"RNA-seq","limit":10,"format":"json"},"record_path":"@graph","headers":{"Accept":"application/json"},"max_items":10}' | "$PY" "$SKILL_DIR/scripts/rest_request.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/rest_request.py`.
