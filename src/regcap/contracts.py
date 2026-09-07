from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT, load_source_contracts


@dataclass(frozen=True)
class SourceCheck:
    project: str
    source_path: Path
    destination: Path
    required: bool
    exists: bool
    notes: str

    @property
    def status(self) -> str:
        if self.exists:
            return "ok"
        if self.required:
            return "missing_required"
        return "missing_optional"


def _iter_artifacts(sibling_root: Path) -> list[SourceCheck]:
    contracts = load_source_contracts()["contracts"]
    checks: list[SourceCheck] = []
    for project, contract in contracts.items():
        project_root = sibling_root / project
        project_required = bool(contract.get("required", False))
        for artifact in contract["artifacts"]:
            required = bool(artifact.get("required", project_required))
            source_path = project_root / artifact["path"]
            checks.append(
                SourceCheck(
                    project=project,
                    source_path=source_path,
                    destination=PROJECT_ROOT / artifact["destination"],
                    required=required,
                    exists=source_path.exists() and source_path.is_file(),
                    notes=str(artifact.get("notes", "")),
                )
            )
    return checks


def validate_sibling_sources(sibling_root: Path) -> list[SourceCheck]:
    return _iter_artifacts(sibling_root)


def copy_sibling_outputs(sibling_root: Path, overwrite: bool = False) -> dict[str, Any]:
    copied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    missing_required: list[dict[str, Any]] = []

    for check in _iter_artifacts(sibling_root):
        record = {
            "project": check.project,
            "source_path": str(check.source_path),
            "destination": str(check.destination.relative_to(PROJECT_ROOT)),
            "required": check.required,
            "status": check.status,
            "notes": check.notes,
        }
        if not check.exists:
            if check.required:
                missing_required.append(record)
            else:
                skipped.append(record)
            continue
        if check.destination.exists() and not overwrite:
            record["status"] = "exists_skipped"
            skipped.append(record)
            continue
        check.destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(check.source_path, check.destination)
        record["status"] = "copied"
        copied.append(record)

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": "regcap",
        "copied": copied,
        "skipped": skipped,
        "missing_required": missing_required,
    }
    manifest_path = PROJECT_ROOT / "output/manifests/regcap_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def write_source_check_csv(checks: list[SourceCheck], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["project", "status", "required", "source_path", "destination", "notes"],
        )
        writer.writeheader()
        for check in checks:
            writer.writerow(
                {
                    "project": check.project,
                    "status": check.status,
                    "required": check.required,
                    "source_path": str(check.source_path),
                    "destination": str(check.destination.relative_to(PROJECT_ROOT)),
                    "notes": check.notes,
                }
            )
