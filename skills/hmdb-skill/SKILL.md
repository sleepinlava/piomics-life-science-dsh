---
name: hmdb-skill
description: Look up Human Metabolome Database records for metabolites, proteins, diseases and pathways. Use when a user wants HMDB summaries; the public site currently challenges scripted clients, so report that state instead of substituting another database.
---

## Service state (checked 2026-09-28)

HMDB serves a Cloudflare bot-protection challenge to scripted clients. Every path tested returned
HTTP 403 with a `Just a moment...` interstitial: the search endpoint, `/downloads`, `/simple/api`,
per-record pages and XML routes, and the `/system/downloads/` archives, over http and https, and also
when the request was pinned to the site's real public edge address. HMDB publishes **no public API**;
its API page asks academic and commercial groups to request access by email
(<https://hmdb.ca/simple/api>).

Data licence: HMDB is released under CC BY-NC 4.0. Commercial use and redistribution require
permission from the authors.

## Operating rules

- Use `scripts/hmdb_lookup.py` for HMDB lookups.
- If it returns `error.code=source_unavailable`, report that HMDB could not be reached and what the
  user can do instead. **Do not silently substitute another database** for an HMDB question, and do
  not present the failure as "no such compound exists".
- Never disable certificate verification, impersonate a browser, or retry in a loop to get past the
  protection.
- The script still performs the documented search request, so it returns real records on a network
  where HMDB does not challenge the client.

## Input

One JSON object on stdin:

- `query` (required): compound, protein, disease or pathway name, or an HMDB accession
- `category` (optional, default `metabolites`): `metabolites`, `proteins`, `diseases`, `pathways`
- `max_items` (optional, default 10), `timeout_sec` (optional, default 30)
- `save_raw` and `raw_output_path` for the untrimmed response

Examples:

- `{"query":"serotonin","max_items":5}`
- `{"query":"glycolysis","category":"pathways","max_items":5}`

## Output

- Success returns `records`, `record_count_returned`, `record_count_available`, `truncated`, and the
  licence note in `warnings`.
- `source_unavailable` means HMDB challenged the request; the message carries the manual route.
- `network_error`, `http_error` and `invalid_response` keep their usual meaning. A
  `invalid_response` body that starts with a challenge page is reported as such.

## Working with HMDB data locally

Because the site blocks scripted access, the licensed route is a local copy:

1. In a browser, download `https://hmdb.ca/system/downloads/current/hmdb_metabolites.zip`
   (MetaboCard XML, about 910 MB) or `structures.zip` (SDF, about 92 MB).
2. Extract `hmdb_metabolites.xml` and query it locally. The archive is one XML document with one
   element per metabolite; stream it rather than loading it into memory.
3. Keep the CC BY-NC 4.0 terms in mind before redistributing anything derived from it.

## Execution

Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"query":"serotonin","max_items":5}' | "$PY" "$SKILL_DIR/scripts/hmdb_lookup.py"
```

## References

- `scripts/rest_request.py` remains a generic REST client and is unchanged, but the HMDB endpoints no
  longer answer through it.
- `references/service-state.md` records the endpoints tested and the evidence for the state above.
