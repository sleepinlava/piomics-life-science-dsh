---
name: tpmi-phewas-skill
description: Fetch compact TPMI PheWAS summaries for single variants by accepting rsID, GRCh37, or GRCh38 input and resolving to the required GRCh38 query. Use when a user wants concise TPMI association results for one variant
---

## Service state (checked 2026-09-28)

TPMI PheWeb is live at `https://pheweb.ibms.sinica.edu.tw` and returns real association data. Two
client-side details matter:

- The site chains to the TWCA Global Root CA, a legacy trust anchor with no Subject Key Identifier.
  Python 3.13+ rejects it under OpenSSL's optional strict profile while browsers and curl accept it.
  The script clears only that strict flag (`ssl.VERIFY_X509_STRICT`) and keeps `CERT_REQUIRED`,
  hostname checking and normal system trust; certificate verification is never disabled.
- The edge blocks some automated clients with HTTP 403. The script reports that as
  `blocked_by_edge_rule` instead of treating it as a variant with no associations.

A variant absent from the release is answered with JSON `null` and HTTP 200; the script reports it as
an empty result, which is different from a blocked or failed request. TPMI's `robots.txt` disallows
`/api/` for crawlers, so use this for interactive per-variant lookups and ask
tpmi@ibms.sinica.edu.tw before any bulk or automated batch use. Cite TPMI and Chen et al., Nature 2025
(doi 10.1038/s41586-025-08626-7) when publishing results.

## Operating rules
- Use `scripts/tpmi_phewas.py` for all TPMI PheWAS lookups.
- Accept exactly one of `rsid`, `grch37`, `grch38`, or `variant`; resolve to the canonical GRCh38 `chr:pos-ref-alt` query before calling TPMI.
- The script accepts `max_results`; start with `max_results=10` and only increase it if the first slice is insufficient.
- Re-run the query when fresh data is needed instead of reusing earlier results.
- Compacted output is controlled by `max_items` and `max_depth`; set `save_raw=true` when the full payload is required.
- If the user needs the full association payload, set `save_raw=true` and report `raw_output_path` instead of printing the payload.

## Execution behavior
- Return concise markdown summaries from the script JSON by default.
- Return the JSON verbatim only if the user explicitly asks for machine-readable output.
- Surface the canonical queried variant, total association count, and whether the results were truncated.
- Increase `max_results` gradually instead of asking for large association dumps in one call.

## Input
- Read one JSON object from stdin, or a single JSON string containing the variant.
- Required input: exactly one of `rsid`, `grch37`, `grch38`, or `variant`
- Optional fields: `max_results`, `save_raw`, `raw_output_path`, `timeout_sec`
- Common patterns:
  - `{"grch38":"6:160540105-T-C","max_results":10}`
  - `{"grch37":"6:162447146-T-C","max_results":10}`
  - `{"rsid":"rs9273363","max_results":10}`
  - `{"variant":"6:160540105:T:C","max_results":25,"save_raw":true}`

## Output
- Success returns `ok`, `source`, `input`, `query_variant`, `max_results_applied`, `association_count`, `association_count_total`, `truncated`, `associations`, `variant`, `variant_url`, `raw_output_path`, and `warnings`.
- Use `raw_output_path` when `save_raw=true`.
- Failure returns `ok=false` with `error.code` and `error.message`.

## Execution
Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"grch38":"6:160540105-T-C","max_results":10}' | "$PY" "$SKILL_DIR/scripts/tpmi_phewas.py"
```

## References
- No additional runtime references are required; this skill only needs this file and `scripts/tpmi_phewas.py`.
