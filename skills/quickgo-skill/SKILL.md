---
name: quickgo-skill
description: Submit compact QuickGO requests for GO terms, annotations, and ontology traversal. Use when a user wants concise QuickGO summaries
---

## Operating rules
- Use `scripts/rest_request.py` for all QuickGO API calls.
- Use `base_url=https://www.ebi.ac.uk/QuickGO/services`.
- GO term lookups usually do not need `max_items`; annotation and traversal endpoints are better with `limit=10` and `max_items=10`.
- Send `Accept: application/json` in `headers`.
- Re-run the query when fresh data is needed instead of reusing earlier results.
- Compacted output is controlled by `max_items` and `max_depth`; set `save_raw=true` when the full payload is required.

## Execution behavior
- Return concise markdown summaries from the script JSON by default.
- Prefer these paths: `ontology/go/terms/<id>`, `annotation/search`, and ontology child or ancestor endpoints.
- Treat `annotation/search` as upstream-fragile when QuickGO's annotation Solr backend is unavailable; fall back to ontology term lookup or UniProt GO annotations when appropriate.
- If the user needs the full payload, set `save_raw=true` and report the saved file path.

## Input
- Read one JSON object from stdin.
- Required fields: `base_url`, `path`
- Optional fields: `method`, `params`, `headers`, `json_body`, `form_body`, `record_path`, `response_format`, `max_items`, `max_depth`, `timeout_sec`, `save_raw`, `raw_output_path`
- Common QuickGO patterns:
  - `{"base_url":"https://www.ebi.ac.uk/QuickGO/services","path":"ontology/go/terms/GO:0008150,GO:0003674","headers":{"Accept":"application/json"},"record_path":"results","max_items":10}`
  - `{"base_url":"https://www.ebi.ac.uk/QuickGO/services","path":"annotation/search","params":{"geneProductId":"P04637","limit":10},"headers":{"Accept":"application/json"},"record_path":"results","max_items":10}`

## Output
- Success returns `ok`, `source`, `path`, `method`, `status_code`, `warnings`, and either compact `records` or a compact `summary`.
- Use `raw_output_path` when `save_raw=true`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"base_url":"https://www.ebi.ac.uk/QuickGO/services","path":"ontology/go/terms/GO:0006915","headers":{"Accept":"application/json"},"record_path":"results","max_items":10}' | "$PY" "$SKILL_DIR/scripts/rest_request.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/rest_request.py`.
