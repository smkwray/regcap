# RegCap

RegCap combines results from companion research repositories into tables and Markdown reports on how bank regulation and balance sheets limit US domestic purchases of Treasury securities. It covers the Supplementary Leverage Ratio (SLR), the Liquidity Coverage Ratio and its high-quality liquid assets (LCR/HQLA), surcharges on global systemically important banks (G-SIBs), dealer leverage and repo financing, and duration losses on securities, with their treatment as accumulated other comprehensive income (AOCI) or held-to-maturity (HTM) holdings.

RegCap runs no regressions. Every result it reports comes from a source repository, and none estimates an effect on the Treasury Deposit Component (TDC), the part of the change in deposits at US banks and credit unions that comes from Treasury payments and trades in Treasury securities ([tdcest](https://github.com/smkwray/tdcest)).

## Data

RegCap downloads nothing. It copies summary files from these repositories, so clone them side by side and build them first:

| Repository | Required | Supplies |
|---|---|---|
| [SLR Watch](https://github.com/smkwray/slrwatch) | Yes | 2020 SLR event study and constraint decomposition |
| [BankCap](https://github.com/smkwray/bankcap) | Yes | Bank-group screen from the Federal Reserve's weekly H.8 balance-sheet release |
| [BidBridge](https://github.com/smkwray/bidbridge) | Yes | Dealer balance-sheet estimates, pinned by SHA-256 hash |
| [QRA Watch](https://github.com/smkwray/qrawatch) | No | Issuance and Quarterly Refunding Announcement context |
| [rowflow](https://github.com/smkwray/rowflow) | No | Foreign-absorption results, for contrast |

`config/source_contracts.yml` lists the expected files, and [docs/source_notes.md](docs/source_notes.md) describes each source's role.

## Install

Python 3.11 or later. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Usage

With the companion repositories in the parent directory:

```bash
regcap validate-sibling-sources --sibling-root ..
regcap copy-sibling-outputs --sibling-root .. --overwrite
make package PYTHON=python
```

These commands list missing source files, copy the rest into `data/imported/`, then check the copies and write and validate every table and report. `regcap --help` lists the individual commands.

## Output

Files go to `output/`, which Git ignores.

| File | Contents |
|---|---|
| `tables/regulatory_capacity_mechanism_matrix.csv` | One row per mechanism: sources, data, estimand, identification, connection to TDC and research priority ([columns](docs/mechanism_matrix.md)) |
| `tables/source_evidence_summary.csv`, `reports/source_evidence_summary.md` | Each mechanism's status and headline source result |
| `reports/dealer_bridge_integration_memo.md` | The dealer result in issuance, duration and leverage context |
| `reports/regulatory_capacity_design_report.md` | Priorities and notes for each mechanism |
| `tables/imported_artifact_quality.csv` | Structure and hash check for each copied file |

## Limits

- The ranking in `config/mechanisms.yml` is a research priority, not an evidence ranking, and each summary carries its source's sample and limits.
- H.8 results describe bank groups, not individual banks; dealer inventory shows short-run warehousing, not final holders.
- Checks confirm structure and BidBridge hashes, not that source outputs are current. A missing or mismatched BidBridge file leaves the dealer row without evidence.

## Tests

The tests run offline on fixtures:

```bash
python -B -m pytest -q
ruff check .
regcap validate-config
```
