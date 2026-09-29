---
name: chembl-skill
description: Submit compact ChEMBL API requests for activity, molecule, target, mechanism, and text-search endpoints. Use when a user wants concise ChEMBL summaries
---

## Operating rules
- Use `scripts/rest_request.py` for all ChEMBL API calls.
- Use `base_url=https://www.ebi.ac.uk/chembl/api/data`.
- The script accepts `max_items`; for activity, mechanism, and text-search collections, start with API `limit=10` and `max_items=10`.
- Single molecule or target lookups usually do not need `max_items`.
- Re-run the query when fresh data is needed instead of reusing earlier results.
- Compacted output is controlled by `max_items` and `max_depth`; set `save_raw=true` when the full payload is required.

## Execution behavior
- Return concise markdown summaries from the script JSON by default.
- Return the script JSON verbatim only if the user explicitly asks for machine-readable output.
- Prefer these paths: `activity.json`, `molecule/<id>.json`, `target/<id>.json`, `mechanism.json`, and `molecule/search.json`.
- Use `record_path` to target list fields like `activities`, `mechanisms`, or `molecules`.

## Input
- Read one JSON object from stdin.
- Required fields: `base_url`, `path`
- Optional fields: `method`, `params`, `headers`, `json_body`, `form_body`, `record_path`, `response_format`, `max_items`, `max_depth`, `timeout_sec`, `save_raw`, `raw_output_path`
- Common ChEMBL patterns:
  - `{"base_url":"https://www.ebi.ac.uk/chembl/api/data","path":"activity.json","params":{"molecule_chembl_id":"CHEMBL25","limit":10},"record_path":"activities","max_items":10}`
  - `{"base_url":"https://www.ebi.ac.uk/chembl/api/data","path":"molecule/CHEMBL25.json"}`
  - `{"base_url":"https://www.ebi.ac.uk/chembl/api/data","path":"molecule/search.json","params":{"q":"imatinib","limit":10},"record_path":"molecules","max_items":10}`

## Output
- Success returns `ok`, `source`, `path`, `method`, `status_code`, `warnings`, and either compact `records` or a compact `summary`.
- Use `raw_output_path` when `save_raw=true`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"base_url":"https://www.ebi.ac.uk/chembl/api/data","path":"activity.json","params":{"molecule_chembl_id":"CHEMBL25","limit":10},"record_path":"activities","max_items":10}' | "$PY" "$SKILL_DIR/scripts/rest_request.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/rest_request.py`.
