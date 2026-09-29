# HMDB service state (checked 2026-09-28)

## Result

No HMDB endpoint, page or archive was retrievable by a scripted client. Every request returned the
same Cloudflare managed challenge.

## Endpoints tested

| Target | Result |
|---|---|
| `https://hmdb.ca/` and `/about`, `/downloads`, `/citing`, `/robots.txt` | HTTP 403, `cf-mitigated: challenge` |
| `https://hmdb.ca/simple/api` (the API information page) | HTTP 403 |
| `https://hmdb.ca/unearth/q?query=serotonin&category=metabolites&format=json&per_page=10` | HTTP 403 |
| `https://hmdb.ca/metabolites/HMDB0000123` and `/metabolites/HMDB0000123.xml` | HTTP 403 |
| `https://hmdb.ca/system/downloads/current/hmdb_metabolites.zip` (about 910 MB) | HTTP 403 |
| `https://hmdb.ca/system/downloads/current/structures.zip` (about 92 MB) | HTTP 403 |
| `https://hmdb.ca/system/downloads/4.0/hmdb_metabolites.zip` | HTTP 403 |
| `http://hmdb.ca/...` | HTTP 403 |

Repeated with browser-like request headers and over http as well as https: unchanged. One probe pinned
the hostname to the site's real public edge address (Cloudflare, `172.67.139.101`) to rule out a
sandbox DNS artifact: still HTTP 403 with the same `cf-mitigated: challenge` header.

Response shape for every attempt: `text/html`, 5163-5489 bytes, body starting
`<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title>`, headers
`server: cloudflare`, `cf-mitigated: challenge`, `cf-ray: ...`.

## Documented access terms

- The downloads page states the data is free to use, but that "use and re-distribution of the data, in
  whole or in part, for commercial purposes requires explicit permission of the authors".
- The about page states the data licence: CC Attribution-NonCommercial 4.0 International.
- The API page documents no endpoint, schema or rate limit; it asks academic and research groups to
  contact `eponine@ualberta.ca` or `samackay@ualberta.ca` for API access, and commercial groups to
  contact `samackay@ualberta.ca`.
- The HMDB 5.0 paper (Wishart et al., Nucleic Acids Res 2022, doi 10.1093/nar/gkab1062) describes the
  download operation as browser-based.

## What this means for the skill

`hmdb_lookup.py` keeps the documented search request so it works where the site does not challenge the
client, and otherwise returns `source_unavailable` with the manual route rather than a bare 403. The
legitimate alternative for programmatic use is a local copy of the published archives
(`hmdb_metabolites.zip`, `structures.zip`) queried offline.
