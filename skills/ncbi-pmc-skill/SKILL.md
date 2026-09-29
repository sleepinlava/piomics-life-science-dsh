---
name: ncbi-pmc-skill
description: Fetch PMC full text and article metadata through the PMC BioC API, for articles in the Open Access Subset and the Author Manuscript Collection. Use when a user wants PMC article text or wants to know whether PMC full text is redistributable.
---

## Service state (checked 2026-09-28)

NCBI retired the PMC Open Access Web Service (`oa.fcgi`) on 2026-02-12; it now answers HTTP 404. The
documented replacement is the PMC BioC API:

    https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_{json|xml}/{PMCID|PMID}/{encoding}

It covers the PMC Open Access Subset and the Author Manuscript Collection — not all of PMC — and it
reports "no result" as **HTTP 200 with an HTML body**, so the client decides success from the content
type and body, never from the status code alone.

## Operating rules

- Use `scripts/ncbi_pmc.py` for all PMC full-text work.
- Accepts a `PMCID` (`PMC3257301`) or a `PMID` (`17299597`); the payload echoes the resolved PMCID.
- Treat `error.code=not_in_open_access_subset` as "this API will not serve that article", which is not
  the same as "the article does not exist". Distinguish the two in answers, and offer the NCBI ID
  Converter or an E-utilities metadata lookup instead of claiming the record is missing.
- Report the licence recorded in the article's infons when the user plans to reuse text; licence terms
  vary per article and compliance is the user's responsibility.
- Respect the documented limits: at most 3 requests per second, and scripts making more than 100
  requests should run outside US Eastern business hours. The client never retries automatically.

## Input

One JSON object on stdin:

- `id` (PMCID) or `pmid` — at least one is required
- `format` (optional, default `json`): `json` or `xml`
- `encoding` (optional, default `unicode`): `unicode` or `ascii`
- `include_text` (optional, default `true`): include the reconstructed full text
- `max_text_chars` (optional, default 20000): cap on the returned text
- `max_items`, `max_depth` (optional): compaction of the `summary` block
- `timeout_sec` (optional, default 60), `save_raw`, `raw_output_path`

Examples:

- `{"id":"PMC3257301","max_text_chars":4000}`
- `{"pmid":"17299597","format":"xml","include_text":false,"max_items":5}`

## Output

- Success returns `ok`, `source`, `identifier`, `document_count`, `passage_count`, `article`
  (`pmcid`, `pmid`, `title`, `journal`, `year`, `license`, `authors`), `passage_types`, `summary`, and
  when `include_text=true` also `full_text`, `text_chars` and `text_truncated`.
- Failures return `ok=false` with `error.code`:
  - `not_in_open_access_subset` — HTTP 200 with an HTML error body
  - `rate_limited` — HTTP 429
  - `not_found` — HTTP 404, usually a malformed identifier
  - `invalid_input`, `invalid_response`, `network_error`

## Execution

Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"id":"PMC3257301","max_text_chars":4000}' | "$PY" "$SKILL_DIR/scripts/ncbi_pmc.py"
```

## References

- `references/access-routes.md` records the verified endpoints, the failure modes and the usage limits
  behind this skill, with the date each was checked.
