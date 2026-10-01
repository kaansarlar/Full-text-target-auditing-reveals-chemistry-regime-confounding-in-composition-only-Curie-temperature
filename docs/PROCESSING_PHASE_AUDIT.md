# Processing, phase, and target-semantics audit

## Status

All 42 development publications were checked against the uploaded full texts. The publication ledger covers all 141 unique development records. Record-level use remains deliberately conservative:

| Record status | Unique records |
|---|---:|
| Target verified and process/phase mapping resolved | 102 |
| Excluded pending target-semantics/value review | 31 |
| Excluded pending process/phase/state mapping | 8 |
| Total | 141 |

The corresponding state-aware table has 145 rows, of which 105 across 34 publications are currently eligible for a process/phase extension.

## Target issues found

| Reference | Audit status | Reason for holdout |
|---|---|---|
| [20] | Target semantics | The dataset's 295 K value is the reported maximum of magnetic entropy change, not an explicitly established Curie temperature; the source separately discusses a blocking temperature near 325 K. |
| [21] | Value conflict | The abstract reports 297 K while the main text gives approximately 280 K; reference [12] reports 329 K for the same nominal composition. |
| [33] | Secondary-source traceback | The review table aggregates 18 records from primary publications. Their original processing state, phase, and target definition cannot be assigned from the review alone. |
| [35] | Multiple transitions/value conflict | Al-containing samples have multiple magnetic transitions. The dataset includes a 685 K value that does not match the source table's 640/905 K pair for the corresponding composition. |
| [40] | State assignment | The source plots separate as-rolled and 900 °C-annealed Curie-temperature series, but the dataset values do not unambiguously identify the transcribed state. |
| [41] | Target semantics | The 290 and 150 K values are entropy-peak/transition-feature temperatures and are not uniformly demonstrated as Curie temperatures. |

These flags do not retroactively alter the reported 141-record manuscript analysis. They define two post hoc sensitivity cohorts and prevent ambiguous records from silently entering the process-aware model.

## Publication-grouped sensitivity results

The original LightGBM protocol was rerun without changing its nested grouped cross-validation or tuning budget.

| Cohort | Records | Publications | OOF R² | RMSE (K) | MAE (K) |
|---|---:|---:|---:|---:|---:|
| Original manuscript cohort | 141 | 42 | 0.607 | 93.6 | 57.7 |
| Target meaning verified | 110 | 36 | 0.420 | 112.7 | 67.8 |
| Target + process/phase mapping resolved | 102 | 34 | 0.205 | 130.5 | 77.4 |

The across-cohort decline must not be interpreted as a causal effect of cleaning: the publication and chemistry distribution changes when sources are held out. It is evidence that the original performance is sensitive to source composition and target-definition heterogeneity.

## Process-aware comparison on the same 102 records

| Features | OOF R² | RMSE (K) | MAE (K) |
|---|---:|---:|---:|
| Composition descriptors only | 0.205 | 130.5 | 77.4 |
| Process/phase categories only | −0.057 | 150.4 | 103.8 |
| Composition + process/phase | 0.453 | 108.2 | 65.4 |

On the identical records and outer publication folds, adding the audited process, thermal-state, phase, and product-form fields increased OOF R² by 0.248 and reduced MAE by 12.0 K. A 10,000-resample publication-cluster bootstrap of the fixed paired OOF errors gave:

- ΔR² = +0.248, 95% interval +0.058 to +0.585;
- ΔRMSE = −22.3 K, 95% interval −36.0 to −6.5 K;
- ΔMAE = −12.0 K, 95% interval −23.5 to −0.8 K.

The combined model reduced absolute error for 70 of 102 records and for 23 of 34 publication groups. These intervals quantify the paired OOF error contrast; they do not include uncertainty from repeating the entire literature-selection and annotation process.

## Interpretation for a revised manuscript

The defensible new result is not that process metadata alone predicts Curie temperature. It does not. The result is that:

1. literature-derived `TC` tables contain target-definition and state-assignment heterogeneity that composition-only curation does not expose;
2. conservative full-text auditing makes the composition-only model less stable across publications;
3. on the same audited cohort, process/phase metadata recovers a substantial part of the lost generalization, while remaining insufficient without composition.

This supports a stronger framing: **publication-grouped validation and target-definition-aware process annotation jointly expose why composition-only screening overstates transferability.** The analysis is post hoc and should be presented as an extension/sensitivity study, not as a preregistered primary endpoint.

## Reproducibility route

```bash
python scripts/build_verified_publication_annotations.py
python scripts/build_processing_phase_annotation.py
python scripts/run_target_semantics_sensitivity.py --n-jobs 4
python scripts/run_process_phase_extension.py --n-jobs 4
python scripts/verify_processing_phase_extension.py
```

Key outputs are under `results/processing_phase_extension/`, including the publication ledger, row-level annotations, target audit, cohort exclusions, OOF predictions, split audits, paired errors, and publication-cluster bootstrap summary.
