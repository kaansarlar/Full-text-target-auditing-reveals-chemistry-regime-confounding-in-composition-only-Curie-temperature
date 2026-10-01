#!/usr/bin/env python3
"""Build a conservative processing/phase annotation scaffold.

The output is an audit table, not a model-ready feature table. Labels inferred
from publication titles are explicitly marked as requiring full-text
verification and must not be used as confirmed inputs.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "development_unique_141.csv"
FULL_DATA = ROOT / "data" / "processed" / "development_full_199.csv"
OUT_DIR = ROOT / "results" / "processing_phase_extension"
VERIFIED_PUBLICATIONS = OUT_DIR / "verified_publication_annotations.csv"


def classify_title(reference_text: str) -> dict[str, str]:
    text = reference_text.lower()
    result = {
        "process_route": "unknown",
        "thermal_state": "unknown",
        "phase_class": "unknown",
        "product_form": "unspecified",
        "label_source": "none",
        "evidence_text": "",
        "confidence": "unverified",
        "verification_status": "full_text_required",
    }

    evidence = []
    if "melt-spun" in text:
        result["process_route"] = "melt_spinning"
        result["product_form"] = "ribbon"
        evidence.append("melt-spun")
    elif "ribbon" in text:
        result["product_form"] = "ribbon"
        evidence.append("ribbon")
    if "thin-film" in text and "co-evaporation" in text:
        result["process_route"] = "co_evaporation"
        result["product_form"] = "thin_film"
        evidence.extend(["thin-film", "co-evaporation"])
    elif "thin-film" in text:
        result["product_form"] = "thin_film"
        evidence.append("thin-film")
    if "microwire" in text:
        result["product_form"] = "microwire"
        evidence.append("microwire")
    if "bulk metallic glass" in text:
        result["phase_class"] = "amorphous"
        result["product_form"] = "bulk_metallic_glass"
        evidence.append("bulk metallic glass")
    elif "amorphous/nanocrystalline" in text:
        result["phase_class"] = "amorphous_nanocrystalline"
        evidence.append("amorphous/nanocrystalline")
    elif "amorphous" in text:
        result["phase_class"] = "amorphous"
        evidence.append("amorphous")
    elif "dual-phase" in text:
        result["phase_class"] = "dual_phase"
        evidence.append("dual-phase")

    if evidence:
        result["label_source"] = "publication_title"
        result["evidence_text"] = "; ".join(dict.fromkeys(evidence))
        result["confidence"] = "candidate_only"
        result["verification_status"] = "full_text_required"
    return result


def descriptor_group_summary(df: pd.DataFrame) -> pd.DataFrame:
    features = [
        "dX", "VEC", "sigma", "dHmix", "dSmix", "nunfilled_mean",
        "mag_moment_mean", "avg_d_valence_electrons", "bandgap_mean",
        "melting_point_mean", "electronegativity_range",
    ]
    grouped = df.groupby(features, dropna=False, sort=False)
    group_id = pd.Series(index=df.index, dtype="object")
    group_n = pd.Series(index=df.index, dtype="int64")
    group_range = pd.Series(index=df.index, dtype="float64")
    for number, (_, idx) in enumerate(grouped.indices.items(), start=1):
        idx = list(idx)
        values = df.loc[idx, "TC"]
        label = f"DG{number:03d}"
        group_id.loc[idx] = label
        group_n.loc[idx] = len(idx)
        group_range.loc[idx] = values.max() - values.min()
    return pd.DataFrame({
        "descriptor_group_id": group_id,
        "descriptor_group_n": group_n,
        "descriptor_group_TC_range_K": group_range,
    })


def apply_verified_source_overrides(out: pd.DataFrame) -> pd.DataFrame:
    """Apply only source-checked record-level annotations."""
    out = out.copy()
    safe_publication_mappings = {"all_records_direct", "record_states_restored"}

    def confirm(mask: pd.Series, *, process: str, state: str, phase: str, product: str,
                evidence: str, note: str = "") -> None:
        """Assign a full-text-verified record mapping in place."""
        out.loc[mask, "process_route"] = process
        out.loc[mask, "thermal_state"] = state
        out.loc[mask, "phase_class"] = phase
        out.loc[mask, "product_form"] = product
        out.loc[mask, "label_source"] = "uploaded_full_text"
        out.loc[mask, "confidence"] = "confirmed"
        out.loc[mask, "verification_status"] = "verified"
        out.loc[mask, "evidence_text"] = evidence
        if note:
            out.loc[mask, "review_notes"] = note

    if VERIFIED_PUBLICATIONS.exists():
        verified = pd.read_csv(VERIFIED_PUBLICATIONS)
        for source in verified.itertuples(index=False):
            source_mask = out["reference_id"].eq(source.reference_id)
            if not source_mask.any():
                continue
            out.loc[source_mask, "target_audit_status"] = source.target_audit_status
            out.loc[source_mask, "target_audit_note"] = source.target_audit_note
            out.loc[source_mask, "publication_mapping_status"] = source.record_mapping_status
            if source.record_mapping_status not in safe_publication_mappings:
                continue
            confirm(
                source_mask,
                process=source.process_route,
                state=source.thermal_state_scope,
                phase=source.phase_class,
                product=source.product_form,
                evidence=(
                f"DOI {source.doi}, uploaded PDF pp. {source.evidence_pages}: "
                f"{source.evidence_summary}"
                ),
            )

    mask = out["reference_id"].eq("[2]")
    if mask.any():
        ingot = mask & out["composition"].str.contains("25.11", regex=False, na=False)
        ribbon = mask & out["composition"].str.contains("23.58", regex=False, na=False)
        out.loc[ingot, "thermal_state"] = "as_cast_ingot"
        out.loc[ingot, "product_form"] = "ingot"
        out.loc[ribbon, "thermal_state"] = "melt_spun_25m_s"
        out.loc[ribbon, "product_form"] = "ribbon"
        out.loc[mask, "review_notes"] = (
            "The measured compositions printed in the source identify the ingot and ribbon records."
        )

    mask = out["reference_id"].eq("[11]")
    if mask.any():
        out.loc[mask, "process_route"] = "arc_melting+suction_casting+melt_extraction"
        out.loc[mask, "phase_class"] = "amorphous_nanocrystalline"
        out.loc[mask, "product_form"] = "microwire"
        out.loc[mask, "label_source"] = "full_text_methods"
        out.loc[mask, "confidence"] = "confirmed"
        out.loc[mask, "verification_status"] = "verified"
        out.loc[mask, "evidence_text"] = (
            "DOI 10.1007/s40843-021-1825-1, Methods: melt-extracted "
            "microwires; DC current annealing at 50, 75, or 100 x 10^6 "
            "A m-2 for 480 s in air; amorphous/nanocrystalline microstructure."
        )
        states = {
            "as_cast": "as_cast",
            "micro_50": "current_annealed_50e6_A_m-2_480s_air",
            # The dataset's micro_70 label corresponds to 75 x 10^6 A m-2
            # in the source Methods section.
            "micro_70": "current_annealed_75e6_A_m-2_480s_air",
            "micro_100": "current_annealed_100e6_A_m-2_480s_air",
        }
        for token, state in states.items():
            state_mask = mask & out["composition"].str.contains(token, regex=False, na=False)
            out.loc[state_mask, "thermal_state"] = state
        typo_mask = mask & out["composition"].str.contains("micro_70", regex=False, na=False)
        out.loc[typo_mask, "review_notes"] = (
            "Raw state label micro_70 maps to 75 x 10^6 A m-2 in the source; "
            "retain raw text for traceability and use the normalized thermal_state."
        )

    mask = out["reference_id"].eq("[29]")
    if mask.any():
        out.loc[mask, "process_route"] = "arc_melting+suction_casting"
        out.loc[mask, "phase_class"] = "single_phase_bcc"
        out.loc[mask, "product_form"] = "suction_cast_rod"
        out.loc[mask, "label_source"] = "full_text_methods_and_table"
        out.loc[mask, "confidence"] = "confirmed"
        out.loc[mask, "verification_status"] = "verified"
        out.loc[mask, "evidence_text"] = (
            "DOI 10.1016/j.cap.2019.09.019: arc-melted and suction-cast rod; "
            "Table 2 assigns TC=322 K to as-quenched and TC=334 K to the "
            "700 K/1 h Ar-annealed condition; both states are BCC."
        )
        as_quenched = mask & out["TC"].eq(322.0)
        annealed = mask & out["TC"].eq(334.0)
        out.loc[as_quenched, "thermal_state"] = "as_quenched"
        out.loc[annealed, "thermal_state"] = "annealed_700K_1h_Ar_slow_cooled"
        out.loc[mask, "review_notes"] = (
            "The raw composition string omits state; thermal_state was restored "
            "from the source table using the reported TC value."
        )

    mask = out["reference_id"].eq("[34]")
    if mask.any():
        as_quenched = mask & out["TC"].eq(442.0)
        annealed = mask & out["TC"].eq(462.0)
        out.loc[as_quenched, "thermal_state"] = "as_quenched"
        out.loc[annealed, "thermal_state"] = "annealed_500K_1h_Ar_slow_cooled"
        out.loc[mask, "review_notes"] = (
            "The raw composition string omits state; thermal_state was restored "
            "from the source using the reported TC value."
        )

    # Composition-specific phase mappings transcribed from the checked full texts.
    mask = out["reference_id"].eq("[5]")
    if mask.any():
        for comp, phase in {
            "Gd20Dy20Er20Ho20Tb20": "single_phase_hcp",
            "Gd25Er25Ho25Tb25": "hcp_plus_trigonal",
            "Dy25Er25Ho25Tb25": "hcp_plus_trigonal",
            "Er33.33Ho33.33Tb33.34": "hcp_plus_trigonal",
        }.items():
            row = mask & out["composition"].eq(comp)
            confirm(row, process="arc_melting+drop_casting", state="as_cast", phase=phase,
                    product="drop_cast_rod", evidence="DOI-checked full text, XRD phase assignment by composition (reference 5).")

    mask = out["reference_id"].eq("[13]")
    if mask.any():
        first = mask & out["composition"].str.startswith("(MnNiSi)", na=False)
        second = mask & out["composition"].str.startswith("(MnNi)0.6", na=False)
        shared = dict(process="arc_melting+vacuum_annealing+water_quenching",
                      state="annealed_1023K_72h_vacuum_water_quenched", product="ingot")
        confirm(first, phase="single_phase_Ni2In_hexagonal", evidence="DOI-checked full text, Fig. 1/XRD (reference 13).", **shared)
        confirm(second, phase="Ni2In_hexagonal_plus_TiNiSi_orthorhombic", evidence="DOI-checked full text, Fig. 8/XRD (reference 13).", **shared)

    mask = out["reference_id"].eq("[14]")
    if mask.any():
        hydrogenated = mask & out["composition"].str.contains("H 57", regex=False, na=False)
        hydrogen_free = mask & ~hydrogenated
        confirm(hydrogen_free, process="arc_melting+copper_mold_casting+ball_milling+annealing",
                state="annealed_538K_150ks_0MPa", phase="amorphous_matrix_plus_nanocrystals",
                product="powder", evidence="DOI-checked full text, hydrogen-free comparison condition (reference 14).")
        confirm(hydrogenated, process="arc_melting+copper_mold_casting+ball_milling+hydrogenation",
                state="hydrogenated_538K_5MPa_150ks", phase="amorphous_matrix_plus_nanocrystalline_dihydrides",
                product="powder", evidence="DOI-checked full text, hydrogenated condition (reference 14).")

    mask = out["reference_id"].eq("[18]")
    if mask.any():
        phase_rules = {
            "CoFeNiCr1.0Cu0.0": "single_phase_fcc",
            "CoFeNiCr1.0Cu0.5": "fcc_with_cu_rich_segregation",
            "CoFeNiCr1.0Cu1.0": "dual_phase_fcc",
            "CoFeNiCr0.8Cu1.0": "fcc_with_cu_rich_segregation",
        }
        for comp, phase in phase_rules.items():
            row = mask & out["composition"].eq(comp)
            confirm(row, process="arc_melting+suction_casting", state="as_cast", phase=phase,
                    product="suction_cast_rod", evidence="DOI-checked full text, XRD/SEM assignment by composition (reference 18).")

    mask = out["reference_id"].eq("[22]")
    if mask.any():
        al = mask & out["composition"].str.endswith("CoAl", na=False)
        ni = mask & out["composition"].str.endswith("CoNi", na=False)
        shared = dict(process="arc_melting+melt_spinning", state="as_spun", product="ribbon")
        confirm(al, phase="fully_amorphous", evidence="DOI-checked full text, XRD assignment for Al ribbon (reference 22).", **shared)
        confirm(ni, phase="amorphous_plus_hcp_nanocrystals", evidence="DOI-checked full text, XRD assignment for Ni ribbon (reference 22).", **shared)

    mask = out["reference_id"].eq("[24]")
    if mask.any():
        rules = {
            144.0: ("as_cast", "hcp_with_minor_fcc_or_oxide", "ingot"),
            143.0: ("suction_cast_3mm_rapidly_quenched", "single_phase_hcp", "suction_cast_rod"),
            146.0: ("annealed_1173K_2h_vacuum", "hcp_with_minor_fcc_or_oxide", "annealed_ingot"),
            139.0: ("severely_cold_deformed", "single_phase_hcp", "cold_deformed_sample"),
        }
        for tc, (state, phase, product) in rules.items():
            row = mask & out["TC"].eq(tc)
            out.loc[row, "thermal_state"] = state
            out.loc[row, "phase_class"] = phase
            out.loc[row, "product_form"] = product
        out.loc[mask, "review_notes"] = "The four source states were restored from their distinct reported transition temperatures."

    mask = out["reference_id"].eq("[25]")
    if mask.any():
        phases = {
            "LaFe10.8Cr0.2Si2": "LaFeSi13_plus_alphaFe_or_La_rich_secondary",
            "LaFe10Co0.5Ni0.5Si2": "LaFeSi13_plus_alphaFe_or_La_rich_secondary",
            "LaFe10.25Co0.25Ni0.25Cr0.25Si2": "predominantly_single_phase_LaFeSi13",
        }
        for comp, phase in phases.items():
            row = mask & out["composition"].eq(comp)
            confirm(row, process="arc_melting+vacuum_annealing+water_quenching",
                    state="annealed_1323K_9d_vacuum_water_quenched", phase=phase,
                    product="ingot", evidence="DOI-checked full text, XRD/EPMA assignment by composition (reference 25).")

    mask = out["reference_id"].eq("[35]")
    if mask.any():
        fcc = mask & out["composition"].str.contains("x = 0.0", regex=False, na=False)
        dual = mask & out["composition"].str.contains("x = 1.5", regex=False, na=False)
        shared = dict(process="arc_melting+casting+annealing+water_quenching",
                      state="annealed_1423K_10h_Ar_water_quenched", product="cast_rod")
        confirm(fcc, phase="single_phase_fcc", evidence="DOI-checked full text, XRD for Al0.0 (reference 35).", **shared)
        confirm(dual, phase="B2_matrix_plus_bcc_FeCr_precipitates", evidence="DOI-checked full text, XRD/TEM for Al1.5 (reference 35).", **shared)

    out["model_eligibility"] = "exclude_unverified_process_phase"
    verified_mask = out["verification_status"].eq("verified")
    target_ok = out["target_audit_status"].eq("verified_as_reported")
    out.loc[verified_mask & target_ok, "model_eligibility"] = "eligible_process_phase_extension"
    out.loc[~target_ok, "model_eligibility"] = "exclude_pending_target_review"
    return out


def build_table(df: pd.DataFrame) -> pd.DataFrame:
    annotations = pd.DataFrame(
        [classify_title(x) for x in df["reference_text"].fillna("")],
        index=df.index,
    )
    degenerate = descriptor_group_summary(df)
    out = pd.concat(
        [
            df[["source_row", "composition", "reference_id", "reference_text", "TC"]],
            annotations,
            degenerate,
        ],
        axis=1,
    )
    out.insert(0, "annotation_record_id", [f"A{i:03d}" for i in range(1, len(out) + 1)])
    out["review_notes"] = ""
    out["publication_mapping_status"] = "not_checked"
    out["target_audit_status"] = "not_checked"
    out["target_audit_note"] = ""
    return apply_verified_source_overrides(out)


def main() -> None:
    df = pd.read_csv(DATA)
    out = build_table(df)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "processing_phase_annotation_seed.csv"
    out.to_csv(out_path, index=False)

    full = pd.read_csv(FULL_DATA)
    state_keys = [
        "reference_id", "composition", "TC", "dX", "VEC", "sigma", "dHmix",
        "dSmix", "nunfilled_mean", "mag_moment_mean",
        "avg_d_valence_electrons", "bandgap_mean", "melting_point_mean",
        "electronegativity_range",
    ]
    state_df = full.drop_duplicates(state_keys, keep="first").reset_index(drop=True)
    state_out = build_table(state_df)
    state_path = OUT_DIR / "processing_phase_annotation_state_aware.csv"
    state_out.to_csv(state_path, index=False)

    publication = (
        out.groupby(["reference_id", "reference_text"], as_index=False)
        .agg(
            n_records=("annotation_record_id", "size"),
            candidate_process=("process_route", lambda x: "; ".join(sorted(set(x)))),
            candidate_phase=("phase_class", lambda x: "; ".join(sorted(set(x)))),
            product_form=("product_form", lambda x: "; ".join(sorted(set(x)))),
            verification_status=("verification_status", lambda x: "; ".join(sorted(set(x)))),
        )
    )
    publication.to_csv(OUT_DIR / "publication_annotation_audit.csv", index=False)

    verified_state = state_out.loc[
        state_out["model_eligibility"].eq("eligible_process_phase_extension")
    ]
    coverage_rows = []
    for field in ["process_route", "phase_class", "product_form", "thermal_state"]:
        counts = verified_state[field].value_counts(dropna=False)
        for category, count in counts.items():
            subset = verified_state.loc[verified_state[field].eq(category), "TC"]
            coverage_rows.append(
                {
                    "field": field,
                    "category": category,
                    "n_records": int(count),
                    "n_publications": int(
                        verified_state.loc[verified_state[field].eq(category), "reference_id"].nunique()
                    ),
                    "TC_median_K": float(subset.median()),
                    "TC_min_K": float(subset.min()),
                    "TC_max_K": float(subset.max()),
                }
            )
    pd.DataFrame(coverage_rows).to_csv(OUT_DIR / "verified_annotation_coverage.csv", index=False)

    target_review = state_out.loc[
        ~state_out["target_audit_status"].isin(["verified_as_reported", "not_checked"])
    ].copy()
    target_audit = (
        target_review.groupby(
            ["reference_id", "reference_text", "target_audit_status", "target_audit_note"],
            as_index=False,
        )
        .agg(
            n_state_aware_records=("annotation_record_id", "size"),
            compositions=("composition", lambda x: "; ".join(dict.fromkeys(map(str, x)))),
            dataset_values_K=("TC", lambda x: "; ".join(dict.fromkeys(f"{v:g}" for v in x))),
            publication_mapping_status=("publication_mapping_status", lambda x: "; ".join(sorted(set(x)))),
            process_phase_verification=("verification_status", lambda x: "; ".join(sorted(set(x)))),
            model_eligibility=("model_eligibility", lambda x: "; ".join(sorted(set(x)))),
        )
        .sort_values("reference_id", key=lambda x: x.str.extract(r"(\d+)")[0].astype(int))
    )
    target_audit.to_csv(OUT_DIR / "target_semantics_audit.csv", index=False)

    title_candidates = (out["label_source"] == "publication_title").sum()
    degenerate_records = (out["descriptor_group_n"] > 1).sum()
    print(f"records={len(out)} publications={publication.shape[0]}")
    print(f"title-derived candidate labels={title_candidates}")
    print(f"confirmed process/phase labels={(out['verification_status'] == 'verified').sum()}")
    print(f"model-eligible labels={(out['model_eligibility'] == 'eligible_process_phase_extension').sum()}")
    print(f"target-review records={len(target_review)} across {target_review['reference_id'].nunique()} publications")
    print(f"descriptor-degenerate records={degenerate_records}")
    print(out_path)
    print(f"state-aware records={len(state_out)}")
    print(
        f"state-aware model-eligible records={len(verified_state)} "
        f"across {verified_state['reference_id'].nunique()} publications"
    )
    print(state_path)


if __name__ == "__main__":
    main()
