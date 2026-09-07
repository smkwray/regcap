from __future__ import annotations

import json
import hashlib
import re

import pytest

from regcap import evidence
from regcap.config import load_source_contracts
from pathlib import Path

from regcap.evidence import (
    build_evidence_rows,
    read_evidence_summary,
    validate_imported_artifacts,
    write_dealer_bridge_memo,
    write_evidence_summary_csv,
    write_evidence_summary_report,
)
from regcap.reporting import write_design_report, write_mechanism_matrix


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_minimal_imports(imported_root: Path) -> None:
    _write_text(
        imported_root / "bidbridge/bidbridge_promotion_summary.csv",
        "\n".join(
            [
                "claim,artifact,estimate,unit,stat,status,interpretation",
                "lp_same_week_full_sample,outputs/tables/lp_results.csv,7.23,$B inventory change,\"t=3.78, p=0.0002\",supporting,Immediate dealer inventory response.",
                "lp_placebo_boundary,outputs/tables/lp_placebo_results.csv,2,count,2 of 5,boundary,LP does not provide clean timing validation.",
                "maturity_bucket_fe_monday,outputs/tables/panel_fe_results.csv,9.45,$M dealer position per $B announced supply,\"se=3.54, 95% CI [2.51, 16.39]\",headline,Within-week supply maps to dealer positions.",
            ]
        ),
    )
    _write_text(
        imported_root / "bidbridge/bidbridge_promotion_memo.md",
        "# BidBridge Promotion Memo\n\nRecommended use preserves dealer warehousing as a bridge, not final ownership.",
    )
    _write_text(
        imported_root / "bidbridge/lp_results.csv",
        "horizon,beta,se,t_stat,p_value,ci_lower,ci_upper,n_obs,r_squared,regime\n0,7229.79,1910.78,3.78,0.0002,3484.7,10974.9,675,0.12,full_sample\n",
    )
    _write_text(
        imported_root / "bidbridge/panel_fe_results.csv",
        "specification,variable,coefficient,std_error,ci_lower,ci_upper\npooled,Announced supply ($B),3.95,1.64,0.74,7.16\n",
    )
    _write_text(
        imported_root / "slrwatch/event_2020_did_results.csv",
        "treatment,outcome,coef,std_err,pvalue,nobs\nlow_headroom_treated,ust_inventory_fv_scaled,-0.0015,0.0062,0.8133,228\n",
    )
    _write_text(
        imported_root / "slrwatch/constraint_decomposition_regime_summary.csv",
        "entity_source,policy_regime,observation_count,mean_headroom_pp,mean_unrealized_loss_tier1,leverage_dominant_share,duration_loss_dominant_share,funding_dominant_share\ninsured_bank,duration_loss_window,135,0.0314,0.0509,0.1630,0.6593,0.1778\n",
    )
    _write_text(
        imported_root / "bankcap/h8_mechanism_summary.json",
        json.dumps(
            {
                "recommendation": "PARTIAL GO: H.8 mechanism context only",
                "claim_boundary": "bank-group context only",
                "common_target_sample": {"context_complete_share": 0.57, "coupon_heavy_rows": 0},
                "bank_level_ingestion": {"status": "blocked"},
                "gate_checks": ["sample periods: 639"],
            }
        ),
    )
    _write_text(
        imported_root / "qrawatch/primary_dealer_summary.csv",
        "summary_type,dataset_type,series_id,measure,value,units,as_of_date,frequency,source_quality,source_file\nlatest_snapshot,latest_series_snapshot,all,latest_row_count,977,count,2026-03-11,weekly,csv_canonical,primary_dealer_panel.csv\n",
    )
    _write_text(
        imported_root / "qrawatch/duration_supply_summary.csv",
        "date,coupon_like_total,headline_public_duration_supply,headline_source_quality,value_units,frequency,sign_convention\n2026-01-07,0.0,0.0,hybrid,USD notional,weekly,Higher values imply more duration supply.\n2026-01-14,1.0,5.0,hybrid,USD notional,weekly,Higher values imply more duration supply.\n",
    )
    _write_text(
        imported_root / "qrawatch/qra_event_shock_summary.csv",
        "quarter,event_id,event_date_aligned,timing_quality,shock_review_status,usable_for_headline,claim_scope\n2026Q1,qra_2026_02,2026-02-04,official,pending,True,descriptive_only\n",
    )
    _write_text(
        imported_root / "rowflow/rowflow_results_summary.csv",
        "sample,frequency,rows,start,end,official_flow_usd_millions,private_flow_usd_millions\nTIC test panel,monthly,2,2026-01,2026-02,1.0,2.0\n",
    )


