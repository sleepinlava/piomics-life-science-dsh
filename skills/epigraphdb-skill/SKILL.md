---
name: epigraphdb-skill
description: Submit compact EpiGraphDB API requests for ontology, literature, MR, gene-drug, and support-path evidence. Use when a user wants concise EpiGraphDB summaries
---

## Operating rules
- Use `scripts/rest_request.py` for all EpiGraphDB API calls.
- Use `base_url=https://api.epigraphdb.org`.
- Start with `max_items=10` for list-style endpoints; use smaller caps for literature-heavy or pairwise endpoints if the response fans out quickly.
- Prefer the connectivity guard endpoints first when endpoint availability matters: `ping`, `builds`, and `meta/api-endpoints`.
- Re-run the query when fresh data is needed instead of reusing earlier results.
- Compacted output is controlled by `max_items` and `max_depth`; set `save_raw=true` when the full payload is required.

## Execution behavior
- Return concise markdown summaries from the script JSON by default.
- Prefer targeted paths such as `ontology/gwas-efo`, `gene/drugs`, `gene/druggability/ppi`, `mr`, and `literature/gwas`.
- If the user needs the full payload, set `save_raw=true` and report the saved file path.

## Input
- Read one JSON object from stdin.
- Required fields: `base_url`, `path`
- Optional fields: `method`, `params`, `headers`, `json_body`, `form_body`, `record_path`, `response_format`, `max_items`, `max_depth`, `timeout_sec`, `save_raw`, `raw_output_path`
- Common EpiGraphDB patterns:
  - `{"base_url":"https://api.epigraphdb.org","path":"ping"}`
  - `{"base_url":"https://api.epigraphdb.org","path":"ontology/gwas-efo","params":{"trait":"asthma","score_threshold":0.8,"fuzzy":true},"max_items":10}`
  - `{"base_url":"https://api.epigraphdb.org","path":"gene/drugs","params":{"gene_name":"IL6R"},"max_items":10}`

## Output
- Success returns `ok`, `source`, `path`, `method`, `status_code`, `warnings`, and either compact `records` or a compact `summary`.
- Use `raw_output_path` when `save_raw=true`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"base_url":"https://api.epigraphdb.org","path":"ontology/gwas-efo","params":{"trait":"asthma","score_threshold":0.8,"fuzzy":true},"max_items":10}' | "$PY" "$SKILL_DIR/scripts/rest_request.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/rest_request.py`.
