---
name: cbioportal-skill
description: Submit compact cBioPortal API requests for studies, molecular profiles, mutations, clinical data, and samples. Use when a user wants concise cBioPortal summaries
---

## Operating rules
- Use `scripts/rest_request.py` for all cBioPortal API calls.
- Use `base_url=https://www.cbioportal.org/api`.
- Collection endpoints are better with `pageSize=10` and `max_items=10`; single study or profile lookups usually do not need `max_items`.
- Use `method=POST` plus `json_body` for fetch-style endpoints such as mutation fetches.
- Send `Accept: application/json` in `headers`.
- Re-run the query when fresh data is needed instead of reusing earlier results.
- Compacted output is controlled by `max_items` and `max_depth`; set `save_raw=true` when the full payload is required.

## Execution behavior
- Return concise markdown summaries from the script JSON by default.
- Prefer these paths: `studies`, `studies/<studyId>/molecular-profiles`, `molecular-profiles/<profileId>/mutations/fetch`, and study-level clinical or sample endpoints.
- If the user needs the full payload, set `save_raw=true` and report the saved file path.

## Input
- Read one JSON object from stdin.
- Required fields: `base_url`, `path`
- Optional fields: `method`, `params`, `headers`, `json_body`, `form_body`, `record_path`, `response_format`, `max_items`, `max_depth`, `timeout_sec`, `save_raw`, `raw_output_path`
- Common cBioPortal patterns:
  - `{"base_url":"https://www.cbioportal.org/api","path":"studies","params":{"keyword":"breast","projection":"SUMMARY","pageSize":10},"headers":{"Accept":"application/json"},"max_items":10}`
  - `{"base_url":"https://www.cbioportal.org/api","path":"molecular-profiles/brca_tcga_mutations/mutations/fetch","method":"POST","json_body":{"sampleListId":"brca_tcga_all","entrezGeneIds":[7157]},"headers":{"Accept":"application/json"},"max_items":10}`

## Output
- Success returns `ok`, `source`, `path`, `method`, `status_code`, `warnings`, and either compact `records` or a compact `summary`.
- Use `raw_output_path` when `save_raw=true`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"base_url":"https://www.cbioportal.org/api","path":"studies","params":{"keyword":"breast","projection":"SUMMARY","pageSize":10},"headers":{"Accept":"application/json"},"max_items":10}' | "$PY" "$SKILL_DIR/scripts/rest_request.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/rest_request.py`.
