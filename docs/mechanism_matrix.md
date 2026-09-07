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
- `research_priority_note`
- `implementation_priority`

First-pass prioritization:

1. Dealer leverage / repo intermediation constraints
2. Duration-loss / AOCI / HTM pressure
3. SLR / leverage capacity
4. LCR / HQLA demand
5. G-SIB surcharge / reporting-date window dressing

This ordering is a configured research priority, not an evidence ranking. The source-evidence summary must separately show valid inputs, a recognized headline, and the producer's diagnostic limits. Duration-loss and SLR mechanisms remain hypotheses or guarded context.

The navigation memo lives at `output/reports/dealer_bridge_integration_memo.md` when generated. It neither promotes a mechanism nor independently establishes a dealer association. Final holder location remains outside `regcap`.
