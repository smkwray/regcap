PYTHON ?= $(HOME)/venvs/regcap/bin/python
PIP ?= $(HOME)/venvs/regcap/bin/pip

.PHONY: install test validate imported matrix evidence dealer-memo report package

install:
	python3 -m venv $(HOME)/venvs/regcap
	$(PIP) install -e ".[dev]"

test:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/regcap-pycache $(PYTHON) -B -m pytest

validate:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/regcap-pycache $(PYTHON) -B -m regcap.cli validate-config

imported:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/regcap-pycache $(PYTHON) -B -m regcap.cli validate-imported-artifacts --output output/tables/imported_artifact_quality.csv

matrix:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/regcap-pycache $(PYTHON) -B -m regcap.cli write-mechanism-matrix --output output/tables/regulatory_capacity_mechanism_matrix.csv

evidence:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/regcap-pycache $(PYTHON) -B -m regcap.cli write-evidence-summary --output output/tables/source_evidence_summary.csv --report output/reports/source_evidence_summary.md

dealer-memo:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/regcap-pycache $(PYTHON) -B -m regcap.cli write-dealer-bridge-memo --output output/reports/dealer_bridge_integration_memo.md

report:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/regcap-pycache $(PYTHON) -B -m regcap.cli write-design-report --matrix output/tables/regulatory_capacity_mechanism_matrix.csv --evidence-summary output/tables/source_evidence_summary.csv --output output/reports/regulatory_capacity_design_report.md

package: validate imported matrix evidence dealer-memo report
	PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/regcap-pycache $(PYTHON) -B -m regcap.cli validate-package --strict
