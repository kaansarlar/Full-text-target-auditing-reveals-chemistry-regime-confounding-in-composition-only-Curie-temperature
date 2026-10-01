from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
cohort = pd.read_csv(ROOT / "results/processing_phase_extension/model_sensitivity/cohort_comparison.csv")
models = pd.read_csv(ROOT / "results/processing_phase_extension/process_phase_model/process_phase_model_comparison.csv")
paired = pd.read_csv(ROOT / "results/processing_phase_extension/process_phase_model/paired_record_errors.csv")

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 8.5,
        "axes.titlesize": 9.5,
        "axes.labelsize": 8.5,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
    }
)

blue = "#4472C4"
orange = "#ED7D31"
green = "#70AD47"
gray = "#A5A5A5"
red = "#C0504D"

fig, axes = plt.subplots(2, 2, figsize=(7.15, 6.0), dpi=180)

# (a) Conservative audit partition.
ax = axes[0, 0]
parts = [("Eligible", 102, green), ("Target review", 31, orange), ("Mapping unresolved", 8, gray)]
left = 0
for label, value, color in parts:
    ax.barh(["141 unique records"], [value], left=left, color=color, height=0.42, label=f"{label} ({value})")
    ax.text(
        left + value / 2,
        0,
        str(value),
        ha="center",
        va="center",
        color="white" if color != gray else "black",
        fontweight="bold",
    )
    left += value
ax.set_xlim(0, 141)
ax.set_xlabel("Records")
ax.set_title("(a) Full-text audit partition", loc="left", fontweight="bold")
ax.legend(frameon=False, fontsize=7, ncol=1, loc="upper center", bbox_to_anchor=(0.5, -0.28))
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0)

# (b) Cohort sensitivity. Across-cohort differences are not treated causally.
ax = axes[0, 1]
order = ["original_141", "target_verified", "process_phase_eligible"]
labels = ["Original\n141", "Target verified\n110", "Strict audited\n102"]
values = [float(cohort.set_index("cohort").loc[name, "oof_r2"]) for name in order]
bars = ax.bar(labels, values, color=[blue, orange, green], width=0.62)
ax.axhline(0, color="black", lw=0.7)
ax.set_ylabel("Publication-grouped OOF $R^2$")
ax.set_ylim(0, 0.7)
ax.set_title("(b) Sensitivity to audit exclusions", loc="left", fontweight="bold")
for bar, value in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width() / 2, value + 0.025, f"{value:.3f}", ha="center", va="bottom", fontweight="bold")
ax.spines[["top", "right"]].set_visible(False)

# (c) Feature comparison on identical records and folds.
ax = axes[1, 0]
model_order = ["composition_only", "process_phase_only", "composition_plus_process_phase"]
model_labels = ["Composition", "Process/phase", "Combined"]
model_values = [float(models.set_index("feature_set").loc[name, "oof_r2"]) for name in model_order]
bars = ax.bar(model_labels, model_values, color=[blue, gray, green], width=0.62)
ax.axhline(0, color="black", lw=0.7)
ax.set_ylabel("Publication-grouped OOF $R^2$")
ax.set_ylim(-0.15, 0.58)
ax.set_title("(c) Same 102 records and outer folds", loc="left", fontweight="bold")
for bar, value in zip(bars, model_values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        value + (0.025 if value >= 0 else -0.04),
        f"{value:.3f}",
        ha="center",
        va="bottom" if value >= 0 else "top",
        fontweight="bold",
    )
ax.spines[["top", "right"]].set_visible(False)

# (d) Publication-level paired absolute errors.
ax = axes[1, 1]
publication = paired.groupby("reference_id", as_index=False).agg(
    composition_mae=("composition_absolute_error_K", "mean"),
    combined_mae=("combined_absolute_error_K", "mean"),
)
improved = publication["combined_mae"] < publication["composition_mae"]
ax.scatter(
    publication.loc[improved, "composition_mae"],
    publication.loc[improved, "combined_mae"],
    color=green,
    s=28,
    alpha=0.85,
    label=f"Improved ({improved.sum()}/34)",
)
ax.scatter(
    publication.loc[~improved, "composition_mae"],
    publication.loc[~improved, "combined_mae"],
    color=red,
    s=28,
    alpha=0.85,
    label=f"Not improved ({(~improved).sum()}/34)",
)
limit = max(publication["composition_mae"].max(), publication["combined_mae"].max()) * 1.05
ax.plot([0, limit], [0, limit], "--", color="black", lw=0.8)
ax.set_xlim(0, limit)
ax.set_ylim(0, limit)
ax.set_xlabel("Composition-only MAE by publication (K)")
ax.set_ylabel("Combined-model MAE by publication (K)")
ax.set_title("(d) Paired publication-level errors", loc="left", fontweight="bold")
ax.legend(frameon=False, fontsize=7, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)

for axis in axes.flat:
    axis.grid(axis="y", alpha=0.18, lw=0.5)

fig.tight_layout(w_pad=2.0, h_pad=2.4)
OUT.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT / "figure8_process_phase_audit.png", dpi=400, bbox_inches="tight")
fig.savefig(OUT / "figure8_process_phase_audit.pdf", bbox_inches="tight")
plt.close(fig)
