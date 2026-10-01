# Processing and phase extension checkpoint

This checkpoint contains the completed source-audited extension of the
Curie-temperature screening study, together with conservative model-eligibility
flags and post hoc grouped sensitivity analyses.

## Files

- `processing_phase_annotation_seed.csv`: the original 141-record
  composition-only table with a conservative annotation scaffold.
- `processing_phase_annotation_state_aware.csv`: a state-preserving table built
  before process-aware modelling. It retains distinct composition/state/TC
  records that can be collapsed by composition-only deduplication.
- `publication_annotation_audit.csv`: publication-level coverage audit.
- `fulltext_source_index.csv`: sanitized identity and coverage audit for the
  privately held source-PDF corpus. It contains no local paths or extracted
  article text. A PDF is accepted as matched only when its manifest DOI is
  found in the extracted full text.
- `verified_publication_annotations.csv`: manually checked publication-level
  process/phase ledger, including the scope and mapping status of each label.
- `verified_annotation_coverage.csv`: category counts and descriptive TC
  ranges for the verified portion of the state-aware table. These summaries
  are diagnostic only and are not causal estimates.
- `target_semantics_audit.csv`: publication-level holdout ledger for values
  whose target meaning, numerical value, primary-source lineage, or material
  state remains unresolved.
- `model_sensitivity/`: grouped LightGBM results for the target-verified and
  stricter process/phase-eligible cohorts.
- `process_phase_model/`: paired comparison of composition-only,
  process/phase-only, and combined feature sets on the same 102 records.

## Verification rule

Title-derived categories are marked `candidate_only` and
`full_text_required`. They must not be used as confirmed model inputs.

The uploaded `makale_42.zip` corpus was indexed on 30 September 2026. All 42
manifest entries have a corresponding PDF, all 42 yielded machine-readable
text, and the expected DOI was found in all 42 PDFs. This closes the source-
availability gap. Candidate passages were checked in context before a
publication or record was marked verified; copyrighted article text is not
redistributed in this package.

All 42 publications and all 141 unique records are represented in the ledger.
The conservative eligibility partition is 102 model-eligible records, 31 held
out for target review, and 8 held out for unresolved process/phase/state
mapping. No target-review or unverified record is admitted to the extension.

The post hoc grouped sensitivity analysis found that composition-only OOF R²
fell from 0.607 in the original 141-record cohort to 0.420 in the 110-record
target-verified cohort and 0.205 in the 102-record process/phase-eligible
cohort. On those same 102 records and folds, adding the audited categorical
fields increased OOF R² to 0.453 and reduced MAE from 77.4 to 65.4 K. The
process/phase-only model was not predictive (R² = -0.057), showing that these
fields complement rather than replace composition.

Run `python scripts/verify_processing_phase_extension.py` from the repository
root to check coverage, exclusion safety, fixed model results, and the paired
publication-cluster bootstrap direction.
