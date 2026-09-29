---
name: rhea-skill
description: Submit compact Rhea reaction search requests for biochemical reactions and reaction IDs. Use when a user wants concise Rhea summaries
---

## Operating rules
- Use `scripts/rest_request.py` for all Rhea calls.
- Use `base_url=https://www.rhea-db.org`.
- Start with the `rhea` search endpoint plus `format=json`.
- Keep queries narrow by reaction ID, compound name, EC number, or free-text reaction term.
- Re-run the query when fresh data is needed instead of reusing earlier results.

## Execution behavior
- Return concise markdown summaries from the script JSON by default.
- Return raw JSON only if the user explicitly asks for machine-readable output.
- Prefer these patterns: reaction search by `query`, targeted ID search via `query=RHEA:<id>`, and small result windows.

## Input
- Read one JSON object from stdin.
- Required fields: `base_url`, `path`
- Optional fields: `method`, `params`, `headers`, `json_body`, `form_body`, `record_path`, `response_format`, `max_items`, `max_depth`, `timeout_sec`, `save_raw`, `raw_output_path`
- Common Rhea patterns:
  - `{"base_url":"https://www.rhea-db.org","path":"rhea","params":{"query":"caffeine","format":"json"},"record_path":"results","max_items":10}`
  - `{"base_url":"https://www.rhea-db.org","path":"rhea","params":{"query":"RHEA:47148","format":"json"},"record_path":"results","max_items":5}`

## Output
- Success returns `ok`, `source`, `path`, `method`, `status_code`, `warnings`, and either compact `records` or a compact `summary`.
- Use `raw_output_path` when `save_raw=true`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"base_url":"https://www.rhea-db.org","path":"rhea","params":{"query":"caffeine","format":"json"},"record_path":"results","max_items":10}' | "$PY" "$SKILL_DIR/scripts/rest_request.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/rest_request.py`.
