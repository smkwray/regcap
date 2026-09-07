from __future__ import annotations

import json
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
                "maturity_bucket_fe_monday,outputs/tables/panel_fe_results.csv,10.61,$M dealer position per $B announced supply,\"se=4.15, 95% CI [2.48, 18.74]\",headline,Within-week supply maps to dealer positions.",
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


def test_validate_imported_artifacts_checks_contract_schema(tmp_path: Path):
    imported_root = tmp_path / "imported"
    _write_minimal_imports(imported_root)

    checks = validate_imported_artifacts(imported_root=imported_root, projects={"bidbridge"})

    assert len(checks) == 4
    assert not [check for check in checks if check.failed]
    assert any(check.row_count == 2 for check in checks if check.destination.name == "bidbridge_promotion_summary.csv")


def test_optional_qrawatch_and_rowflow_contracts_are_schema_checked(tmp_path: Path):
    imported_root = tmp_path / "imported"
    _write_minimal_imports(imported_root)

    checks = validate_imported_artifacts(imported_root=imported_root, projects={"qrawatch", "rowflow"})

    assert len(checks) == 4
    assert not [check for check in checks if check.failed]


def test_evidence_summary_can_feed_design_report(tmp_path: Path):
    imported_root = tmp_path / "imported"
    _write_minimal_imports(imported_root)
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
    assert "strongest near-term promotion" in text
    assert "qrawatch dealer panel" in evidence_text
    assert "not final holder absorption" in evidence_text
    assert "Do not infer customer identity" in dealer_text
