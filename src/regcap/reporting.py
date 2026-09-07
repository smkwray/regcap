from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import PROJECT_ROOT
from .evidence import read_evidence_summary
from .mechanisms import MATRIX_COLUMNS, mechanism_matrix_rows


def write_mechanism_matrix(output: Path) -> Path:
    rows = mechanism_matrix_rows()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return output


def read_matrix(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    missing = set(MATRIX_COLUMNS).difference(reader.fieldnames or [])
    if missing:
        raise ValueError(f"Matrix missing columns: {sorted(missing)}")
    return rows


def write_design_report(matrix_path: Path, output: Path, evidence_summary_path: Path | None = None) -> Path:
    rows = read_matrix(matrix_path)
    evidence_by_mechanism = {}
    if evidence_summary_path is not None and evidence_summary_path.exists():
        evidence_by_mechanism = {
            row["mechanism_id"]: row for row in read_evidence_summary(evidence_summary_path)
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Regulatory Capacity Design Report",
        "",
        "This report summarizes domestic regulatory and balance-sheet capacity mechanisms for the Treasury Deposit Component research. It is an integrator output: it consumes compact public-safe outputs and metadata from sibling projects, and it does not duplicate raw-data pipelines.",
        "",
        "## Core question",
        "",
        "When Treasury supply is not absorbed abroad, what domestic balance-sheet constraints determine whether banks, dealers, MMFs, or the Fed absorb the marginal security, and how does that alter the domestic deposit/reserve footprint?",
        "",
        "## Claim boundaries",
        "",
        "- Do not claim SLR relief robustly caused Treasury absorption; the current SLR evidence is cautionary and mixed.",
        "- Do not turn H.8 bank-group screens into individual-bank evidence.",
        "- Do not treat dealer inventory accumulation as final domestic absorption.",
        "- Do not claim domestic regulation caused the TDC deposit response.",
        "- Do not duplicate raw Call Report, FR Y-9C, or FR Y-15 ingestion in this package.",
        "- Do not write to sibling projects.",
        "",
        "## Configured research priorities",
        "",
        "These are design hypotheses, not evidence-derived rankings or admission decisions.",
        "",
        "| Priority | Mechanism | Primary project | Recommendation |",
        "|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['implementation_priority']} | {row['mechanism_label']} | "
            f"{row['primary_existing_project']} | {row['go_no_go_recommendation']} |"
        )

    if evidence_by_mechanism:
        lines.extend(
            [
                "",
                "## Source-backed status notes",
                "",
                "| Mechanism | Status | Evidence note | Context note | Claim boundary |",
                "|---|---|---|---|---|",
            ]
        )
        for row in rows:
            evidence = evidence_by_mechanism.get(row["mechanism_id"])
            if not evidence:
                continue
            lines.append(
                f"| {row['mechanism_label']} | {evidence['status']} | "
                f"{evidence['evidence_note']} | {evidence.get('context_note', '')} | {evidence['claim_boundary']} |"
            )

    lines.extend(["", "## Mechanism notes", ""])
    for row in rows:
        lines.extend(
            [
                f"### {row['mechanism_label']}",
                "",
                f"Research function: {row['research_function']}",
                "",
                f"Cleanest estimand: {row['cleanest_estimand']}",
                "",
                f"Identification leverage: {row['identification_leverage']}",
                "",
                f"TDC connection: {row['tdc_connection']}",
                "",
                f"Safe claim: {row['claim_boundary_safe']}",
                "",
                f"Unsafe claim: {row['claim_boundary_unsafe']}",
                "",
            ]
        )

    lines.extend(
        [
            "## First implementation read",
            "",
            "The configured priorities organize possible research. Evidence status must be read from the source-backed notes, including missing inputs and failed diagnostics. This report neither promotes a mechanism nor provides independent empirical authority.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def write_manifest(
    matrix: Path | None = None,
    report: Path | None = None,
    evidence_summary: Path | None = None,
    evidence_report: Path | None = None,
    dealer_bridge_memo: Path | None = None,
) -> Path:
    path = PROJECT_ROOT / "output/manifests/regcap_manifest.json"
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": "regcap",
        "outputs": {},
    }
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        if isinstance(existing, dict) and isinstance(existing.get("outputs"), dict):
            manifest["outputs"].update(existing["outputs"])
    if matrix:
        manifest["outputs"]["mechanism_matrix"] = str(matrix.relative_to(PROJECT_ROOT))
    if report:
        manifest["outputs"]["design_report"] = str(report.relative_to(PROJECT_ROOT))
    if evidence_summary:
        manifest["outputs"]["source_evidence_summary"] = str(evidence_summary.relative_to(PROJECT_ROOT))
    if evidence_report:
        manifest["outputs"]["source_evidence_report"] = str(evidence_report.relative_to(PROJECT_ROOT))
    if dealer_bridge_memo:
        manifest["outputs"]["dealer_bridge_memo"] = str(dealer_bridge_memo.relative_to(PROJECT_ROOT))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path
