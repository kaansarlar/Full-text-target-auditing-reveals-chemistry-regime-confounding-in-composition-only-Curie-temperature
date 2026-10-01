#!/usr/bin/env python3
"""Compare composition-only and process/phase-aware models on audited records."""

from __future__ import annotations

import argparse
import json
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from publication_grouped_analysis import (
    HEA_FEATURES,
    INNER_SPLITS,
    OUTER_SPLITS,
    RANDOM_STATE,
    grouped_splits,
    metrics,
    model_specs,
    sample_grid,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "development_unique_141.csv"
ANNOTATION = ROOT / "results" / "processing_phase_extension" / "processing_phase_annotation_seed.csv"
SENSITIVITY = ROOT / "results" / "processing_phase_extension" / "model_sensitivity" / "cohort_comparison.csv"
DEFAULT_OUT = ROOT / "results" / "processing_phase_extension" / "process_phase_model"
COMPOSITION_OOF = ROOT / "results" / "processing_phase_extension" / "model_sensitivity" / "process_phase_eligible" / "oof__hea__LightGBM.csv"
CATEGORICAL = ["process_route", "thermal_state", "phase_class", "product_form"]

warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names, but LGBMRegressor was fitted with feature names",
    category=UserWarning,
)


def paired_cluster_bootstrap(combined_oof: Path, output_dir: Path, n_boot: int = 10000) -> None:
    """Compare fixed OOF predictions with publication-cluster bootstrap CIs."""
    composition = pd.read_csv(COMPOSITION_OOF)[
        ["source_row", "reference_id", "y_true_TC", "y_pred_TC", "absolute_error_K"]
    ].rename(columns={
        "y_pred_TC": "composition_prediction_K",
        "absolute_error_K": "composition_absolute_error_K",
    })
    combined = pd.read_csv(combined_oof)[
        ["source_row", "reference_id", "TC", "y_pred_TC", "absolute_error_K"]
    ].rename(columns={
        "TC": "y_true_combined_check",
        "y_pred_TC": "combined_prediction_K",
        "absolute_error_K": "combined_absolute_error_K",
    })
    paired = composition.merge(combined, on=["source_row", "reference_id"], validate="one_to_one")
    if not np.allclose(paired["y_true_TC"], paired["y_true_combined_check"]):
        raise RuntimeError("OOF target vectors differ between paired models")
    paired.drop(columns="y_true_combined_check", inplace=True)
    paired["absolute_error_difference_K"] = (
        paired["combined_absolute_error_K"] - paired["composition_absolute_error_K"]
    )
    paired.to_csv(output_dir / "paired_record_errors.csv", index=False)

    y = paired["y_true_TC"].to_numpy()
    pred_c = paired["composition_prediction_K"].to_numpy()
    pred_p = paired["combined_prediction_K"].to_numpy()
    refs = paired["reference_id"].to_numpy()
    unique_refs = np.unique(refs)
    rng = np.random.default_rng(RANDOM_STATE)
    samples = {"delta_mae_K": [], "delta_rmse_K": [], "delta_r2": []}
    for _ in range(n_boot):
        selected = rng.choice(unique_refs, size=len(unique_refs), replace=True)
        idx = np.concatenate([np.flatnonzero(refs == ref) for ref in selected])
        comp = metrics(y[idx], pred_c[idx])
        proc = metrics(y[idx], pred_p[idx])
        samples["delta_mae_K"].append(proc["mae"] - comp["mae"])
        samples["delta_rmse_K"].append(proc["rmse"] - comp["rmse"])
        samples["delta_r2"].append(proc["r2"] - comp["r2"])

    comp_all = metrics(y, pred_c)
    proc_all = metrics(y, pred_p)
    observed = {
        "delta_mae_K": proc_all["mae"] - comp_all["mae"],
        "delta_rmse_K": proc_all["rmse"] - comp_all["rmse"],
        "delta_r2": proc_all["r2"] - comp_all["r2"],
    }
    rows = []
    for metric, values in samples.items():
        values = np.asarray(values)
        direction = values < 0 if metric != "delta_r2" else values > 0
        rows.append({
            "metric": metric,
            "observed_difference_combined_minus_composition": observed[metric],
            "cluster_bootstrap_95pct_low": float(np.quantile(values, 0.025)),
            "cluster_bootstrap_95pct_high": float(np.quantile(values, 0.975)),
            "bootstrap_probability_of_improvement": float(direction.mean()),
            "n_bootstrap": n_boot,
            "cluster_unit": "reference_id",
        })
    pd.DataFrame(rows).to_csv(output_dir / "paired_cluster_bootstrap.csv", index=False)


