#!/usr/bin/env python3
"""Build the v1.2.0 record-level strict experimental Curie-temperature audit."""
from pathlib import Path
import json, re
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/processed/development_unique_141.csv'
OUT=ROOT/'results/strict_tc_audit'

RE={'Sc','Y','Gd','Tb','Dy','Ho','Er','Tm','Yb','Lu'}
MET={'B','C','Si','Ge','P','As','Sb'}
def family(comp):
    els=set(re.findall(r'[A-Z][a-z]?',str(comp)))
    return 'RE-rich' if els & RE else ('TM-metalloid' if els & MET else '3d-TM')

def main():
    d=pd.read_csv(SRC).copy(); d['TC_original']=d.TC
    d['chemistry_family']=d.composition.map(family)
    d['audit_status']='include_strict_experimental_TC'; d['audit_note']='Source-compatible experimental Curie temperature'
    decisions={
      'exclude_Neel_temperature':['[1]','[2]','[5]','[24]','[28]'],
      'exclude_secondary_source_only':['[33]'],
      'exclude_proxy_temperature':['[6]','[7]','[20]','[41]'],
      'exclude_state_ambiguous':['[40]'],
      'exclude_other_non_Curie_transition':['[14]','[16]','[19]'],
      'exclude_conflicting_assignment':['[21]','[35]'],
    }
    notes={
      'exclude_Neel_temperature':'Source identifies the value as a Néel temperature',
      'exclude_secondary_source_only':'Secondary-review value without primary-source traceback',
      'exclude_proxy_temperature':'Entropy peak, blocking temperature, or related proxy',
      'exclude_state_ambiguous':'Processing-state branch cannot be mapped unambiguously',
      'exclude_other_non_Curie_transition':'Non-Curie magnetic or magnetostructural feature',
      'exclude_conflicting_assignment':'Conflicting transition assignment or value',
    }
    for status,refs in decisions.items():
        m=d.reference_id.isin(refs); d.loc[m,'audit_status']=status; d.loc[m,'audit_note']=notes[status]
    for ref,comp in [('[4]','GdTbHoEr'),('[4]','GdTbHoErPr'),('[23]','GdTbHoEr'),('[23]','GdTbHoErLa')]:
        m=d.reference_id.eq(ref)&d.composition.eq(comp)
        d.loc[m,'audit_status']='exclude_Neel_temperature'; d.loc[m,'audit_note']=notes['exclude_Neel_temperature']
    d.loc[d.source_row.eq(91),'TC']=741.0
    d.loc[d.source_row.eq(92),'TC']=696.0
    d.loc[d.source_row.eq(91),'audit_note']='Experimental Curie temperature; source transcription corrected 736 to 741 K'
    d.loc[d.source_row.eq(92),'audit_note']='Experimental Curie temperature; source transcription corrected 651 to 696 K'
    strict=d[d.audit_status.eq('include_strict_experimental_TC')].copy()
    assert len(d)==141 and len(strict)==79 and strict.reference_id.nunique()==26
    counts=(d[~d.audit_status.eq('include_strict_experimental_TC')].groupby('audit_status').size()
            .rename('n_records').reset_index())
    fam=(strict.groupby('chemistry_family').agg(n_records=('TC','size'),n_publications=('reference_id','nunique'),
          TC_min_K=('TC','min'),TC_median_K=('TC','median'),TC_max_K=('TC','max')).reset_index())
    OUT.mkdir(parents=True,exist_ok=True)
    d.to_csv(OUT/'strict_tc_record_audit.csv',index=False)
    strict.to_csv(OUT/'strict_experimental_tc_79.csv',index=False)
    counts.to_csv(OUT/'strict_tc_exclusion_counts.csv',index=False)
    fam.to_csv(OUT/'strict_tc_family_summary.csv',index=False)
    total_ss=((strict.TC-strict.TC.mean())**2).sum()
    within=((strict.TC-strict.groupby('chemistry_family').TC.transform('mean'))**2).sum()
    (OUT/'strict_tc_audit_summary.json').write_text(json.dumps({
      'audited_records':141,'strict_records':79,'strict_publications':26,
      'excluded_records':62,'between_family_variance_share':1-within/total_ss,
      'corrected_source_rows':{'91':741.0,'92':696.0}},indent=2),encoding='utf-8')
    print(f'Strict cohort: {len(strict)} records / {strict.reference_id.nunique()} publications')

if __name__=='__main__': main()
