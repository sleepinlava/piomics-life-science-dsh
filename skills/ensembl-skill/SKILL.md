---
name: ensembl-skill
description: Submit compact Ensembl REST API requests for lookup, overlap, cross-reference, and variation endpoints. Use when a user wants concise Ensembl summaries
---

## Operating rules
- Use `scripts/rest_request.py` for all Ensembl API calls.
- Use `base_url=https://rest.ensembl.org`.
- The script accepts `max_items`; object lookups usually do not need it, but `overlap` and `xrefs` are better with `max_items=10`.
- Send JSON-friendly headers such as `Accept: application/json` and `Content-Type: application/json`.
- Re-run the query when fresh data is needed instead of reusing earlier results.
- Compacted output is controlled by `max_items` and `max_depth`; set `save_raw=true` when the full payload is required.

## Execution behavior
- Return concise markdown summaries from the script JSON by default.
- Return the script JSON verbatim only if the user explicitly asks for machine-readable output.
- Prefer these paths: `lookup/id/<id>`, `overlap/region/<species>/<region>`, `xrefs/id/<id>`, and `variation/<species>/<id>`.
- Use `save_raw=true` when the user needs the full payload.

## Input
- Read one JSON object from stdin.
- Required fields: `base_url`, `path`
- Optional fields: `method`, `params`, `headers`, `json_body`, `form_body`, `record_path`, `response_format`, `max_items`, `max_depth`, `timeout_sec`, `save_raw`, `raw_output_path`
- Common Ensembl patterns:
  - `{"base_url":"https://rest.ensembl.org","path":"lookup/id/ENSG00000141510","headers":{"Accept":"application/json","Content-Type":"application/json"}}`
  - `{"base_url":"https://rest.ensembl.org","path":"overlap/region/homo_sapiens/1:1000000-1002000","params":{"feature":"gene"},"headers":{"Accept":"application/json","Content-Type":"application/json"},"max_items":10}`

## Output
- Success returns `ok`, `source`, `path`, `method`, `status_code`, `warnings`, and either compact `records` or a compact `summary`.
- Use `raw_output_path` when `save_raw=true`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"base_url":"https://rest.ensembl.org","path":"lookup/id/ENSG00000141510","headers":{"Accept":"application/json","Content-Type":"application/json"}}' | "$PY" "$SKILL_DIR/scripts/rest_request.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/rest_request.py`.
