# Data corrections and provenance audit

## Version 1.0.1 — 2026-09-29

This release corrects provenance metadata and documents two legacy extraction issues. It does not alter the numerical analysis matrix or any reported model result.

### Corrected source-workbook field alignment

The legacy spreadsheet row corresponding to public `source_row=39` contained eight comma-separated values instead of the nine declared fields. The missing value was `RC=0`, so the remaining classical descriptors appeared one position to the left in that workbook. The public raw CSV already contained the intended aligned values:

`TC=44`, `H=2`, `dS=4.6`, `RC=0`, `dX=0.2734054704`, `VEC=4.22`, `sigma=13.9108345209`, `dHmix=-33.592`, and `dSmix=13.6019358217`.

After inserting the missing zero in the legacy workbook, all nine original numerical fields match the public raw CSV for all 199 records within floating-point precision.

### Corrected nominal-composition labels

Source-table verification of reference `[33]` showed that repeated `H=2 T`, `dS=0.35 J kg-1 K-1` records had been assigned nominal-composition strings by queue order. The descriptor–target rows were already correct. Only the formula labels were changed:

| Source row | TC (K) | Previous label | Corrected label |
|---:|---:|---|---|
| 141 | 171 | FeCoNiCr | Fe25.64Co25.64Ni25.64Cr23.08 |
| 143 | 100 | Fe25.3Co25.3Ni25.3Cr24.1 | FeCoNiCr |
| 144 | 131 | Fe25.64Co25.64Ni25.64Cr23.08 | Fe25.3Co25.3Ni25.3Cr24.1 |

`composition` is not a model feature and is not part of the deduplication key. Consequently, this correction does not change the 199/141 row counts, publication-grouped folds, regression metrics, target-window rules, SHAP values, or figures.

### Repeated-series common point

Rows 60 and 66 represent the same nominal common composition as written in two intersecting composition series in reference `[13]`. Their retained `TC` values are 271.0 and 271.3 K. The 0.3 K difference is consistent with legacy graphical reading or rounding. Both records are retained to preserve the original extraction; no exact equality or deletion is imposed retrospectively. This note prevents the pair from being mistaken for two distinct nominal chemistries.

### Meaning of the ambiguity flag

`composition_match_ambiguous_within_reference=True` records that more than one formula in the same publication shared the same rounded `H`–`dS` key during later formula reconstruction. It is an algorithmic traceability flag, not evidence that `TC` or the numerical descriptors are wrong. Resolved and retained cases are listed in `data/processed/development_curation_audit.csv`.
