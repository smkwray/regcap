from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT, ConfigError, load_source_contracts
from .mechanisms import mechanism_by_id


IMPORTED_ROOT = PROJECT_ROOT / "data/imported"

QUALITY_COLUMNS = [
    "project",
    "destination",
    "required",
    "status",
    "artifact_format",
    "row_count",
    "column_count",
    "details",
]

EVIDENCE_COLUMNS = [
    "mechanism_id",
    "mechanism_label",
    "status",
    "source_projects",
    "evidence_note",
    "context_note",
    "claim_boundary",
]


@dataclass(frozen=True)
class ArtifactQualityCheck:
    project: str
    destination: Path
    required: bool
    status: str
    artifact_format: str
    row_count: int | None
    column_count: int | None
    details: str

    @property
    def failed(self) -> bool:
        return self.status in {"missing_required", "invalid"}


def _destination_path(destination: str, imported_root: Path) -> Path:
    relative = Path(destination)
    try:
        imported_relative = relative.relative_to("data/imported")
    except ValueError:
        return PROJECT_ROOT / relative
    return imported_root / imported_relative


def _iter_contract_artifacts(projects: set[str] | None = None) -> list[tuple[str, dict[str, Any]]]:
    artifacts: list[tuple[str, dict[str, Any]]] = []
    contracts = load_source_contracts()["contracts"]
    for project, contract in contracts.items():
        if projects is not None and project not in projects:
            continue
        project_required = bool(contract.get("required", False))
        for artifact in contract["artifacts"]:
            item = dict(artifact)
            item["required"] = bool(item.get("required", project_required))
            artifacts.append((project, item))
    return artifacts


def _read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return rows, list(reader.fieldnames or [])


def _schema_check(path: Path, schema: dict[str, Any]) -> tuple[str, int | None, int | None, str]:
    artifact_format = str(schema["format"])
    if artifact_format == "csv":
        rows, columns = _read_csv_rows(path)
        missing = sorted(set(schema["required_columns"]).difference(columns))
        if missing:
            return artifact_format, len(rows), len(columns), f"missing columns: {missing}"
        if not rows:
            return artifact_format, 0, len(columns), "empty csv"
        return artifact_format, len(rows), len(columns), "ok"

    if artifact_format == "json":
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return artifact_format, None, None, "json root is not an object"
        missing = sorted(set(schema["required_keys"]).difference(data))
        if missing:
            return artifact_format, None, len(data), f"missing keys: {missing}"
        return artifact_format, None, len(data), "ok"

    text = path.read_text(encoding="utf-8")
    heading = str(schema["required_heading"])
    if heading not in text[:500]:
        return artifact_format, None, None, f"missing heading: {heading}"
    if len(text.strip()) < 100:
        return artifact_format, None, None, "markdown is too short"
    return artifact_format, None, None, "ok"


def validate_imported_artifacts(
    imported_root: Path = IMPORTED_ROOT,
    projects: set[str] | None = None,
) -> list[ArtifactQualityCheck]:
    checks: list[ArtifactQualityCheck] = []
    for project, artifact in _iter_contract_artifacts(projects=projects):
        destination = _destination_path(str(artifact["destination"]), imported_root)
        required = bool(artifact["required"])
        schema = artifact.get("schema") or {"format": destination.suffix.lstrip(".")}
        artifact_format = str(schema.get("format", destination.suffix.lstrip(".")))

        if not destination.exists():
            status = "missing_required" if required else "missing_optional"
            checks.append(
                ArtifactQualityCheck(
                    project=project,
                    destination=destination,
                    required=required,
                    status=status,
                    artifact_format=artifact_format,
                    row_count=None,
                    column_count=None,
                    details="not found",
                )
            )
            continue

        try:
            artifact_format, row_count, column_count, details = _schema_check(destination, schema)
        except (OSError, csv.Error, json.JSONDecodeError, UnicodeDecodeError) as exc:
            checks.append(
                ArtifactQualityCheck(
                    project=project,
                    destination=destination,
                    required=required,
                    status="invalid",
                    artifact_format=artifact_format,
                    row_count=None,
                    column_count=None,
                    details=str(exc),
                )
            )
            continue

        checks.append(
            ArtifactQualityCheck(
                project=project,
                destination=destination,
                required=required,
                status="ok" if details == "ok" else "invalid",
                artifact_format=artifact_format,
                row_count=row_count,
                column_count=column_count,
                details=details,
            )
        )
    return checks


