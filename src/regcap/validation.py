from __future__ import annotations

from pathlib import Path

from .config import PROJECT_ROOT, ConfigError, validate_config
from .evidence import build_evidence_rows, read_evidence_summary, validate_imported_artifacts
from .mechanisms import MATRIX_COLUMNS
from .reporting import read_matrix


PUBLIC_BOUNDARY_PHRASES = [
    "Do not claim SLR relief robustly caused Treasury absorption",
    "Do not turn H.8 bank-group screens into individual-bank evidence",
    "Do not treat dealer inventory accumulation as final domestic absorption",
    "Do not claim domestic regulation caused the TDC deposit response",
]


def validate_package(strict: bool = False) -> list[str]:
    messages = validate_config()
    matrix = PROJECT_ROOT / "output/tables/regulatory_capacity_mechanism_matrix.csv"
    report = PROJECT_ROOT / "output/reports/regulatory_capacity_design_report.md"
    evidence_summary = PROJECT_ROOT / "output/tables/source_evidence_summary.csv"
    evidence_report = PROJECT_ROOT / "output/reports/source_evidence_summary.md"
    dealer_bridge_memo = PROJECT_ROOT / "output/reports/dealer_bridge_integration_memo.md"

    if matrix.exists():
        rows = read_matrix(matrix)
        if len(rows) != 5:
            raise ConfigError(f"Expected 5 mechanism rows, found {len(rows)}")
        missing_columns = set(MATRIX_COLUMNS).difference(rows[0])
        if missing_columns:
            raise ConfigError(f"Matrix missing columns: {sorted(missing_columns)}")
        messages.append(f"Validated matrix output: {matrix.relative_to(PROJECT_ROOT)}")
    elif strict:
        raise ConfigError(f"Missing strict matrix output: {matrix}")

    if report.exists():
        text = report.read_text(encoding="utf-8")
        missing_phrases = [phrase for phrase in PUBLIC_BOUNDARY_PHRASES if phrase not in text]
        if missing_phrases:
            raise ConfigError(f"Report missing required claim boundaries: {missing_phrases}")
        if evidence_summary.exists() and "## Source-backed status notes" not in text:
            raise ConfigError("Report missing source-backed status notes despite available evidence summary")
        messages.append(f"Validated design report: {report.relative_to(PROJECT_ROOT)}")
    elif strict:
        raise ConfigError(f"Missing strict design report: {report}")

    if evidence_summary.exists():
        evidence_rows = read_evidence_summary(evidence_summary)
        if len(evidence_rows) != 5:
            raise ConfigError(f"Expected 5 evidence rows, found {len(evidence_rows)}")
        if evidence_rows != build_evidence_rows(PROJECT_ROOT / "data/imported"):
            raise ConfigError("Evidence summary is stale relative to current imported artifacts; regenerate it")
        messages.append(f"Validated evidence summary: {evidence_summary.relative_to(PROJECT_ROOT)}")
    elif strict:
        raise ConfigError(f"Missing strict evidence summary: {evidence_summary}")

    if evidence_report.exists():
        evidence_text = evidence_report.read_text(encoding="utf-8")
        if "final holder absorption" not in evidence_text and "final domestic absorption" not in evidence_text:
            raise ConfigError("Evidence report missing dealer absorption claim boundary")
        messages.append(f"Validated evidence report: {evidence_report.relative_to(PROJECT_ROOT)}")
    elif strict:
        raise ConfigError(f"Missing strict evidence report: {evidence_report}")

    if dealer_bridge_memo.exists():
        memo_text = dealer_bridge_memo.read_text(encoding="utf-8")
        for phrase in (
            "Do not treat dealer inventory accumulation as final domestic absorption",
            "Do not infer customer identity or final holder location",
        ):
            if phrase not in memo_text:
                raise ConfigError(f"Dealer bridge memo missing required boundary: {phrase}")
        messages.append(f"Validated dealer bridge memo: {dealer_bridge_memo.relative_to(PROJECT_ROOT)}")
    elif strict:
        raise ConfigError(f"Missing strict dealer bridge memo: {dealer_bridge_memo}")

    imported_root = PROJECT_ROOT / "data/imported"
    if imported_root.exists():
        failures = [check for check in validate_imported_artifacts(imported_root) if check.failed]
        if failures:
            details = [f"{check.project}:{check.destination.name}:{check.status}" for check in failures]
            raise ConfigError(f"Imported artifact validation failed: {details}")
        messages.append("Validated imported artifact schemas")
    elif strict:
        raise ConfigError(f"Missing strict imported artifact root: {imported_root}")

    return messages


def ensure_relative_output(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path
