[README.md](https://github.com/user-attachments/files/32981557/README.md)
# Full-text target auditing of Curie-temperature screening

This repository contains the public reproducibility package for the manuscript:

> **Full-text target auditing reveals chemistry-regime confounding in composition-only Curie-temperature screening of magnetocaloric high-entropy alloys**

The repository is intentionally compact. It contains the analysis-ready data, publication-group assignments, source manifests, executable analysis code, principal numerical outputs, and final figures required to audit or reproduce the reported results. Manuscript drafts, downloaded source articles, duplicate workbooks, and exploratory files that do not support a reported result are deliberately excluded.

## Version 1.0.1 metadata correction

Version 1.0.1 corrects three nominal-composition labels in source rows 141, 143, and 144 after verification against the source table. The associated `TC` values, all descriptors, publication assignments, deduplication, model inputs, predictions, figures, and reported metrics are unchanged. The full audit is in `docs/DATA_CORRECTIONS.md` and `data/processed/development_curation_audit.csv`.

## Version 1.1.0 target and process audit

Version 1.1.0 adds a full-text audit of all 42 development sources, a conservative target-semantics partition, record-level processing/phase annotations, and a paired publication-grouped comparison of composition-only, process/phase-only, and combined feature sets. The original 141-record analysis is retained unchanged.

## Version 1.2.0 strict-TC and chemistry-regime audit

Version 1.2.0 applies a record-level full-text target audit to all 141 unique development rows. It retains 79 directly reported experimental Curie-temperature records from 26 publications, documents 62 exclusions by reason, corrects two transcription errors against the primary sources, and assigns three prespecified chemistry families. The rare-earth-rich family requires a combined nominal rare-earth fraction of at least 50 at.%; minor rare-earth additions therefore remain in their non-rare-earth chemistry family. The release adds equal-budget grouped model comparison, repeated grouped partitions, within-family and leave-one-family-out tests, a direct target-window classifier, and a strict-cohort process/phase sensitivity analysis. These analyses show that apparently useful pooled performance is substantially explained by chemistry-regime separation and does not transfer within or across families.

## Quick verification

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/run_pipeline.py --mode verify
python scripts/verify_processing_phase_extension.py
python scripts/verify_strict_tc_extension.py
```

These fast verification paths normally complete in seconds. They check dataset sizes, publication groups and their size distribution, descriptor–target deduplication, held-out publication coverage, headline regression metrics, development-window metrics, nested rule-selection results, historical and targeted literature outcomes, the v1.0.1 metadata corrections, the strict full-text audit partition, chemistry-family analyses, direct classification, strict-cohort process/phase sensitivity, source manifests, figure availability, and the absence of redistributed source-article PDFs.

The generated report is written to `docs/VERIFICATION_REPORT.json`.

## Full computational rerun

```bash
python scripts/run_pipeline.py --mode full --n-jobs 4
```

This reruns publication-grouped nested model selection, full-data TreeSHAP interpretation, development-window rules, the historical audit, repeated nested target-window rule selection, external-rule metrics, and Figures 2–7. New files are written under `reproduced/`; supplied reference outputs under `results/` are not overwritten. Runtime is hardware-dependent and may be tens of minutes or longer.

To regenerate only the deterministic window and rule figures:

```bash
python scripts/run_pipeline.py --mode figures
```

## Repository contents

| Path | Contents |
|---|---|
| `data/raw/` | Original 199-record numerical table and the record-random comparison used in the validation-design figure |
| `data/processed/` | 199-row provenance table, 141-row analysis table, 32-record historical audit, 26-row five-paper challenge table, and processing-state sensitivity pairs |
| `references/` | DOI-bearing source manifests for all analysis cohorts and the original package bibliography |
| `scripts/` | Verification, grouped regression, TreeSHAP, rule selection, external evaluation, full-text audit assembly, process-aware modelling, and figure-generation code |
| `results/` | Supplied numerical outputs needed to audit the manuscript claims |
| `figures/` | Final manuscript Figures 1–8 |
| `docs/` | Data dictionary, claim-to-file map, reviewer guide, reproducibility notes, verification report, and checksums |

## Data cohorts

- **Development data:** 199 literature measurement records mapped to 42 publication sources and consolidated to 141 unique descriptor–Tc rows using eleven composition descriptors plus Tc as the deduplication key.
- **Historical audit:** 32 records absent from the 141-row development table: 14 experimental HEA/MEA/CCA controls, 15 ordered Mn–Ni–Si-based out-of-domain stress records, and 3 simulation sensitivity records.
- **Targeted five-paper challenge:** 26 rows retaining primary states, alternate processing states, transition-ambiguity cases, and an exclusion log. The primary classification analysis uses 13 rows. Because target relevance influenced retrieval, this cohort is a stress test rather than a population-level external validation set.

## Processing, phase, and target-semantics audit

The 42 development-source articles were checked at full-text level for synthesis route, thermal state, product form, phase constitution, and the meaning of the reported target temperature. Conservative record-level rules yield 102 model-eligible unique records across 34 publications. Thirty-one records from six publications are held out pending target review, and eight further records lack an unambiguous record-level process/phase mapping. No flagged or unverified record enters the process-aware model.

The audit trail is in `results/processing_phase_extension/target_semantics_audit.csv` and `publication_annotation_audit.csv`; the full method and file map are in `docs/PROCESSING_PHASE_AUDIT.md`.

## Strict experimental Curie-temperature cohort

The v1.2.0 full-text audit retains 79 directly reported experimental Curie temperatures from 26 publications. The 62 excluded rows comprise 21 Néel temperatures, 18 secondary-source-only values, 7 proxy temperatures, 7 state-ambiguous values, 6 other non-Curie transitions, and 3 conflicting assignments. The strict cohort contains 32 3d-transition-metal, 25 rare-earth-rich, and 22 transition-metal–metalloid records. Family membership explains 60.5% of total target variance.

All decisions and corrected values are in `results/strict_tc_audit/strict_tc_record_audit.csv`; the retained table is `strict_experimental_tc_79.csv`.

## Headline values

- Publication-grouped HEA-descriptor LightGBM: OOF R² = 0.607, RMSE = 93.6 K, MAE = 57.7 K.
- Strict 79-record equal-budget grouped comparison: SVR is best, with OOF R² = 0.610, RMSE = 101.2 K, and MAE = 66.3 K.
- Across five repeated grouped partitions, SVR gives R² = 0.468 ± 0.126; a family-mean baseline gives R² = 0.505 ± 0.004.
- Within-family R² values are 0.198 (3d-TM), −1.791 (RE-rich), and −0.297 (TM-metalloid); every leave-one-family-out R² is negative.
- Direct grouped logistic classification of the 250–350 K window gives balanced accuracy = 0.726, MCC = 0.433, and enrichment = 1.59×.
- On the strict 71-record/24-publication process cohort, adding process/phase fields changes R² from 0.305 to 0.328; the paired cluster-bootstrap interval crosses zero (ΔR² 95% interval −0.083 to +0.093).
- Repeated nested F1-first rule selection: balanced accuracy = 0.694 ± 0.039 and MCC = 0.374 ± 0.075.
- Historical 32-record fixed-family audit: balanced accuracy = 0.860; within the Mn-based family, balanced accuracy = 0.563 and enrichment = 1.07×.
- Full-development candidate in the 13-record primary challenge: TP/TN/FP/FN = 8/0/4/1, balanced accuracy = 0.444, MCC = −0.192.
- Same nominal Ag-containing composition: reported Tc changes from 209 K in the as-rolled state to 295 K after annealing.

## Source articles and copyright

Copyrighted article PDFs are not redistributed. Each literature-derived record is traceable through the DOI-bearing source manifests in `references/`. See `LICENSE.md` for the repository's split code/data licensing and third-party-material exception.

## Citation

Please cite the associated manuscript and the archived release:

> Şarlar K 2026 *Full-text target auditing reveals chemistry-regime confounding in composition-only Curie-temperature screening*, version v1.2.0 (Zenodo), doi: [10.5281/zenodo.23102726](https://doi.org/10.5281/zenodo.23102726)

The all-versions DOI `10.5281/zenodo.22901861` always resolves to the latest archived version.

Start with `docs/REVIEWER_GUIDE.md` for a short audit route and `docs/ANALYSIS_MAP.md` for exact table/figure provenance.
