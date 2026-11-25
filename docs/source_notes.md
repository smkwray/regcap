# Source Notes

`regcap` integrates compact public artifacts from sibling projects and keeps each source project's stated limits.

## Source roles

`slrwatch` supplies SLR/leverage-capacity context and the broader constraint-decomposition lane. Its current 2020 SLR event evidence is cautionary rather than a robust positive Treasury-absorption result.

`bankcap` supplies the H.8 bank-group mechanism screen. H.8 evidence is useful for mechanism context and research-priority decisions, but it is not bank-level evidence.

`bidbridge` supplies a conditional dealer-warehousing association. The pinned v5 source uses supply-only maturity-bucket and week fixed effects. Its supporting binary high-supply LP fails clean timing diagnostics; neither QT amplification nor final holder absorption is established.

`qrawatch` supplies issuance composition, duration-supply, QRA, and primary-dealer context. Its role here is supporting context, especially for duration-heavy supply and refunding windows.

`rowflow` covers foreign absorption and is used for contrast only; `regcap` covers domestic capacity.

## Source contract

The source contract in `config/source_contracts.yml` points only to compact reports, tables, summaries, and manifests. It intentionally avoids raw Call Report, FR Y-9C, FR Y-15, dealer, or auction ingestion.

Generated imports are copied into ignored `data/imported/` paths. The copy operation is one-way into `regcap`; it never writes to sibling repositories.

The second layer validates copied artifact shape and configured content hashes against `config/source_contracts.yml`, then writes a compact source-evidence summary from those imported outputs. The summary is still public-safe mechanism status, not a raw-data reconstruction or a stronger causal claim.