def write_artifact_quality_csv(checks: list[ArtifactQualityCheck], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUALITY_COLUMNS)
        writer.writeheader()
        for check in checks:
            writer.writerow(
                {
                    "project": check.project,
                    "destination": _relative_display(check.destination),
                    "required": check.required,
                    "status": check.status,
                    "artifact_format": check.artifact_format,
                    "row_count": "" if check.row_count is None else check.row_count,
                    "column_count": "" if check.column_count is None else check.column_count,
                    "details": check.details,
                }
            )
    return output


def _relative_display(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ConfigError(f"Expected JSON object: {path}")
    return data


def _format_number(value: str | float | int | None, digits: int = 2) -> str:
    if value in {None, ""}:
        return "n/a"
    return f"{float(value):.{digits}f}"


def _find_row(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str] | None:
    for row in rows:
        if row.get(key) == value:
            return row
    return None


def build_evidence_rows(imported_root: Path = IMPORTED_ROOT) -> list[dict[str, str]]:
    mechanisms = mechanism_by_id()
    rows: list[dict[str, str]] = []

    rows.append(_dealer_bridge_row(imported_root, mechanisms["dealer_repo_bridge"]))
    rows.append(_duration_loss_row(imported_root, mechanisms["duration_loss_aoci_htm"]))
    rows.append(_slr_row(imported_root, mechanisms["slr_leverage_capacity"]))
    rows.append(_lcr_row(imported_root, mechanisms["lcr_hqla_demand"]))
    rows.append(_gsib_row(mechanisms["gsib_window_dressing"]))
    return rows


def _base_row(
    mechanism: dict[str, str],
    status: str,
    sources: str,
    note: str,
    boundary: str,
    context: str = "",
) -> dict[str, str]:
    return {
        "mechanism_id": mechanism["mechanism_id"],
        "mechanism_label": mechanism["mechanism_label"],
        "status": status,
        "source_projects": sources,
        "evidence_note": note,
        "context_note": context,
        "claim_boundary": boundary,
    }


def _dealer_bridge_row(imported_root: Path, mechanism: dict[str, str]) -> dict[str, str]:
    path = imported_root / "bidbridge/bidbridge_promotion_summary.csv"
    if not path.exists():
        return _base_row(
            mechanism,
            "missing",
            "bidbridge",
            "Required bidbridge promotion summary is not imported.",
            mechanism["claim_boundary_unsafe"],
        )
    rows, _ = _read_csv_rows(path)
    headline = _find_row(rows, "status", "headline") or _find_row(rows, "claim", "lp_same_week_full_sample")
    same_week = _find_row(rows, "claim", "lp_same_week_full_sample")
    if headline is None:
        note = "Promotion table is present, but no headline or same-week claim row was found."
    else:
        note = (
            f"{headline['claim']} reports {headline['estimate']} {headline['unit']} "
            f"({headline['stat']}); same-week LP context is "
            f"{same_week['estimate']} {same_week['unit']} ({same_week['stat']})"
            if same_week
            else f"{headline['claim']} reports {headline['estimate']} {headline['unit']} ({headline['stat']})"
        )
    return _base_row(
        mechanism,
        "strongest near-term promotion",
        "bidbridge; qrawatch",
        note,
        "Short-run dealer warehousing evidence only; not final holder absorption.",
        _qrawatch_dealer_context(imported_root),
    )


def _duration_loss_row(imported_root: Path, mechanism: dict[str, str]) -> dict[str, str]:
    path = imported_root / "slrwatch/constraint_decomposition_regime_summary.csv"
    if not path.exists():
        return _base_row(
            mechanism,
            "missing",
            "slrwatch; bankcap; qrawatch",
            "Required slrwatch regime summary is not imported.",
            mechanism["claim_boundary_unsafe"],
        )
    rows, _ = _read_csv_rows(path)
    duration_rows = [row for row in rows if row.get("policy_regime") == "duration_loss_window"]
    pieces = [
        f"{row['entity_source']} duration-loss dominant share "
        f"{_format_number(float(row['duration_loss_dominant_share']) * 100, 1)}%"
        for row in duration_rows
        if row.get("duration_loss_dominant_share") not in {None, ""}
    ]
    note = "; ".join(pieces) if pieces else "Regime summary is present, but duration-loss window rows were not found."
    return _base_row(
        mechanism,
        "guarded regime mechanism",
        "slrwatch; bankcap; qrawatch",
        note,
        "Use as regime-dependent constraint evidence, not a standalone explanation of TDC residuals.",
        _qrawatch_duration_context(imported_root),
    )


def _slr_row(imported_root: Path, mechanism: dict[str, str]) -> dict[str, str]:
    path = imported_root / "slrwatch/event_2020_did_results.csv"
    if not path.exists():
        return _base_row(
            mechanism,
            "missing",
            "slrwatch; bankcap",
            "Required slrwatch event-study surface is not imported.",
            mechanism["claim_boundary_unsafe"],
        )
    rows, _ = _read_csv_rows(path)
    ust_rows = [row for row in rows if row.get("outcome") == "ust_inventory_fv_scaled"]
    if ust_rows:
        pieces = [
            f"{row['treatment']} coef {_format_number(row.get('coef'), 4)}, p={_format_number(row.get('pvalue'), 4)}"
            for row in ust_rows[:3]
        ]
        note = "Cautionary event-study read: " + "; ".join(pieces) + "."
    else:
        note = "Event-study surface is present, but UST inventory rows were not found."
    return _base_row(
        mechanism,
        "cautionary mechanism classifier",
        "slrwatch; bankcap",
        note,
        "Do not treat SLR relief as a robust causal Treasury-absorption result.",
    )


def _lcr_row(imported_root: Path, mechanism: dict[str, str]) -> dict[str, str]:
    path = imported_root / "bankcap/h8_mechanism_summary.json"
    data = _read_json_object(path)
    if data is None:
        return _base_row(
            mechanism,
            "missing",
            "bankcap; slrwatch; qrawatch",
            "Required bankcap H.8 mechanism summary is not imported.",
            mechanism["claim_boundary_unsafe"],
        )
    sample = data.get("common_target_sample", {})
    if not isinstance(sample, dict):
        sample = {}
    ingestion = data.get("bank_level_ingestion", {})
    if not isinstance(ingestion, dict):
        ingestion = {}
    note = (
        f"{data.get('recommendation', 'H.8 summary imported')}; "
        f"context-complete share {_format_number(sample.get('context_complete_share'), 2)}, "
        f"coupon-heavy rows {sample.get('coupon_heavy_rows', 'n/a')}, "
        f"bank-level ingestion {ingestion.get('status', 'n/a')}."
    )
    return _base_row(
        mechanism,
        "partial mechanism context",
        "bankcap; slrwatch; qrawatch",
        note,
        "H.8 bank-group evidence is context only, not bank-level identification.",
        _qrawatch_duration_context(imported_root),
    )


def _gsib_row(mechanism: dict[str, str]) -> dict[str, str]:
    return _base_row(
        mechanism,
        "sidecar design only",
        "slrwatch; bidbridge",
        "No dedicated imported G-SIB or reporting-date compact table is contracted yet; keep as an appendix/calendar-capacity design lane.",
        "Treat as temporary capacity-window context, not permanent Treasury demand.",
    )


def _qrawatch_dealer_context(imported_root: Path) -> str:
    dealer_path = imported_root / "qrawatch/primary_dealer_summary.csv"
    qra_path = imported_root / "qrawatch/qra_event_shock_summary.csv"
    pieces: list[str] = []
    if dealer_path.exists():
        rows, _ = _read_csv_rows(dealer_path)
        latest = _find_row(rows, "summary_type", "latest_snapshot")
        if latest:
            pieces.append(
                f"qrawatch dealer panel reports {latest.get('value', 'n/a')} "
                f"{latest.get('units', 'rows')} as of {latest.get('as_of_date', 'n/a')}"
            )
    if qra_path.exists():
        rows, _ = _read_csv_rows(qra_path)
        usable = sum(1 for row in rows if row.get("usable_for_headline") == "True")
        descriptive = sum(1 for row in rows if row.get("claim_scope") == "descriptive_only")
        pieces.append(f"QRA shock table has {usable} headline-usable events and {descriptive} descriptive-only rows")
    return "; ".join(pieces) if pieces else "Optional qrawatch dealer/QRA context is not imported."


def _qrawatch_duration_context(imported_root: Path) -> str:
    path = imported_root / "qrawatch/duration_supply_summary.csv"
    if not path.exists():
        return "Optional qrawatch duration-supply context is not imported."
    rows, _ = _read_csv_rows(path)
    if not rows:
        return "qrawatch duration-supply table is imported but empty."
    latest = rows[-1]
    positive_rows = sum(
        1
        for row in rows
        if row.get("headline_public_duration_supply") not in {None, ""}
        and float(row["headline_public_duration_supply"]) > 0
    )
    return (
        f"qrawatch duration table has {len(rows)} weekly rows; latest date {latest.get('date', 'n/a')}; "
        f"{positive_rows} rows have positive headline public duration supply."
    )


def write_evidence_summary_csv(rows: list[dict[str, str]], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EVIDENCE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return output


def read_evidence_summary(path: Path) -> list[dict[str, str]]:
    rows, columns = _read_csv_rows(path)
    missing = set(EVIDENCE_COLUMNS).difference(columns)
    if missing:
        raise ConfigError(f"Evidence summary missing columns: {sorted(missing)}")
    return rows


def write_evidence_summary_report(rows: list[dict[str, str]], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Source Evidence Summary",
        "",
        "This public-safe summary reads compact imported outputs from sibling projects. It preserves each source boundary and does not reproduce raw-data pipelines.",
        "",
        "| Mechanism | Status | Source projects | Evidence note | Context note | Claim boundary |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['mechanism_label']} | {row['status']} | {row['source_projects']} | "
            f"{row['evidence_note']} | {row.get('context_note', '')} | {row['claim_boundary']} |"
        )
    lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def write_dealer_bridge_memo(evidence_rows: list[dict[str, str]], output: Path) -> Path:
    dealer = next((row for row in evidence_rows if row["mechanism_id"] == "dealer_repo_bridge"), None)
    duration = next((row for row in evidence_rows if row["mechanism_id"] == "duration_loss_aoci_htm"), None)
    slr = next((row for row in evidence_rows if row["mechanism_id"] == "slr_leverage_capacity"), None)
    if dealer is None:
        raise ConfigError("Evidence summary has no dealer_repo_bridge row")

    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Dealer Bridge Integration Memo",
        "",
        "## Recommended use",
        "",
        "Use the dealer/repo bridge as the first promoted `regcap` integration lane. The supported role is narrow: dealers can warehouse Treasury supply over short horizons before final holder location is measured elsewhere.",
        "",
        "## Source-backed status",
        "",
        f"- Dealer bridge status: {dealer['status']}.",
        f"- Dealer bridge evidence: {dealer['evidence_note']}",
    ]
    if dealer.get("context_note"):
        lines.append(f"- Issuance and dealer context: {dealer['context_note']}")
    if duration is not None:
        lines.append(f"- Duration-capacity interaction: {duration['evidence_note']}")
    if slr is not None:
        lines.append(f"- Leverage-capacity caution: {slr['evidence_note']}")

    lines.extend(
        [
            "",
            "## Integration boundary",
            "",
            "- Do not treat dealer inventory accumulation as final domestic absorption.",
            "- Do not infer customer identity or final holder location from dealer warehousing evidence.",
            "- Do not claim SLR relief robustly caused Treasury absorption.",
            "- Keep `rowflow` as the foreign/external absorption branch and use it only as contrast context here.",
            "",
            "## Design handoff",
            "",
            "The next analytical layer should join dealer warehousing timing to final-holder modules only through compact public-safe summaries. `regcap` should continue to own mechanism classification, source status, and claim-boundary enforcement rather than raw auction, dealer, or holder-flow ingestion.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")
    return output
