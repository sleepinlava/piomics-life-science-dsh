---
name: ncbi-blast-skill
description: Submit, poll, and summarize NCBI BLAST Common URL API jobs (Blast.cgi) for nucleotide or protein sequences. Use when a user wants RID status, BLAST results, or compact top-hit summaries; fetch raw Text/JSON2 only on request.
---

## Operating rules

- Use `scripts/ncbi_blast.py` for all concrete BLAST work.
- Honor NCBI limits: `>=10s` between requests and `>=60s` between polls for the same RID.
- Always surface the `RID` in the response so the job can be resumed or refetched later.
- If the conversation is long or multiple tool calls have occurred, refetch from the `RID` instead of trusting older context.
- If a prior turn saved raw output to disk, do not read it back into context unless the user asks for a specific follow-up.

## Execution behavior

- Return compact BLAST summaries first.
- Do not paste full `JSON2` or long Text alignments into the response by default.
- Default to `max_hits=5` and `max_queries=5`.
- If the user asks for raw output, write it to a file and report the path.
- Only provide Python code when the user explicitly asks for code or execution is unavailable.
- For normal user-facing answers, summarize the script JSON in markdown; if the user explicitly asks for machine-readable output, return the JSON verbatim.

## Input

- The script reads one JSON object from stdin.
- `action` must be one of `submit`, `status`, `fetch`, or `run`.
- `submit` and `run` require `program`, `database`, `query_fasta`, and `email` (or `NCBI_EMAIL`).
- `status` and `fetch` require `rid`.
- `program` must be one of `blastn`, `blastp`, `blastx`, `tblastn`, or `tblastx`.
- `result_format` defaults to `json2` for `run` and `fetch`.
- `tool` defaults to `NCBI_TOOL`, then `ncbi-blast-skill`.
- `max_hits` defaults to `5`; `max_queries` defaults to `5`.
- `hitlist_size` defaults to `50`; `descriptions` and `alignments` default to `5`.
- `wait_timeout_sec` defaults to `900`.
- `save_raw` defaults to `false`.
- If `save_raw=true` and `raw_output_path` is omitted, the script writes a unique `ncbi-blast-<rid>-*.<json|txt>` file under the system temporary directory and reports it in `raw_output_path`.
- `query_fasta` may contain multi-FASTA input; compact summaries still cap per-query output with `max_hits` and `max_queries`.

## Output

- Common success fields: `ok`, `source`, `action`, `warnings`.
- `submit` returns `rid`, `rtoe_seconds`, and `status="SUBMITTED"`.
- `status` returns `rid`, normalized `status`, and `has_hits`.
- `run` and `fetch` with `result_format=json2` return `rid`, `status`, `has_hits`, `result_format`, `query_count_returned`, `query_count_available`, `query_summaries_truncated`, `query_summaries`, and `raw_output_path`.
- Each `query_summary` contains `query_title`, `hit_count_returned`, `hit_count_available`, `truncated`, and `top_hits`.
- Each `top_hit` contains `rank`, `accession`, `title`, `evalue`, and `bit_score`.
- `fetch` with `result_format=text` returns `text_head` capped at 800 characters unless `save_raw=true`; when `save_raw=true`, it returns only the artifact path.
- Failures return `ok=false`, `error.code`, `error.message`, and `warnings`.

## Execution

- Run `scripts/ncbi_blast.py` with the package interpreter (execution block below).
- `requests` is a required dependency. Install it into the package environment with `pip install -r requirements.txt`; the script reports `missing_dependency` instead of installing anything itself.

Resolve `SKILL_DIR` to this skill's directory (the directory containing this `SKILL.md`) and `PY` to the package interpreter before running the command below; never assume the current working directory is the skill directory.

```bash
PY="${PIOMICS_LS_PYTHON:-python3}"
SKILL_DIR="<absolute path of this skill directory>"
echo '{"action":"run","program":"blastp","database":"swissprot","query_fasta":">q1\nMTEYK...","email":"you@example.com"}' | "$PY" "$SKILL_DIR/scripts/ncbi_blast.py"
```

## References

- Load `references/blast-common-url-api.txt` only for parameter details or uncommon BLAST options.
- Do not load `references/intent-notes.txt` during normal skill execution; it is not runtime guidance.
