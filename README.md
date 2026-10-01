# Target-audited, process-aware validation of Curie-temperature screening

This repository contains the public reproducibility package for the manuscript:

> **Full-text target auditing and process-aware validation expose the limits of composition-only Curie-temperature screening in magnetocaloric high-entropy alloys**

The repository is intentionally compact. It contains the analysis-ready data, publication-group assignments, source manifests, executable analysis code, principal numerical outputs, and final figures required to audit or reproduce the reported results. Manuscript drafts, downloaded source articles, duplicate workbooks, and exploratory files that do not support a reported result are deliberately excluded.

## Version 1.0.1 metadata correction

Version 1.0.1 corrects three nominal-composition labels in source rows 141, 143, and 144 after verification against the source table. The associated `TC` values, all descriptors, publication assignments, deduplication, model inputs, predictions, figures, and reported metrics are unchanged. The full audit is in `docs/DATA_CORRECTIONS.md` and `data/processed/development_curation_audit.csv`.

## Version 1.1.0 target and process audit

Version 1.1.0 adds a full-text audit of all 42 development sources, a conservative target-semantics partition, record-level processing/phase annotations, and a paired publication-grouped comparison of composition-only, process/phase-only, and combined feature sets. The original 141-record analysis is retained unchanged.

## Quick verification

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/run_pipeline.py --mode verify
python scripts/verify_processing_phase_extension.py
```

These fast verification paths normally complete in seconds. They check dataset sizes, publication groups and their size distribution, descriptor–target deduplication, held-out publication coverage, headline regression metrics, development-window metrics, nested rule-selection results, historical and targeted literature outcomes, the v1.0.1 metadata corrections, the full-text audit partition, process-aware paired results, cluster-bootstrap direction, source manifests, figure availability, and the absence of redistributed source-article PDFs.

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

## Headline values

- Publication-grouped HEA-descriptor LightGBM: OOF R² = 0.607, RMSE = 93.6 K, MAE = 57.7 K.
- Target-verified composition-only sensitivity cohort: 110 records from 36 publications, OOF R² = 0.420.
- Identical 102-record audited cohort: composition-only R² = 0.205; composition plus process/phase R² = 0.453 and MAE decreases from 77.4 to 65.4 K.
- Paired publication-cluster bootstrap: ΔR² = +0.248 (95% interval +0.058 to +0.585) and ΔMAE = −12.0 K (−23.5 to −0.8 K).
- Repeated nested F1-first rule selection: balanced accuracy = 0.694 ± 0.039 and MCC = 0.374 ± 0.075.
- Historical 32-record fixed-family audit: balanced accuracy = 0.860; within the Mn-based family, balanced accuracy = 0.563 and enrichment = 1.07×.
- Full-development candidate in the 13-record primary challenge: TP/TN/FP/FN = 8/0/4/1, balanced accuracy = 0.444, MCC = −0.192.
- Same nominal Ag-containing composition: reported Tc changes from 209 K in the as-rolled state to 295 K after annealing.

## Source articles and copyright

Copyrighted article PDFs are not redistributed. Each literature-derived record is traceable through the DOI-bearing source manifests in `references/`. See `LICENSE.md` for the repository's split code/data licensing and third-party-material exception.

## Citation

Please cite the associated manuscript and the exact archived release used for the process-aware extension:

> Şarlar K 2026 *Target-audited, process-aware validation of Curie-temperature screening*, version v1.1.0 (Zenodo), doi: [10.5281/zenodo.23082961](https://doi.org/10.5281/zenodo.23082961)

The all-versions DOI `10.5281/zenodo.22901861` always resolves to the latest archived version.

Start with `docs/REVIEWER_GUIDE.md` for a short audit route and `docs/ANALYSIS_MAP.md` for exact table/figure provenance.
