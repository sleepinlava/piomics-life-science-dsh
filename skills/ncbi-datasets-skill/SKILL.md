---
name: ncbi-datasets-skill
description: Submit compact NCBI Datasets v2 requests for assembly, genome, taxonomy, and related metadata endpoints. Use when a user wants concise NCBI Datasets summaries; save raw JSON or text only on request.
---

## Operating rules
- Use `scripts/ncbi_datasets.py` for all Datasets v2 calls in this package.
- Use explicit REST `path` values relative to `https://api.ncbi.nlm.nih.gov/datasets/v2`.
- Prefer targeted metadata paths instead of broad unfiltered pulls.
- Re-run the query when fresh data is needed instead of reusing earlier results.
- Compacted output is controlled by `max_items` and `max_depth`; set `save_raw=true` when the full payload is required.

## Execution behavior
- Return concise markdown summaries from the script output by default.
- Return raw JSON or text only if the user explicitly asks for machine-readable output.
- Prefer targeted endpoint calls instead of broad unfiltered dumps.
- If the user needs the full raw response, set `save_raw=true` and report the saved file path.

## Input
- Read one JSON object from stdin.
- Required field: `path`
- Optional fields: `params`, `record_path`, `response_format`, `max_items`, `max_depth`, `timeout_sec`, `save_raw`, `raw_output_path`
- Common Datasets patterns:
  - `{"path":"genome/taxon/9606/dataset_report","params":{"page_size":10},"record_path":"reports","max_items":10}`
  - `{"path":"genome/accession/GCF_000001405.40/dataset_report"}`
  - `{"path":"taxonomy/taxon/9606"}`

## Output
- Success returns `ok`, `source`, path metadata, and either compact `records`, a compact `summary`, or `text_head`.
- Use `raw_output_path` when `save_raw=true`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"path":"genome/taxon/9606/dataset_report","params":{"page_size":10},"record_path":"reports","max_items":10}' | "$PY" "$SKILL_DIR/scripts/ncbi_datasets.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/ncbi_datasets.py`.
