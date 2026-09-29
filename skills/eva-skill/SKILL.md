---
name: eva-skill
description: Submit compact EVA REST requests for species metadata and archived variant lookups. Use when a user wants concise European Variation Archive summaries
---

## Operating rules
- Use `scripts/rest_request.py` for all EVA calls.
- Use `base_url=https://www.ebi.ac.uk/eva/webservices/rest/v1`.
- Prefer metadata and targeted variant lookups over broad genomic window pulls.
- Keep region queries narrow by species, assembly, or small coordinate windows when possible.
- Re-run the query when fresh data is needed instead of reusing earlier results.

## Execution behavior
- Return concise markdown summaries from the script JSON by default.
- Return raw JSON only if the user explicitly asks for machine-readable output.
- Prefer these paths: `meta/species/list` and targeted variant or region routes from the EVA REST API.

## Input
- Read one JSON object from stdin.
- Required fields: `base_url`, `path`
- Optional fields: `method`, `params`, `headers`, `json_body`, `form_body`, `record_path`, `response_format`, `max_items`, `max_depth`, `timeout_sec`, `save_raw`, `raw_output_path`
- Common EVA patterns:
  - `{"base_url":"https://www.ebi.ac.uk/eva/webservices/rest/v1","path":"meta/species/list","record_path":"response.0.result","max_items":10}`
  - `{"base_url":"https://www.ebi.ac.uk/eva/webservices/rest/v1","path":"variants/rs699","max_items":10}`

## Output
- Success returns `ok`, `source`, `path`, `method`, `status_code`, `warnings`, and either compact `records` or a compact `summary`.
- Use `raw_output_path` when `save_raw=true`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"base_url":"https://www.ebi.ac.uk/eva/webservices/rest/v1","path":"meta/species/list","record_path":"response.0.result","max_items":10}' | "$PY" "$SKILL_DIR/scripts/rest_request.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/rest_request.py`.
