from regcap.mechanisms import MATRIX_COLUMNS, mechanism_matrix_rows


def test_mechanism_matrix_has_required_columns_and_priority_order():
    rows = mechanism_matrix_rows()

    assert len(rows) == 5
    assert list(rows[0]) == MATRIX_COLUMNS
    assert rows[0]["mechanism_id"] == "dealer_repo_bridge"
    assert rows[-1]["mechanism_id"] == "gsib_window_dressing"


def test_matrix_keeps_required_claim_boundaries():
    rows = {row["mechanism_id"]: row for row in mechanism_matrix_rows()}

    assert "final domestic absorption" in rows["dealer_repo_bridge"]["claim_boundary_unsafe"]
    assert "cautionary" in rows["slr_leverage_capacity"]["claim_boundary_safe"]
    assert "TDC deposit residual" in rows["duration_loss_aoci_htm"]["claim_boundary_unsafe"]
