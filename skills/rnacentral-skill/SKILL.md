---
name: rnacentral-skill
description: Submit compact RNAcentral API requests for RNA entry browsing, single-entry lookup, and cross-reference retrieval. Use when a user wants concise RNAcentral summaries
---

## Operating rules
- Use `scripts/rest_request.py` for all RNAcentral calls.
- Use `base_url=https://rnacentral.org/api/v1`.
- Keep the trailing slash on collection and record paths to avoid redirects.
- Start with targeted lookups such as `rna/<URS>/<taxid>` because broad `rna/` browsing can be slow or time out.
- Re-run the query when fresh data is needed instead of reusing earlier results.

## Execution behavior
- Return concise markdown summaries from the script JSON by default.
- Return raw JSON only if the user explicitly asks for machine-readable output.
- Prefer these paths: `rna/<URS>/<taxid>`, `rna/<URS>/`, `rna/<URS>/xrefs/`, and targeted `rna/` searches with `q` plus small `page_size`.

## Input
- Read one JSON object from stdin.
- Required fields: `base_url`, `path`
- Optional fields: `method`, `params`, `headers`, `json_body`, `form_body`, `record_path`, `response_format`, `max_items`, `max_depth`, `timeout_sec`, `save_raw`, `raw_output_path`
- Common RNAcentral patterns:
  - `{"base_url":"https://rnacentral.org/api/v1","path":"rna/URS000075C808/9606","max_items":10}`
  - `{"base_url":"https://rnacentral.org/api/v1","path":"rna/","params":{"q":"TP53","page_size":10},"record_path":"results","max_items":10}`
  - `{"base_url":"https://rnacentral.org/api/v1","path":"rna/URS0000000001/"}`
  - `{"base_url":"https://rnacentral.org/api/v1","path":"rna/URS0000000001/xrefs/","record_path":"results","max_items":10}`

## Output
- Success returns `ok`, `source`, `path`, `method`, `status_code`, `warnings`, and either compact `records` or a compact `summary`.
- Use `raw_output_path` when `save_raw=true`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"base_url":"https://rnacentral.org/api/v1","path":"rna/URS000075C808/9606","max_items":10}' | "$PY" "$SKILL_DIR/scripts/rest_request.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/rest_request.py`.