def fit_feature_set(df: pd.DataFrame, feature_set: str, numeric: list[str], categorical: list[str],
                    candidate_budget: int, n_jobs: int, out_dir: Path) -> dict:
    columns = numeric + categorical
    X = df[columns].copy()
    y = df["TC"].astype(float).reset_index(drop=True)
    groups = df["reference_id"].astype(str).to_numpy()
    outer = grouped_splits(y, groups, OUTER_SPLITS, RANDOM_STATE)

    transformers = []
    if numeric:
        transformers.append(("numeric", "passthrough", numeric))
    if categorical:
        transformers.append(("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical))
    preprocessor = ColumnTransformer(transformers, remainder="drop")
    base_spec = model_specs()["LightGBM"]
    estimator = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", clone(base_spec["pipeline"].named_steps["regressor"])),
    ])
    model_index = list(model_specs()).index("LightGBM")
    candidates = sample_grid(base_spec["grid"], candidate_budget, RANDOM_STATE + model_index * 17)

    y_oof = np.full(len(y), np.nan)
    fold_rows = []
    param_rows = []
    split_rows = []
    for fold, (train_idx, test_idx) in enumerate(outer, start=1):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        g_train, g_test = groups[train_idx], groups[test_idx]
        inner = grouped_splits(y_train, g_train, INNER_SPLITS, RANDOM_STATE + fold)
        search = GridSearchCV(
            clone(estimator), candidates, scoring="r2", cv=inner, n_jobs=n_jobs,
            refit=True, error_score=np.nan, verbose=0,
        )
        search.fit(X_train, y_train, groups=g_train)
        pred = search.best_estimator_.predict(X_test)
        y_oof[test_idx] = pred
        fm = metrics(y_test, pred)
        fold_rows.append({
            "feature_set": feature_set, "fold": fold, "n_train": len(train_idx),
            "n_test": len(test_idx), "n_train_references": len(set(g_train)),
            "n_test_references": len(set(g_test)), "inner_best_r2": float(search.best_score_),
            **fm,
        })
        param_rows.append({"feature_set": feature_set, "fold": fold, **search.best_params_})
        split_rows.append({
            "feature_set": feature_set, "fold": fold,
            "train_references": ";".join(sorted(set(g_train))),
            "test_references": ";".join(sorted(set(g_test))),
        })
        print(f"{feature_set:24s} fold {fold:02d}/{len(outer)} R2={fm['r2']:.3f} MAE={fm['mae']:.1f}", flush=True)

    overall = metrics(y, y_oof)
    folds = pd.DataFrame(fold_rows)
    summary = {
        "feature_set": feature_set,
        "n_records": len(df),
        "n_references": int(df["reference_id"].nunique()),
        "n_numeric_features": len(numeric),
        "n_categorical_fields": len(categorical),
        "oof_r2": overall["r2"],
        "oof_rmse": overall["rmse"],
        "oof_mae": overall["mae"],
        "fold_r2_mean": float(folds["r2"].mean()),
        "fold_r2_sd": float(folds["r2"].std(ddof=1)),
    }
    oof = df[["source_row", "composition", "reference_id", "TC", *CATEGORICAL]].copy()
    oof["feature_set"] = feature_set
    oof["y_pred_TC"] = y_oof
    oof["residual_TC"] = y - y_oof
    oof["absolute_error_K"] = np.abs(y - y_oof)
    out_dir.mkdir(parents=True, exist_ok=True)
    folds.to_csv(out_dir / f"fold_metrics__{feature_set}.csv", index=False)
    pd.DataFrame(param_rows).to_csv(out_dir / f"best_params__{feature_set}.csv", index=False)
    pd.DataFrame(split_rows).to_csv(out_dir / f"split_audit__{feature_set}.csv", index=False)
    oof.to_csv(out_dir / f"oof_predictions__{feature_set}.csv", index=False)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--candidate-budget", type=int, default=60)
    parser.add_argument("--n-jobs", type=int, default=max(1, min(8, os.cpu_count() or 1)))
    args = parser.parse_args()

    data = pd.read_csv(DATA).reset_index(drop=True)
    annotation = pd.read_csv(ANNOTATION).reset_index(drop=True)
    keys = ["source_row", "composition", "reference_id", "TC"]
    if len(data) != len(annotation) or not data[keys].equals(annotation[keys]):
        raise RuntimeError("Annotation and analysis tables are not row-aligned")
    eligible = annotation["model_eligibility"].eq("eligible_process_phase_extension")
    df = data.loc[eligible].reset_index(drop=True)
    for field in CATEGORICAL:
        df[field] = annotation.loc[eligible, field].astype(str).reset_index(drop=True)

    baseline = pd.read_csv(SENSITIVITY)
    baseline = baseline.loc[baseline["cohort"].eq("process_phase_eligible")].iloc[0]
    rows = [{
        "feature_set": "composition_only",
        "n_records": int(baseline.n_records),
        "n_references": int(baseline.n_references),
        "n_numeric_features": len(HEA_FEATURES),
        "n_categorical_fields": 0,
        "oof_r2": float(baseline.oof_r2),
        "oof_rmse": float(baseline.oof_rmse),
        "oof_mae": float(baseline.oof_mae),
        "fold_r2_mean": float(baseline.fold_r2_mean),
        "fold_r2_sd": float(baseline.fold_r2_sd),
    }]
    rows.append(fit_feature_set(df, "process_phase_only", [], CATEGORICAL,
                                args.candidate_budget, args.n_jobs, args.output_dir))
    rows.append(fit_feature_set(df, "composition_plus_process_phase", HEA_FEATURES, CATEGORICAL,
                                args.candidate_budget, args.n_jobs, args.output_dir))
    summary = pd.DataFrame(rows)
    summary["delta_r2_vs_composition_only"] = summary["oof_r2"] - summary.loc[0, "oof_r2"]
    summary["delta_mae_K_vs_composition_only"] = summary["oof_mae"] - summary.loc[0, "oof_mae"]
    summary.to_csv(args.output_dir / "process_phase_model_comparison.csv", index=False)
    paired_cluster_bootstrap(
        args.output_dir / "oof_predictions__composition_plus_process_phase.csv",
        args.output_dir,
    )
    audit = {
        "status": "post_hoc_sensitivity_analysis",
        "cohort_rule": "target verified and record-level process/phase mapping resolved",
        "outer_split_seed": RANDOM_STATE,
        "outer_splits": OUTER_SPLITS,
        "inner_splits": INNER_SPLITS,
        "candidate_budget": args.candidate_budget,
        "warning": "Sparse publication-linked process categories can be unseen in held-out publications; interpret as a robustness diagnostic, not a definitive production model.",
    }
    (args.output_dir / "analysis_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
