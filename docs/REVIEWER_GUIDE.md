# Reviewer guide

## Five-minute audit

1. Run `python scripts/run_pipeline.py --mode verify`.
2. Run `python scripts/verify_processing_phase_extension.py`.
3. Run `python scripts/verify_strict_tc_extension.py`.
4. Inspect `docs/VERIFICATION_REPORT.json`; every package check should report `PASS`.
5. Open `results/strict_tc_audit/strict_tc_record_audit.csv` for every v1.2.0 target decision and correction.
6. Open `results/strict_tc_grouped_cv/summary__strict_hea__SVR.csv`, `results/strict_tc_robustness/`, and `results/strict_tc_classification/direct_classifier_summary.csv` for the principal strict-cohort results.
7. Open `results/strict_tc_process_phase/process_phase_model_comparison.csv` and `paired_cluster_bootstrap.csv` for the identical-cohort process-aware sensitivity.
8. Open `docs/DATA_CORRECTIONS.md` and `data/processed/development_curation_audit.csv` for the retained v1.0.1 metadata audit.

## Claim-to-file shortcuts

| Claim | Primary evidence |
|---|---|
| 199 measurements → 141 unique descriptor–Tc rows from 42 publications | `data/processed/development_full_199.csv`, `development_unique_141.csv` |
| No publication appears in both training and test portions of an outer fold | `results/grouped_cv/splits__hea__LightGBM.csv` and `publication_grouped_split_audit.csv` |
| OOF R²/MAE/RMSE of the best model | `results/grouped_cv/publication_grouped_model_summary.csv` |
| Global TreeSHAP ranking | `results/interpretation/HEA_TreeSHAP_importance.csv` |
| Instability and performance of nested rule selection | `results/rule_reassessment/shap_rank_stability.csv`, `nested_rule_comparison_summary.csv`, `outer_fold_rule_selections.csv` |
| Chemistry-family confounding in the historical audit | `data/processed/historical_audit_32.csv`, `results/rule_reassessment/external_v1_v2_metrics.csv` |
| Five-paper stress-test outcome | `data/processed/targeted_challenge_26.csv`, `results/rule_reassessment/external_v1_v2_metrics.csv` |
| Processing non-identifiability | `data/processed/process_state_sensitivity.csv` |
| Target-audit partition and reasons | `results/processing_phase_extension/target_semantics_audit.csv`, `publication_annotation_audit.csv` |
| Target-verified and strict-cohort sensitivity | `results/processing_phase_extension/model_sensitivity/cohort_comparison.csv` |
| Process/phase contribution on identical records and folds | `results/processing_phase_extension/process_phase_model/process_phase_model_comparison.csv`, `paired_record_errors.csv`, `paired_cluster_bootstrap.csv` |
| Strict experimental Curie-temperature inclusion/exclusion decisions | `results/strict_tc_audit/strict_tc_record_audit.csv`, `strict_tc_exclusion_counts.csv` |
| Chemistry-family composition and variance partition | `results/strict_tc_audit/strict_tc_family_summary.csv`, `results/strict_tc_robustness/family_variance_decomposition.csv` |
| Strict-cohort grouped model comparison | `results/strict_tc_grouped_cv/summary__strict_hea__*.csv` |
| Repeated partitions, within-family, and leave-one-family-out tests | `results/strict_tc_robustness/repeated_partition_metrics.csv`, `within_family_metrics.csv`, `leave_family_out_metrics.csv` |
| Direct 250–350 K classification | `results/strict_tc_classification/direct_classifier_summary.csv` |
| Strict-cohort process/phase sensitivity | `results/strict_tc_process_phase/process_phase_model_comparison.csv`, `paired_cluster_bootstrap.csv` |

## Prespecified limitations

- The 141-row dataset is small and publication-clustered.
- The 32-record audit is a constructed literature set, not a population sample.
- Its target-positive records are concentrated in ordered Mn-based intermetallics rather than unambiguous HEAs.
- The five-paper set was retrieved with target relevance in mind and is therefore reported as a stress test.
- Composition-only descriptors cannot encode annealing, phase fractions, disorder, or multiple transition assignments.
- The process-aware extension is post hoc; sparse categorical levels can remain publication specific, and its bootstrap conditions on the completed manual audit.
- Chemistry families are broad post-audit strata used to diagnose regime confounding, not universal materials classes.
- The strict cohort remains small (79 records across 26 publications), so family-specific and leave-family-out estimates are stress tests rather than production error guarantees.
- The publication-grouped RMSE of 93.6 K is comparable to the 100 K width of the 250–350 K interval; the regression is intended for prioritization, not confident single-composition window assignment.

## Source audit

- `references/development_sources_42.csv` links the 141-row development table to its 42 source references.
- `references/historical_audit_sources.csv` maps all 32 audit rows to the v28 bibliography.
- `references/targeted_challenge_sources.csv` maps the challenge rows to five DOI-bearing papers.
- `references/manuscript_references.md` preserves the bibliography distributed with the original package; the revised manuscript contains 56 cited references.
- `data/processed/development_curation_audit.csv` records the row-level v1.0.1 corrections and retained legacy extraction notes.

The package excludes copyrighted source PDFs; the DOI/source manifests are the audit trail.
