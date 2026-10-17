# RegCap

RegCap organizes evidence about domestic balance-sheet capacity and Treasury
absorption. It reads compact outputs from related projects and builds mechanism
summaries, source-quality tables, and research-design notes. It is a navigation
and synthesis tool; it does not estimate an independent effect on the Treasury
Deposit Component (TDC).

## Coverage

The mechanism registry covers the Supplementary Leverage Ratio (SLR), liquidity
coverage and high-quality liquid assets (LCR/HQLA), global systemically important
bank (G-SIB) surcharges, dealer financing, and duration losses. Accounting context
includes accumulated other comprehensive income (AOCI) and held-to-maturity
(HTM) securities.

Sources are [SLR Watch](https://github.com/smkwray/slrwatch),
[BankCap](https://github.com/smkwray/bankcap),
[BidBridge](https://github.com/smkwray/bidbridge), and
[QRA Watch](https://github.com/smkwray/qrawatch), with optional
[ROWFlow](https://github.com/smkwray/rowflow) context.
`config/` defines source contracts and mechanism mappings.

## Install and validate

Python 3.11 or later is required. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -B -m pytest -q
ruff check .
regcap validate-config
```

## Build summaries

Point `SIBLING_ROOT` at the directory containing the source projects:

```bash
export SIBLING_ROOT=..
regcap validate-sibling-sources --sibling-root "$SIBLING_ROOT"
regcap copy-sibling-outputs --sibling-root "$SIBLING_ROOT" --overwrite
regcap validate-imported-artifacts --output output/tables/imported_artifact_quality.csv
regcap write-mechanism-matrix --output output/tables/regulatory_capacity_mechanism_matrix.csv
regcap write-evidence-summary --output output/tables/source_evidence_summary.csv --report output/reports/source_evidence_summary.md
regcap write-dealer-bridge-memo --output output/reports/dealer_bridge_integration_memo.md
regcap write-design-report --matrix output/tables/regulatory_capacity_mechanism_matrix.csv --evidence-summary output/tables/source_evidence_summary.csv --output output/reports/regulatory_capacity_design_report.md
regcap validate-package --strict
```

Run each command's `--help` for output paths. Generated reports and tables live
under `output/`; raw, imported, and derived data live under `data/`. Both are
local artifacts ignored by Git.

## Interpretation

Configured mechanism rankings are hypotheses, not estimated effects or
independent corroboration. Consult each underlying producer's sample, methods,
uncertainty, and limits before using a summary.

The BidBridge import checks four pinned artifacts and their SHA-256 hashes.
Stale, missing, or unqualified artifacts supply no dealer evidence; schema
validity alone does not establish freshness.

The summaries do not turn inconclusive SLR results into support for Treasury
absorption, aggregate H.8 screens into individual-bank evidence, or dealer
inventory into final ownership. They do not establish that regulation caused a
deposit response. See [claim boundaries](docs/claim_boundaries.md) and
[source notes](docs/source_notes.md).
