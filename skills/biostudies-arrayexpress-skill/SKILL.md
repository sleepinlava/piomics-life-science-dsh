---
name: biostudies-arrayexpress-skill
description: Submit compact BioStudies and ArrayExpress API requests for free-text search and accession-based study retrieval. Use when a user wants concise BioStudies summaries
---

## Operating rules
- Use `scripts/rest_request.py` for all BioStudies and ArrayExpress calls.
- Use `base_url=https://www.ebi.ac.uk/biostudies/api/v1`.
- Search pages are better with `pageSize=10` and `max_items=10`; accession lookups usually do not need `max_items`.
- Re-run the query when fresh data is needed instead of reusing earlier results.
- Compacted output is controlled by `max_items` and `max_depth`; set `save_raw=true` when the full payload is required.

## Execution behavior
- Return concise markdown summaries from the script JSON by default.
- Prefer these paths: `search`, `ArrayExpress/search`, `studies/<accession>`, and `studies/<accession>/info`.
- If the user needs the full payload, set `save_raw=true` and report the saved file path instead of printing the payload.

## Input
- Read one JSON object from stdin.
- Required fields: `base_url`, `path`
- Optional fields: `method`, `params`, `headers`, `json_body`, `form_body`, `record_path`, `response_format`, `max_items`, `max_depth`, `timeout_sec`, `save_raw`, `raw_output_path`
- Common BioStudies patterns:
  - `{"base_url":"https://www.ebi.ac.uk/biostudies/api/v1","path":"search","params":{"query":"rna","page":1,"pageSize":10},"record_path":"hits","max_items":10}`
  - `{"base_url":"https://www.ebi.ac.uk/biostudies/api/v1","path":"ArrayExpress/search","params":{"query":"single cell","page":1,"pageSize":10},"record_path":"hits","max_items":10}`
  - `{"base_url":"https://www.ebi.ac.uk/biostudies/api/v1","path":"studies/E-MTAB-6701"}`

## Output
- Success returns `ok`, `source`, `path`, `method`, `status_code`, `warnings`, and either compact `records` or a compact `summary`.
- Use `raw_output_path` when `save_raw=true`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"base_url":"https://www.ebi.ac.uk/biostudies/api/v1","path":"search","params":{"query":"rna","page":1,"pageSize":10},"record_path":"hits","max_items":10}' | "$PY" "$SKILL_DIR/scripts/rest_request.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/rest_request.py`.
