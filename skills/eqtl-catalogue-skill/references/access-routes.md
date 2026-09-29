# eQTL Catalogue access routes (verified 2026-09-28)

Everything below was checked live on 2026-09-28 against the published services.

## 1. What is retired

| Route | Status |
|---|---|
| `https://www.ebi.ac.uk/eqtl/api/...` (all paths, including `/v3/studies`, `/v3/associations`, `/v1/genes/<id>/associations`) | HTTP 410 `This API is no longer available` |
| `https://www.ebi.ac.uk/eqtl/api/docs` | HTTP 410 |
| `https://www.ebi.ac.uk/eqtl/Data_access/` (documentation, not an API) | HTTP 200; states the REST API "has now been deprecated and is no longer available" |

## 2. Routes the client uses instead

### 2.1 Dataset inventory (replaces the old studies/datasets endpoints)

| Item | Value |
|---|---|
| URL | `https://raw.githubusercontent.com/eQTL-Catalogue/eQTL-Catalogue-resources/master/tabix/tabix_ftp_paths.tsv` |
| Verified | HTTP 200, 287387 bytes, 758 dataset rows |
| Columns | `study_id`, `dataset_id`, `study_label`, `sample_group`, `tissue_id`, `tissue_label`, `condition_label`, `sample_size`, `quant_method`, and the published file path |

Related table: `data_tables/dataset_metadata_r7.tsv` (75969 bytes) adds `pmid` and `study_type`.

### 2.2 Summary-statistics files and tabix index (replaces association queries)

| Item | Value |
|---|---|
| Layout | `https://ftp.ebi.ac.uk/pub/databases/spot/eQTL/sumstats/<QTS study>/<QTD dataset>/<QTD dataset>.<suffix>.tsv.gz` |
| Example file | `.../QTS000002/QTD000021/QTD000021.all.tsv.gz` — HTTP 200, 2991536954 bytes, `Accept-Ranges: bytes` |
| Example index | `.../QTD000021.all.tsv.gz.tbi` — HTTP 200, 1935109 bytes, itself BGZF-compressed (4904293 bytes decompressed) |
| Directory listing | `https://ftp.ebi.ac.uk/pub/databases/spot/eQTL/sumstats/` (Apache autoindex, 9144 bytes, 42 study directories) |
| Suffixes | `.all.tsv.gz` (single tissue) and `.cc.tsv.gz` (conditionally independent) carry `.tbi`; `.permuted.tsv.gz` has no index (HTTP 404) |

Region reads work over plain HTTPS with HTTP range requests; no `tabix` binary and no `pysam` are
required. Verified example: `QTD000021` region `20:46120612-46120613` returns 27 rows for
`rs4239702` across several genes, with column names read from the file header.

Verified header columns for `QTD000021.all.tsv.gz`:
`molecular_trait_id`, `chromosome`, `position`, `ref`, `alt`, `variant`, `ma_samples`, `maf`, and
further columns including `gene_id`, `pvalue` and `rsid`.

### 2.3 ELIXIR-Estonia credible-set API (replaces credible-set queries)

| Item | Value |
|---|---|
| URL | `https://elixir.ut.ee/eqtl/api/subset?q=<value>&field=<field>` |
| Verified | HTTP 200, 7583 bytes for `q=rs2413583&field=rsid` |
| Payload | `{"n": 16, "q": "...", "field": "...", "page": [ ... ]}` |
| Row fields | `dataset_id`, `molecular_trait_id`, `gene_name`, `gene_id`, `credible_set`, `variant`, `rsid`, `quantification_method`, credible-set statistics |
| Other endpoint | `/page?limit=&offset=` paginates the whole credible-set table (911 bytes for `limit=2`) |

The EBI data-access page links this browser, so it is a sanctioned route rather than a workaround.

## 3. Usage limits and risks

- EBI warns that frequent tabix requests look like denial-of-service traffic to its firewall and can
  lead to an IP being blacklisted; it recommends at most one request every couple of seconds, or
  downloading the full files when many regions are needed.
- `region` issues one index request (cached per process), one small header request on first use, and
  one ranged data request per query.
- Identifiers are dataset identifiers (`QTD...`) and study identifiers (`QTS...`); the inventory table
  is the authoritative mapping from labels to identifiers.