def test_validate_imported_artifacts_checks_contract_schema(tmp_path: Path, monkeypatch):
    imported_root = tmp_path / "imported"
    _write_minimal_imports(imported_root)
    _pin_fixture_contracts(imported_root, monkeypatch)

    checks = validate_imported_artifacts(imported_root=imported_root, projects={"bidbridge"})

    assert len(checks) == 4
    assert not [check for check in checks if check.failed]
    assert any(check.row_count == 3 for check in checks if check.destination.name == "bidbridge_promotion_summary.csv")


def test_optional_qrawatch_and_rowflow_contracts_are_schema_checked(tmp_path: Path, monkeypatch):
    imported_root = tmp_path / "imported"
    _write_minimal_imports(imported_root)
    _pin_fixture_contracts(imported_root, monkeypatch)

    checks = validate_imported_artifacts(imported_root=imported_root, projects={"qrawatch", "rowflow"})

    assert len(checks) == 4
    assert not [check for check in checks if check.failed]


def test_evidence_summary_can_feed_design_report(tmp_path: Path, monkeypatch):
    imported_root = tmp_path / "imported"
    _write_minimal_imports(imported_root)
    _pin_fixture_contracts(imported_root, monkeypatch)
    evidence_csv = tmp_path / "source_evidence_summary.csv"
    evidence_report = tmp_path / "source_evidence_summary.md"
    dealer_memo = tmp_path / "dealer_bridge_integration_memo.md"
    matrix = tmp_path / "matrix.csv"
    report = tmp_path / "design_report.md"

    rows = build_evidence_rows(imported_root=imported_root)
    write_evidence_summary_csv(rows, evidence_csv)
    reread_rows = read_evidence_summary(evidence_csv)
    write_evidence_summary_report(rows, evidence_report)
    write_dealer_bridge_memo(rows, dealer_memo)
    write_mechanism_matrix(matrix)
    write_design_report(matrix, report, evidence_summary_path=evidence_csv)

    text = report.read_text(encoding="utf-8")
    evidence_text = evidence_report.read_text(encoding="utf-8")
    dealer_text = dealer_memo.read_text(encoding="utf-8")
    assert len(rows) == 5
    assert reread_rows[0]["context_note"]
    assert "Source-backed status notes" in text
    assert "source association; navigation only" in text
    assert "does not provide clean timing validation" in text
    assert "strongest near-term promotion" not in text
    assert "qrawatch dealer panel" in evidence_text
    assert "not final holder absorption" in evidence_text
    assert "Do not infer customer identity" in dealer_text
    assert "Bankcap limits this to H.8 mechanism context" in evidence_text
    for generated in (matrix, report, evidence_report, dealer_memo, evidence_csv):
        assert not re.search(
            r"\b(?:partial\s+)?go\b|deserves promotion|go_no_go_recommendation|strongest near-term promotion",
            generated.read_text(), re.IGNORECASE,
        ), generated.name


