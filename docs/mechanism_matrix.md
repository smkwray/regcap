# Domestic Capacity Mechanisms for Treasury Absorption

The generated matrix lives at `output/tables/regulatory_capacity_mechanism_matrix.csv`.

The matrix columns are:

- `mechanism_id`
- `mechanism_label`
- `research_function`
- `primary_existing_project`
- `supporting_projects`
- `public_data_sources`
- `frequency`
- `cleanest_estimand`
- `identification_leverage`
- `tdc_connection`
- `claim_boundary_safe`
- `claim_boundary_unsafe`
- `go_no_go_recommendation`
- `implementation_priority`

First-pass prioritization:

1. Dealer leverage / repo intermediation constraints
2. Duration-loss / AOCI / HTM pressure
3. SLR / leverage capacity
4. LCR / HQLA demand
5. G-SIB surcharge / reporting-date window dressing

Dealer/repo is the cleanest near-term implementation lane because existing source evidence is already built around pre-auction supply shocks and short-horizon dealer inventory. Duration-loss/AOCI/HTM is the best research lane for regime dependence, but it needs careful language. SLR remains useful as a mechanism classifier and annex unless later evidence strengthens.

The promoted integration memo lives at `output/reports/dealer_bridge_integration_memo.md` when generated. It should be read as a bridge-design note: dealer warehousing can explain short-run intermediation timing, while final holder location remains outside `regcap` unless another compact source summary supplies it.
