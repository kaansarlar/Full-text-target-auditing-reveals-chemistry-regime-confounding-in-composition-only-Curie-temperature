#!/usr/bin/env python3
"""Fast integrity checks for the full-text processing/phase extension."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "processing_phase_extension"


def check(name: str, condition: bool, detail: str) -> None:
    if not condition:
        raise AssertionError(f"[FAIL] {name}: {detail}")
    print(f"[PASS] {name}: {detail}")


def main() -> None:
    ledger = pd.read_csv(OUT / "verified_publication_annotations.csv")
    seed = pd.read_csv(OUT / "processing_phase_annotation_seed.csv")
    state = pd.read_csv(OUT / "processing_phase_annotation_state_aware.csv")
    audit = pd.read_csv(OUT / "target_semantics_audit.csv")
    cohort = pd.read_csv(OUT / "model_sensitivity" / "cohort_comparison.csv")
    model = pd.read_csv(OUT / "process_phase_model" / "process_phase_model_comparison.csv")
    bootstrap = pd.read_csv(OUT / "process_phase_model" / "paired_cluster_bootstrap.csv")

    check("publication-ledger", len(ledger) == 42 and ledger.reference_id.nunique() == 42,
          f"{len(ledger)} rows, {ledger.reference_id.nunique()} publications")
    check("publication-record-coverage", int(ledger.n_unique_records.sum()) == 141,
          f"sum={int(ledger.n_unique_records.sum())}")
    check("annotation-sizes", len(seed) == 141 and len(state) == 145,
          f"unique/state-aware={len(seed)}/{len(state)}")
    counts = seed.model_eligibility.value_counts()
    check("eligibility-partition",
          counts.get("eligible_process_phase_extension", 0) == 102
          and counts.get("exclude_pending_target_review", 0) == 31
          and counts.get("exclude_unverified_process_phase", 0) == 8,
          counts.to_dict().__str__())
    invalid = seed.loc[
        seed.model_eligibility.eq("eligible_process_phase_extension")
        & (~seed.target_audit_status.eq("verified_as_reported")
           | ~seed.verification_status.eq("verified"))
    ]
    check("no-unsafe-model-rows", invalid.empty, f"unsafe eligible rows={len(invalid)}")
    expected_review = {"[20]", "[21]", "[33]", "[35]", "[40]", "[41]"}
    check("target-review-sources", set(audit.reference_id) == expected_review,
          f"found={sorted(audit.reference_id)}")

    target = cohort.set_index("cohort")
    check("target-verified-r2", np.isclose(target.loc["target_verified", "oof_r2"], 0.420037, atol=1e-6),
          f"R2={target.loc['target_verified', 'oof_r2']:.6f}")
    check("eligible-composition-r2", np.isclose(target.loc["process_phase_eligible", "oof_r2"], 0.204505, atol=1e-6),
          f"R2={target.loc['process_phase_eligible', 'oof_r2']:.6f}")
    models = model.set_index("feature_set")
    check("combined-process-r2", np.isclose(models.loc["composition_plus_process_phase", "oof_r2"], 0.452784, atol=1e-6),
          f"R2={models.loc['composition_plus_process_phase', 'oof_r2']:.6f}")
    check("paired-improvement",
          float(models.loc["composition_plus_process_phase", "delta_r2_vs_composition_only"]) > 0
          and float(models.loc["composition_plus_process_phase", "delta_mae_K_vs_composition_only"]) < 0,
          "combined model improves R2 and MAE on identical rows/folds")
    b = bootstrap.set_index("metric")
    check("cluster-bootstrap-direction",
          b.loc["delta_r2", "cluster_bootstrap_95pct_low"] > 0
          and b.loc["delta_mae_K", "cluster_bootstrap_95pct_high"] < 0,
          "95% paired cluster intervals favor combined model")
    figure = ROOT / "figures" / "figure8_process_phase_audit.png"
    check("process-phase-figure", figure.is_file() and figure.stat().st_size > 100_000,
          f"{figure.relative_to(ROOT)} exists and is nontrivial")
    print("\nAll processing/phase extension checks passed.")


if __name__ == "__main__":
    main()
