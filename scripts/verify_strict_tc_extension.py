#!/usr/bin/env python3
"""Fast integrity checks for the v1.2.0 strict-TC extension."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def check(name: str, condition: bool, detail: str) -> None:
    if not condition:
        raise AssertionError(f"[FAIL] {name}: {detail}")
    print(f"[PASS] {name}: {detail}")


def main() -> None:
    audit_dir = ROOT / "results" / "strict_tc_audit"
    grouped_dir = ROOT / "results" / "strict_tc_grouped_cv"
    robust_dir = ROOT / "results" / "strict_tc_robustness"
    class_dir = ROOT / "results" / "strict_tc_classification"
    process_dir = ROOT / "results" / "strict_tc_process_phase"

    summary = json.loads((audit_dir / "strict_tc_audit_summary.json").read_text())
    check("audit-partition",
          summary["audited_records"] == 141
          and summary["strict_records"] == 79
          and summary["strict_publications"] == 26
          and summary["excluded_records"] == 62,
          "141 audited = 79 retained + 62 excluded; 26 retained publications")

    exclusions = pd.read_csv(audit_dir / "strict_tc_exclusion_counts.csv")
    check("exclusion-total", int(exclusions.n_records.sum()) == 62,
          f"sum={int(exclusions.n_records.sum())}")

    families = pd.read_csv(audit_dir / "strict_tc_family_summary.csv").set_index("chemistry_family")
    expected = {"3d-TM": (32, 9), "RE-rich": (25, 9), "TM-metalloid": (22, 8)}
    observed = {name: (int(families.loc[name, "n_records"]),
                       int(families.loc[name, "n_publications"])) for name in expected}
    check("family-counts", observed == expected, str(observed))

    summaries = [pd.read_csv(path).iloc[0] for path in grouped_dir.glob("summary__strict_hea__*.csv")]
    models = pd.DataFrame(summaries).set_index("model")
    tuned = models.drop(index="DummyMean")
    check("equal-budget-models", len(models) == 7 and tuned.candidate_budget.nunique() == 1
          and int(tuned.candidate_budget.iloc[0]) == 60
          and int(models.loc["DummyMean", "candidate_budget"]) == 0,
          f"{len(models)} models; six tuned models at {int(tuned.candidate_budget.iloc[0])} candidates plus dummy")
    check("svr-best", models.oof_r2.idxmax() == "SVR"
          and np.isclose(models.loc["SVR", "oof_r2"], 0.6104189971356822),
          f"best={models.oof_r2.idxmax()}, R2={models.loc['SVR', 'oof_r2']:.6f}")

    repeats = pd.read_csv(robust_dir / "repeated_partition_metrics.csv")
    check("repeated-partitions", len(repeats) == 5
          and np.isclose(repeats.r2.mean(), 0.4680697900067443)
          and np.isclose(repeats.family_mean_r2.mean(), 0.5054314967805322),
          f"SVR mean R2={repeats.r2.mean():.6f}; family baseline={repeats.family_mean_r2.mean():.6f}")

    variance = pd.read_csv(robust_dir / "family_variance_decomposition.csv").iloc[0]
    check("between-family-variance",
          np.isclose(variance.between_family_variance_share, 0.6046272861299071),
          f"share={variance.between_family_variance_share:.6f}")

    within = pd.read_csv(robust_dir / "within_family_metrics.csv").set_index("chemistry_family")
    expected_r2 = {"3d-TM": 0.1977705433259831,
                   "RE-rich": -1.791145888982642,
                   "TM-metalloid": -0.29656707005800187}
    check("within-family-r2",
          all(np.isclose(within.loc[name, "model_r2"], value)
              for name, value in expected_r2.items()),
          str(within.model_r2.round(6).to_dict()))

    lofo = pd.read_csv(robust_dir / "leave_family_out_metrics.csv")
    check("leave-family-out", (lofo.r2 < 0).all(), str(lofo.set_index("held_out_family").r2.round(6).to_dict()))

    classifiers = pd.read_csv(class_dir / "direct_classifier_summary.csv").set_index("model")
    check("direct-classifier", classifiers.balanced_accuracy.idxmax() == "Logistic"
          and np.isclose(classifiers.loc["Logistic", "mcc"], 0.4328187984966831),
          f"best=Logistic, MCC={classifiers.loc['Logistic', 'mcc']:.6f}")

    process = pd.read_csv(process_dir / "process_phase_model_comparison.csv").set_index("feature_set")
    check("strict-process-cohort",
          (process.n_records == 71).all() and (process.n_references == 24).all(),
          "71 records, 24 publications")
    bootstrap = pd.read_csv(process_dir / "paired_cluster_bootstrap.csv").set_index("metric")
    check("unresolved-process-effect",
          bootstrap.loc["delta_r2", "cluster_bootstrap_95pct_low"] < 0
          < bootstrap.loc["delta_r2", "cluster_bootstrap_95pct_high"],
          "delta-R2 95% interval crosses zero")

    figure = ROOT / "figures" / "figure8_strict_tc_v34.png"
    check("strict-figure", figure.is_file() and figure.stat().st_size > 100_000,
          f"{figure.relative_to(ROOT)} exists and is nontrivial")
    print("\nAll v1.2.0 strict-TC extension checks passed.")


if __name__ == "__main__":
    main()
