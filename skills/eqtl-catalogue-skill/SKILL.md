---
name: eqtl-catalogue-skill
description: Query the eQTL Catalogue through its current HTTPS access routes, for credible sets, dataset resolution and region-level summary statistics. Use when a user wants public eQTL Catalogue evidence for a variant, gene, tissue or region.
---

## Service state (checked 2026-09-28)

The EBI REST API this skill originally used (`https://www.ebi.ac.uk/eqtl/api`) is retired: every path
returns HTTP 410 with "This API is no longer available". The catalogue itself is still published, and
the project documents the replacement routes on <https://www.ebi.ac.uk/eqtl/Data_access/>. Use
`scripts/eqtl_query.py`, which implements them.

`scripts/rest_request.py` remains in this skill as a generic REST client, but no eQTL Catalogue
endpoint answers on it any more.

## Operating rules

- Use `scripts/eqtl_query.py` for all eQTL Catalogue work.
- Choose the action that matches the question:
  - `credible_set` for a variant, gene or dataset lookup (fast; REST).
  - `datasets` to resolve a study, tissue or quantification method to a `dataset_id`.
  - `region` to read summary statistics for one region out of a dataset file (tabix over HTTPS).
- Never present a transport or policy failure as "no association". Report the error code.
- A credible set is not an association p-value table, and a region row is not evidence of causality;
  keep the distinction explicit in answers.

## Input

One JSON object on stdin. `action` is required.

- `action`: `credible_set`, `datasets`, or `region`
- `credible_set`: `query` (for example `rs2413583`) and optional `field` (default `rsid`; also accepts
  `gene_id`, `gene_name`, `dataset_id`, `molecular_trait_id`), `max_items`
- `datasets`: any combination of `study`, `tissue`, `quant_method`, `sample_group`, `condition`;
  matching is a case-insensitive substring test over the inventory row
- `region`: `dataset` (for example `QTD000021`) or an explicit `url`, plus `region` in the form
  `chr:beg-end` (1-based, inclusive)
- Optional everywhere: `max_items` (default 10), `timeout_sec` (default 120), `save_raw`, `raw_output_path`

Examples:

- `{"action":"credible_set","field":"rsid","query":"rs2413583","max_items":10}`
- `{"action":"datasets","study":"BLUEPRINT","tissue":"monocyte","max_items":5}`
- `{"action":"region","dataset":"QTD000021","region":"20:46120612-46120613","max_items":10}`

## Output

- `credible_set` returns `records`, `record_count_returned`, `record_count_available`, `truncated`.
- `datasets` returns `datasets` with `dataset_id`, study/tissue labels and the HTTPS
  `summary_stats_url` and `tabix_index_url`.
- `region` returns `columns` (read from the file header) and `records` as objects keyed by column name;
  `record_count_available` counts every row the region holds, `record_count_returned` is capped by
  `max_items`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution

Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"action":"credible_set","field":"rsid","query":"rs2413583","max_items":10}' | "$PY" "$SKILL_DIR/scripts/eqtl_query.py"
```

## Access limits

- EBI asks that tabix-style range requests stay infrequent and warns that bursts are treated like
  denial-of-service traffic and can get a client IP blacklisted. One `region` call issues a cached
  index request plus one ranged data request, plus one small header request on first use.
- For many regions, download the summary-statistics file once instead of issuing many range requests.
- The `region` action reads single-tissue files by default (`<dataset>.all.tsv.gz`). Conditionally
  independent files (`<dataset>.cc.tsv.gz`) exist for some datasets; pass an explicit `url` to read
  those. Permuted files carry no tabix index.

## References

- `references/access-routes.md` records the verified endpoints, identifiers and limits behind this
  skill, with the date each was checked.
