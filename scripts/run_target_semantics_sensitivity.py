#!/usr/bin/env python3
"""Re-run grouped LightGBM after conservative full-text audit exclusions.

This script does not overwrite the manuscript's original 141-record result.
It compares that fixed baseline with two explicitly post hoc sensitivity
cohorts: records whose target meaning is source-verified, and the stricter
subset that is also eligible for the processing/phase extension.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

from publication_grouped_analysis import FEATURE_SETS, model_specs, run_model


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "development_unique_141.csv"
ANNOTATION = ROOT / "results" / "processing_phase_extension" / "processing_phase_annotation_seed.csv"
BASELINE = ROOT / "results" / "grouped_cv" / "publication_grouped_model_summary.csv"
DEFAULT_OUT = ROOT / "results" / "processing_phase_extension" / "model_sensitivity"


def load_and_validate() -> tuple[pd.DataFrame, pd.DataFrame]:
    data = pd.read_csv(DATA).reset_index(drop=True)
    annotation = pd.read_csv(ANNOTATION).reset_index(drop=True)
    keys = ["source_row", "composition", "reference_id", "TC"]
    if len(data) != len(annotation) or not data[keys].equals(annotation[keys]):
        raise RuntimeError("Annotation table is not row-aligned with development_unique_141.csv")
    return data, annotation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--candidate-budget", type=int, default=60)
    parser.add_argument("--n-jobs", type=int, default=max(1, min(8, os.cpu_count() or 1)))
    args = parser.parse_args()

    data, annotation = load_and_validate()
    cohorts = {
        "target_verified": annotation["target_audit_status"].eq("verified_as_reported"),
        "process_phase_eligible": annotation["model_eligibility"].eq("eligible_process_phase_extension"),
    }
    spec = model_specs()["LightGBM"]
    rows = []
    excluded_rows = []

    baseline = pd.read_csv(BASELINE)
    baseline = baseline.loc[
        baseline["feature_set"].eq("hea") & baseline["model"].eq("LightGBM")
    ].iloc[0]
    rows.append({
        "cohort": "original_141",
        "selection_basis": "preregistered manuscript analysis table; no post-hoc audit exclusion",
        "n_records": int(baseline.n_records),
        "n_references": int(baseline.n_references),
        "oof_r2": float(baseline.oof_r2),
        "oof_rmse": float(baseline.oof_rmse),
        "oof_mae": float(baseline.oof_mae),
        "fold_r2_mean": float(baseline.fold_r2_mean),
        "fold_r2_sd": float(baseline.fold_r2_sd),
    })

    for cohort, mask in cohorts.items():
        subset = data.loc[mask].reset_index(drop=True)
        cohort_dir = args.output_dir / cohort
        cohort_dir.mkdir(parents=True, exist_ok=True)
        result = run_model(
            subset,
            FEATURE_SETS["hea"],
            "hea",
            "LightGBM",
            spec,
            cohort_dir,
            args.candidate_budget,
            args.n_jobs,
        )
        summary = result[0]
        rows.append({
            "cohort": cohort,
            "selection_basis": (
                "full-text target meaning verified"
                if cohort == "target_verified"
                else "target verified and record-level process/phase mapping resolved"
            ),
            **{k: summary[k] for k in [
                "n_records", "n_references", "oof_r2", "oof_rmse", "oof_mae",
                "fold_r2_mean", "fold_r2_sd",
            ]},
        })
        excluded = annotation.loc[~mask, [
            "annotation_record_id", "source_row", "composition", "reference_id", "TC",
            "publication_mapping_status", "target_audit_status", "target_audit_note",
            "model_eligibility", "review_notes",
        ]].copy()
        excluded.insert(0, "cohort", cohort)
        excluded_rows.append(excluded)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    comparison = pd.DataFrame(rows)
    comparison["delta_oof_r2_vs_original"] = comparison["oof_r2"] - comparison.loc[0, "oof_r2"]
    comparison["delta_oof_mae_K_vs_original"] = comparison["oof_mae"] - comparison.loc[0, "oof_mae"]
    comparison.to_csv(args.output_dir / "cohort_comparison.csv", index=False)
    pd.concat(excluded_rows, ignore_index=True).to_csv(
        args.output_dir / "cohort_exclusions.csv", index=False
    )
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
