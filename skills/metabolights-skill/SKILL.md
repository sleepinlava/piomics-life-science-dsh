---
name: metabolights-skill
description: Submit compact MetaboLights requests for study discovery and study-level metabolomics metadata. Use when a user wants concise MetaboLights summaries
---

## Operating rules
- Use `scripts/rest_request.py` for all MetaboLights calls.
- Use `base_url=https://www.ebi.ac.uk/metabolights/ws`.
- Start with `studies` for archive browsing and `studies/<MTBLS accession>` for targeted records.
- Keep study discovery narrow and paged rather than pulling very large pages.
- Re-run the query when fresh data is needed instead of reusing earlier results.

## Execution behavior
- Return concise markdown summaries from the script JSON by default.
- Return raw JSON only if the user explicitly asks for machine-readable output.
- Prefer these paths: `studies` and `studies/<MTBLS accession>`.

## Input
- Read one JSON object from stdin.
- Required fields: `base_url`, `path`
- Optional fields: `method`, `params`, `headers`, `json_body`, `form_body`, `record_path`, `response_format`, `max_items`, `max_depth`, `timeout_sec`, `save_raw`, `raw_output_path`
- Common MetaboLights patterns:
  - `{"base_url":"https://www.ebi.ac.uk/metabolights/ws","path":"studies","record_path":"content","max_items":10}`
  - `{"base_url":"https://www.ebi.ac.uk/metabolights/ws","path":"studies/MTBLS1"}`

## Output
- Success returns `ok`, `source`, `path`, `method`, `status_code`, `warnings`, and either compact `records` or a compact `summary`.
- Use `raw_output_path` when `save_raw=true`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"base_url":"https://www.ebi.ac.uk/metabolights/ws","path":"studies","record_path":"content","max_items":10}' | "$PY" "$SKILL_DIR/scripts/rest_request.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/rest_request.py`.
