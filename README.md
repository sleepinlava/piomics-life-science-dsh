# PiOmics life-science skills for DeepSeek Harness

This private Cordis bundle adapts the 50 PiOmics life-science skills to DeepSeek Harness. It uses the built-in `@deepseek-ai/dsh-skill-filesystem` provider and keeps each skill's Python scripts beside its `SKILL.md`. The PiOmics source package is maintained separately.

The upstream material was marked Proprietary. This local adaptation carries the existing maintainer's authorization statement in [NOTICE.md](NOTICE.md); that statement does not grant a new license or authorize public redistribution.

## Run

From this directory, set up Python 3.11+ in an environment outside this package and install the pinned requirements. Then boot a dsh profile with the bundle patch:

```bash
python3 -m venv /path/to/venv
/path/to/venv/bin/python -m pip install -r requirements.txt
export PIOMICS_LS_PYTHON=/path/to/venv/bin/python
export PIOMICS_LS_SKILLS_DIR="$(pwd)/skills"
dsh --profile web --patch "$(pwd)/cordis.patch.yml" --no-open
```

`PIOMICS_LS_SKILLS_DIR` must be an absolute path. Optional plotting in `locus-to-gene-mapper-skill` also needs `requirements-plotting.txt`. The `--patch` overlay is process-local: it inserts one provider with a distinct `providerName` and does not replace the profile's existing skill providers. The model can load `research-router-skill` for broad questions or a named source skill such as `uniprot-skill` for a direct lookup.

## Verify

```bash
dsh --profile web --patch "$(pwd)/cordis.patch.yml" --dump-config
```

The composed tree should include `piomics-life-science-skills`. DeepSeek Harness discovers only one level under a configured root; this bundle's `skills/<name>/SKILL.md` layout follows that rule. Each skill resolves its own script and reference paths from its loaded directory. The scripts retain the source package's output and network behavior. A successful catalog load does not establish that external services are available or that a scientific conclusion is valid.

References: [dsh profile and bundle architecture](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md#profiles-and-bundles), [filesystem skill provider](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.md).
