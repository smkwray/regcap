from __future__ import annotations

from typing import Any

from .config import load_mechanisms


MATRIX_COLUMNS = [
    "mechanism_id",
    "mechanism_label",
    "research_function",
    "primary_existing_project",
    "supporting_projects",
    "public_data_sources",
    "frequency",
    "cleanest_estimand",
    "identification_leverage",
    "tdc_connection",
    "claim_boundary_safe",
    "claim_boundary_unsafe",
    "go_no_go_recommendation",
    "implementation_priority",
]


def _join(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return str(value)


def mechanism_matrix_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for mechanism in sorted(load_mechanisms(), key=lambda row: int(row["implementation_priority"])):
        rows.append({column: _join(mechanism[column]) for column in MATRIX_COLUMNS})
    return rows


def mechanism_by_id() -> dict[str, dict[str, str]]:
    return {row["mechanism_id"]: row for row in mechanism_matrix_rows()}