def _pin_fixture_contracts(imported_root, monkeypatch):
    """Use declared hashes of synthetic fixtures, never claim they are production evidence."""
    contracts = load_source_contracts()
    for artifact in contracts["contracts"]["bidbridge"]["artifacts"]:
        path = imported_root / Path(artifact["destination"]).relative_to("data/imported")
        artifact["schema"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(evidence, "load_source_contracts", lambda: contracts)


@pytest.mark.parametrize("defect", ["missing_headline", "duplicate_headline", "missing_boundary", "unrelated_boundary", "blank_boundary", "nonfinite"])
def test_dealer_evidence_never_falls_back_to_lp_or_promotes_invalid_rows(tmp_path, monkeypatch, defect):
    imported = tmp_path / "imported"
    _write_minimal_imports(imported)
    path = imported / "bidbridge/bidbridge_promotion_summary.csv"
    lines = path.read_text().splitlines()
    if defect == "missing_headline":
        lines = [line for line in lines if not line.startswith("maturity_bucket_fe_monday,")]
    elif defect == "duplicate_headline":
        lines.append(next(line for line in lines if line.startswith("maturity_bucket_fe_monday,")))
    elif defect == "missing_boundary":
        lines = [line for line in lines if not line.startswith("lp_placebo_boundary,")]
    elif defect == "unrelated_boundary":
        lines = [line.replace("lp_placebo_boundary,", "unrelated_boundary,") for line in lines]
    elif defect == "blank_boundary":
        lines = [line.replace("LP does not provide clean timing validation.", "   ") for line in lines]
    else:
        lines = [line.replace(",9.45,", ",nan,") for line in lines]
    path.write_text("\n".join(lines))
    _pin_fixture_contracts(imported, monkeypatch)
    rows = build_evidence_rows(imported)
    assert rows[0]["status"] in {"invalid", "unavailable"}
    assert "7.23" not in rows[0]["evidence_note"]
    assert "9.45" not in rows[0]["evidence_note"]
    if defect in {"unrelated_boundary", "blank_boundary"}:
        assert rows[0]["status"] == "unavailable"
    memo = tmp_path / "memo.md"
    write_dealer_bridge_memo(rows, memo)
    assert "first promoted" not in memo.read_text()


def test_stale_import_is_rejected_before_rendering_estimate(tmp_path, monkeypatch):
    imported = tmp_path / "imported"
    _write_minimal_imports(imported)
    _pin_fixture_contracts(imported, monkeypatch)
    path = imported / "bidbridge/bidbridge_promotion_summary.csv"
    path.write_text(path.read_text().replace(",9.45,", ",10.61,"))
    checks = validate_imported_artifacts(imported, {"bidbridge"})
    assert any(check.failed and "sha256 mismatch" in check.details for check in checks)
    row = build_evidence_rows(imported)[0]
    assert row["status"] == "invalid"
    assert "10.61" not in row["evidence_note"]


def test_missing_import_does_not_promote_dealer_lane(tmp_path):
    row = build_evidence_rows(tmp_path)[0]
    assert row["status"] == "missing"
    memo = tmp_path / "memo.md"
    write_dealer_bridge_memo([row], memo)
    assert "first promoted" not in memo.read_text()


def test_cached_summary_is_rejected_when_source_status_changes(tmp_path, monkeypatch):
    from regcap import validation
    from regcap.config import ConfigError

    imported = tmp_path / "data/imported"
    _write_minimal_imports(imported)
    _pin_fixture_contracts(imported, monkeypatch)
    rows = build_evidence_rows(imported)
    rows[0]["status"] = "strongest near-term promotion"
    write_evidence_summary_csv(rows, tmp_path / "output/tables/source_evidence_summary.csv")
    monkeypatch.setattr(validation, "PROJECT_ROOT", tmp_path)
    with pytest.raises(ConfigError, match="stale relative"):
        validation.validate_package()


@pytest.mark.parametrize("filename,target,mechanism_id", [
    ("constraint_decomposition_regime_summary.csv", "duration_loss_window", "duration_loss_aoci_htm"),
    ("event_2020_did_results.csv", "ust_inventory_fv_scaled", "slr_leverage_capacity"),
])
def test_missing_nondealer_target_rows_are_unavailable(tmp_path, monkeypatch, filename, target, mechanism_id):
    imported = tmp_path / "imported"
    _write_minimal_imports(imported)
    path = imported / "slrwatch" / filename
    path.write_text(path.read_text().replace(target, "unrelated_target"))
    _pin_fixture_contracts(imported, monkeypatch)
    row = next(row for row in build_evidence_rows(imported) if row["mechanism_id"] == mechanism_id)
    assert row["status"] == "unavailable"
    assert not re.search(r"\d", row["evidence_note"])
    assert row["context_note"] == ""


def test_missing_qra_flag_field_fails_schema_and_does_not_imply_zero_flags(tmp_path, monkeypatch):
    imported = tmp_path / "imported"
    _write_minimal_imports(imported)
    path = imported / "qrawatch/qra_event_shock_summary.csv"
    path.write_text(path.read_text().replace(",usable_for_headline,", ",").replace(",True,", ","))
    _pin_fixture_contracts(imported, monkeypatch)
    checks = validate_imported_artifacts(imported, {"qrawatch"})
    check = next(check for check in checks if check.destination == path)
    assert check.failed
    assert "missing columns: ['usable_for_headline']" == check.details
    context = build_evidence_rows(imported)[0]["context_note"]
    assert "flags are unavailable" in context
    assert "usable_for_headline=True flags" not in context
    assert "descriptive-only rows" not in context
