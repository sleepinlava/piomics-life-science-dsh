---
name: ipd-skill
description: Submit compact IPD REST requests for HLA allele and cell-level metadata using the public IPD query API. Use when a user wants concise IPD summaries; save raw JSON or text only on request.
---

## Operating rules
- Use `scripts/rest_request.py` for all IPD calls.
- Use `base_url=https://www.ebi.ac.uk/cgi-bin/ipd/api`.
- The most stable public routes are `allele` and `cell`.
- For HLA allele browsing, pass `project=HLA` and keep `limit` modest.
- Re-run the query when fresh data is needed instead of reusing earlier results.

## Execution behavior
- Return concise markdown summaries from the script JSON by default.
- Return raw JSON or text only if the user explicitly asks for machine-readable output.
- Prefer these paths: `allele`, `cell`, and `allele/download`.

## Input
- Read one JSON object from stdin.
- Required fields: `base_url`, `path`
- Optional fields: `method`, `params`, `headers`, `json_body`, `form_body`, `record_path`, `response_format`, `max_items`, `max_depth`, `timeout_sec`, `save_raw`, `raw_output_path`
- Common IPD patterns:
  - `{"base_url":"https://www.ebi.ac.uk/cgi-bin/ipd/api","path":"allele","params":{"project":"HLA","limit":10},"record_path":"data","max_items":10}`
  - `{"base_url":"https://www.ebi.ac.uk/cgi-bin/ipd/api","path":"allele","params":{"project":"HLA","query":"contains(name,\"A*01\")","limit":10},"record_path":"data","max_items":10}`
  - `{"base_url":"https://www.ebi.ac.uk/cgi-bin/ipd/api","path":"cell","params":{"limit":10},"record_path":"data","max_items":10}`

## Output
- Success returns `ok`, `source`, `path`, `method`, `status_code`, `warnings`, and either compact `records`, a compact `summary`, or `text_head`.
- Use `raw_output_path` when `save_raw=true`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"base_url":"https://www.ebi.ac.uk/cgi-bin/ipd/api","path":"allele","params":{"project":"HLA","limit":10},"record_path":"data","max_items":10}' | "$PY" "$SKILL_DIR/scripts/rest_request.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/rest_request.py`.
