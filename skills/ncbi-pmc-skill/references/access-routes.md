# PMC access routes (verified 2026-09-28)

## 1. Retired

| Route | Evidence |
|---|---|
| `https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC3257301` | HTTP 404, 1584 bytes, `text/html`, title `NCBI/xpmc12 - WWW Error 404 Diagnostic` |
| `https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi` (no parameters) | HTTP 404, 1528 bytes |
| `https://pmc.ncbi.nlm.nih.gov/tools/oa-web-service/` (its documentation) | HTTP 404 |
| NLM announcement | NLM Tech Bull. 2026 Jan-Feb;(468):e8, posted 2026-02-17: "The PMC OA Web Service API — a utility for locating individual article packages on the FTP Service — will no longer be available". Replacement for file retrieval is the PMC Article Datasets services. |

## 2. Replacement used by the client

| Item | Value |
|---|---|
| Template | `https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_[format]/[ID]/[encoding]` |
| `format` | `json` (BioC_json) or `xml` (BioC_xml) |
| `ID` | PubMed ID (`17299597`) or PMC ID (`PMC3257301`) |
| `encoding` | `unicode` or `ascii` |
| Verified JSON call | `BioC_json/PMC3257301/unicode` → HTTP 200, `application/json`, 89671 bytes |
| Verified XML call | `BioC_xml/PMC3257301/unicode` → HTTP 200, `text/xml`, 90603 bytes, root `<collection>` |
| Verified PMID call | `BioC_json/17299597/unicode` → HTTP 200, 71513 bytes (the documented sample URL) |
| Trailing encoding | Optional in practice; send it explicitly |
| JSON shape | Array with one collection: `bioctype`, `source`, `date`, `documents[]`; each document has `id`, `infons` and `passages[]` (`text`, `infons.section_type`, `offset`) |
| Coverage | PMC Open Access Subset plus the PMC Author Manuscript Collection; the licence is per article, recorded in `documents[0].infons.license` |

## 3. Failure modes

| Case | Observed behaviour |
|---|---|
| Identifier with no redistributable full text | **HTTP 200** with `Content-Type: text/html` and the body `[Error] : No result can be found.` |
| Real PMCID outside the Open Access Subset vs a fabricated PMCID | Byte-identical error body; only a follow-up NCBI ID Converter call (`https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids=...&format=json`) distinguishes them |
| Rate limiting | HTTP 429 after roughly 8-10 undelayed calls in a session |
| Unknown route | HTTP 404 |

The client therefore requires HTTP 200 **and** a JSON/XML content type before parsing.

## 4. Usage terms

- PMC lists the BioC API among the few services approved for automated retrieval of PMC content:
  "The PMC Cloud Service, PMC OAI-PMH Service, E-Utilities and BioC API are the only services that may
  be used for automated retrieval of PMC content."
- Rate limit: 3 requests per second; higher rates receive an error.
- Scripts making more than 100 requests should run outside PMC peak hours (Monday-Friday, 05:00-21:00
  US Eastern).
- Not every PMC article is available for text mining and reuse; licence terms are per article.
