from pathlib import Path

from regcap.reporting import read_matrix, write_design_report, write_manifest, write_mechanism_matrix


def test_write_matrix_and_report(tmp_path: Path):
    matrix = tmp_path / "matrix.csv"
    report = tmp_path / "report.md"

    write_mechanism_matrix(matrix)
    rows = read_matrix(matrix)
    write_design_report(matrix, report)

    assert "research_priority_note" in rows[0]
    assert "Priority note" in report.read_text()
    assert "Recommendation" not in report.read_text()
    assert len(rows) == 5
    assert rows[0]["mechanism_id"] == "dealer_repo_bridge"
    text = report.read_text(encoding="utf-8")
    assert "Do not claim SLR relief robustly caused Treasury absorption" in text
    assert "neither promotes a mechanism nor provides independent empirical authority" in text


def test_manifest_preserves_previous_outputs(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("regcap.reporting.PROJECT_ROOT", tmp_path)
    matrix = tmp_path / "output/tables/test_matrix.csv"
    report = tmp_path / "output/reports/test_report.md"
    manifest = tmp_path / "output/manifests/regcap_manifest.json"
    original = manifest.read_text(encoding="utf-8") if manifest.exists() else None
    try:
        write_manifest(matrix=matrix)
        write_manifest(report=report)
        text = manifest.read_text(encoding="utf-8")

        assert "test_matrix.csv" in text
        assert "test_report.md" in text
    finally:
        if original is None:
            manifest.unlink(missing_ok=True)
        else:
            manifest.write_text(original, encoding="utf-8")
