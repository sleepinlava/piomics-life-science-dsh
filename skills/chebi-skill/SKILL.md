---
name: chebi-skill
description: Submit compact ChEBI 2.0 API requests for chemical search, compound lookup, ontology traversal, and structure metadata. Use when a user wants concise ChEBI summaries
---

## Operating rules
- Use `scripts/rest_request.py` for all ChEBI calls.
- Use `base_url=https://www.ebi.ac.uk`.
- Prefer the documented public routes under `chebi/backend/api/public/`.
- Start with `es_search/` for free-text lookup and use `compound/<CHEBI:id>/` for targeted records.
- Re-run the query when fresh data is needed instead of reusing earlier results.

## Execution behavior
- Return concise markdown summaries from the script JSON by default.
- Return raw JSON only if the user explicitly asks for machine-readable output.
- Prefer these paths: `chebi/backend/api/public/es_search/`, `chebi/backend/api/public/compound/<CHEBI:id>/`, and ontology child or parent routes.

## Input
- Read one JSON object from stdin.
- Required fields: `base_url`, `path`
- Optional fields: `method`, `params`, `headers`, `json_body`, `form_body`, `record_path`, `response_format`, `max_items`, `max_depth`, `timeout_sec`, `save_raw`, `raw_output_path`
- Common ChEBI patterns:
  - `{"base_url":"https://www.ebi.ac.uk","path":"chebi/backend/api/public/es_search/","params":{"query":"caffeine","size":10},"record_path":"results","max_items":10}`
  - `{"base_url":"https://www.ebi.ac.uk","path":"chebi/backend/api/public/compound/CHEBI:27732/"}`
  - `{"base_url":"https://www.ebi.ac.uk","path":"chebi/backend/api/public/ontology/children/CHEBI:27732/"}`

## Output
- Success returns `ok`, `source`, `path`, `method`, `status_code`, `warnings`, and either compact `records` or a compact `summary`.
- Use `raw_output_path` when `save_raw=true`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"base_url":"https://www.ebi.ac.uk","path":"chebi/backend/api/public/es_search/","params":{"query":"caffeine","size":10},"record_path":"results","max_items":10}' | "$PY" "$SKILL_DIR/scripts/rest_request.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/rest_request.py`.
