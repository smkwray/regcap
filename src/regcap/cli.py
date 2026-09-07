from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import ConfigError, PROJECT_ROOT, validate_config
from .contracts import copy_sibling_outputs, validate_sibling_sources, write_source_check_csv
from .evidence import (
    build_evidence_rows,
    validate_imported_artifacts,
    write_artifact_quality_csv,
    write_dealer_bridge_memo,
    write_evidence_summary_csv,
    write_evidence_summary_report,
)
from .reporting import write_design_report, write_manifest, write_mechanism_matrix
from .validation import ensure_relative_output, validate_package


def _print_messages(messages: list[str]) -> None:
    for message in messages:
        print(message)


def cmd_validate_config(_: argparse.Namespace) -> int:
    _print_messages(validate_config())
    return 0


def cmd_validate_sibling_sources(args: argparse.Namespace) -> int:
    sibling_root = Path(args.sibling_root).expanduser().resolve()
    checks = validate_sibling_sources(sibling_root)
    for check in checks:
        print(f"{check.status}: {check.project} {check.source_path}")
    if args.output:
        write_source_check_csv(checks, ensure_relative_output(Path(args.output)))
    missing = [check for check in checks if check.required and not check.exists]
    if missing:
        print(f"Missing required sibling artifacts: {len(missing)}", file=sys.stderr)
        return 1
    return 0


def cmd_copy_sibling_outputs(args: argparse.Namespace) -> int:
    sibling_root = Path(args.sibling_root).expanduser().resolve()
    manifest = copy_sibling_outputs(sibling_root, overwrite=args.overwrite)
    copied = len(manifest["copied"])
    missing_required = len(manifest["missing_required"])
    skipped = len(manifest["skipped"])
    print(f"Copied {copied} artifacts; skipped {skipped}; missing required {missing_required}")
    print("Wrote output/manifests/regcap_manifest.json")
    return 1 if missing_required else 0


def cmd_validate_imported_artifacts(args: argparse.Namespace) -> int:
    checks = validate_imported_artifacts()
    for check in checks:
        destination = check.destination.relative_to(PROJECT_ROOT)
        print(f"{check.status}: {check.project} {destination} ({check.details})")
    if args.output:
        write_artifact_quality_csv(checks, ensure_relative_output(Path(args.output)))
    failures = [check for check in checks if check.failed]
    if failures:
        print(f"Imported artifact validation failures: {len(failures)}", file=sys.stderr)
        return 1
    return 0


def cmd_write_mechanism_matrix(args: argparse.Namespace) -> int:
    output = ensure_relative_output(Path(args.output))
    write_mechanism_matrix(output)
    write_manifest(matrix=output if output.is_absolute() else PROJECT_ROOT / output)
    print(f"Wrote {output}")
    return 0


def cmd_write_design_report(args: argparse.Namespace) -> int:
    matrix = ensure_relative_output(Path(args.matrix))
    output = ensure_relative_output(Path(args.output))
    evidence_summary = ensure_relative_output(Path(args.evidence_summary)) if args.evidence_summary else None
    write_design_report(matrix, output, evidence_summary_path=evidence_summary)
    write_manifest(matrix=matrix, report=output, evidence_summary=evidence_summary)
    print(f"Wrote {output}")
    return 0


def cmd_write_evidence_summary(args: argparse.Namespace) -> int:
    output = ensure_relative_output(Path(args.output))
    report = ensure_relative_output(Path(args.report)) if args.report else None
    rows = build_evidence_rows()
    write_evidence_summary_csv(rows, output)
    if report is not None:
        write_evidence_summary_report(rows, report)
    write_manifest(evidence_summary=output, evidence_report=report)
    print(f"Wrote {output}")
    if report is not None:
        print(f"Wrote {report}")
    return 0


def cmd_write_dealer_bridge_memo(args: argparse.Namespace) -> int:
    output = ensure_relative_output(Path(args.output))
    rows = build_evidence_rows()
    write_dealer_bridge_memo(rows, output)
    write_manifest(dealer_bridge_memo=output)
    print(f"Wrote {output}")
    return 0


def cmd_validate_package(args: argparse.Namespace) -> int:
    _print_messages(validate_package(strict=args.strict))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="regcap", description="Regulatory capacity integrator CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate-config", help="Validate config files")
    validate.set_defaults(func=cmd_validate_config)

    sibling = subparsers.add_parser("validate-sibling-sources", help="Validate sibling compact artifacts")
    sibling.add_argument("--sibling-root", required=True)
    sibling.add_argument("--output", default="")
    sibling.set_defaults(func=cmd_validate_sibling_sources)

    copy = subparsers.add_parser("copy-sibling-outputs", help="Copy sibling compact artifacts into ignored data/imported")
    copy.add_argument("--sibling-root", required=True)
    copy.add_argument("--overwrite", action="store_true")
    copy.set_defaults(func=cmd_copy_sibling_outputs)

    imported = subparsers.add_parser("validate-imported-artifacts", help="Validate copied sibling artifact schemas")
    imported.add_argument("--output", default="")
    imported.set_defaults(func=cmd_validate_imported_artifacts)

    matrix = subparsers.add_parser("write-mechanism-matrix", help="Write regulatory capacity mechanism CSV")
    matrix.add_argument("--output", required=True)
    matrix.set_defaults(func=cmd_write_mechanism_matrix)

    evidence = subparsers.add_parser("write-evidence-summary", help="Write public-safe source evidence summary")
    evidence.add_argument("--output", required=True)
    evidence.add_argument("--report", default="")
    evidence.set_defaults(func=cmd_write_evidence_summary)

    dealer_memo = subparsers.add_parser("write-dealer-bridge-memo", help="Write dealer bridge integration memo")
    dealer_memo.add_argument("--output", required=True)
    dealer_memo.set_defaults(func=cmd_write_dealer_bridge_memo)

    report = subparsers.add_parser("write-design-report", help="Write public-safe design report")
    report.add_argument("--matrix", required=True)
    report.add_argument("--output", required=True)
    report.add_argument("--evidence-summary", default="")
    report.set_defaults(func=cmd_write_design_report)

    package = subparsers.add_parser("validate-package", help="Validate config and generated outputs")
    package.add_argument("--strict", action="store_true")
    package.set_defaults(func=cmd_validate_package)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ConfigError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
