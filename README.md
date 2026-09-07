# regcap

`regcap` is a lightweight integrator for the domestic regulatory-capacity branch of the Treasury Deposit Component research.

Core question:

> When Treasury supply is not absorbed abroad, what domestic balance-sheet constraints determine whether banks, dealers, MMFs, or the Fed absorb the marginal security, and how does that alter the domestic deposit/reserve footprint?

The project consumes compact outputs and source metadata from sibling projects. It does not duplicate raw-data pipelines from `slrwatch`, `bankcap`, `bidbridge`, or `qrawatch`, and it does not own the foreign/external absorption branch handled by `rowflow`.

## Mechanisms

The package covers five domestic-capacity mechanisms:

- SLR / leverage capacity
- LCR / HQLA demand
- G-SIB surcharge / reporting-date window dressing
- Dealer leverage / repo intermediation constraints
- Duration-loss / AOCI / HTM pressure

Generated local outputs are:

- `output/tables/regulatory_capacity_mechanism_matrix.csv`
- `output/tables/imported_artifact_quality.csv`
- `output/tables/source_evidence_summary.csv`
- `output/reports/source_evidence_summary.md`
- `output/reports/dealer_bridge_integration_memo.md`
- `output/reports/regulatory_capacity_design_report.md`
- `output/manifests/regcap_manifest.json`

Generated data and outputs are project-local and gitignored.

## Install

Use an external virtual environment:

```bash
python3 -m venv /tmp/regcap-env
/tmp/regcap-env/bin/python -m pip install -e ".[dev]"
```

Run tests without writing repo-local caches:

```bash
/tmp/regcap-env/bin/python -B -m pytest
```

## Command Map

```bash
regcap validate-config

regcap validate-sibling-sources --sibling-root "$SIBLING_ROOT"

regcap copy-sibling-outputs --sibling-root "$SIBLING_ROOT" --overwrite

regcap validate-imported-artifacts \
  --output output/tables/imported_artifact_quality.csv

regcap write-mechanism-matrix \
  --output output/tables/regulatory_capacity_mechanism_matrix.csv

regcap write-evidence-summary \
  --output output/tables/source_evidence_summary.csv \
  --report output/reports/source_evidence_summary.md

regcap write-dealer-bridge-memo \
  --output output/reports/dealer_bridge_integration_memo.md

regcap write-design-report \
  --matrix output/tables/regulatory_capacity_mechanism_matrix.csv \
  --evidence-summary output/tables/source_evidence_summary.csv \
  --output output/reports/regulatory_capacity_design_report.md

regcap validate-package --strict
```

Set `SIBLING_ROOT` to the local project family root that contains `slrwatch`, `bankcap`, `bidbridge`, `qrawatch`, and optionally `rowflow`.

## Claim Boundary

This package is a research-navigation layer. Its configured mechanism rankings
are hypotheses, not estimated effects or independent corroboration. Cite the
underlying producer and verify its current evidence before using a generated note.

The BidBridge contract selects four frozen v5 artifacts and checks their SHA-256
hashes before displaying an association. A stale import, missing headline, or
missing diagnostic boundary admits no dealer evidence. Updating this pin requires
reviewing the producer receipt; schema validity alone does not establish freshness.

- Do not claim SLR relief robustly caused Treasury absorption; the current `slrwatch` read is cautionary and mixed.
- Do not turn H.8 bank-group screens into individual-bank evidence.
- Do not treat dealer inventory accumulation as final domestic absorption.
- Do not claim domestic regulation caused the TDC deposit response.
- Do not duplicate raw Call Report, FR Y-9C, or FR Y-15 ingestion in this package.
- Do not write to sibling projects.

## Project Layout

```text
regcap/
  config/       source contracts, mechanisms, and variable registry
  docs/         public design notes and claim boundaries
  src/regcap/   package and CLI
  tests/        fixture-backed tests
  data/         ignored local raw/imported/derived data
  output/       ignored generated reports, tables, and manifests
```

Source projects: [slrwatch](https://github.com/smkwray/slrwatch), [bankcap](https://github.com/smkwray/bankcap), [bidbridge](https://github.com/smkwray/bidbridge), [qrawatch](https://github.com/smkwray/qrawatch), [rowflow](https://github.com/smkwray/rowflow).
