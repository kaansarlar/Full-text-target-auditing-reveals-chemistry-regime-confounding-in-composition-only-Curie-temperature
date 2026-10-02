#!/usr/bin/env python3
"""Equal-budget publication-grouped model comparison on the strict TC cohort."""
from __future__ import annotations
import argparse,json,os,time
from pathlib import Path
import pandas as pd
from publication_grouped_analysis import HEA_FEATURES,model_specs,run_model

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'results/strict_tc_audit/strict_experimental_tc_79.csv'
OUT=ROOT/'results/strict_tc_grouped_cv'
MODELS=['DummyMean','Ridge','RandomForest','GradientBoosting','SVR','XGBoost','LightGBM']

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate-budget',type=int,default=60);p.add_argument('--n-jobs',type=int,default=max(1,min(8,os.cpu_count() or 1)));p.add_argument('--output-dir',type=Path,default=OUT);p.add_argument('--models',default=','.join(MODELS));a=p.parse_args()
 d=pd.read_csv(DATA);a.output_dir.mkdir(parents=True,exist_ok=True); specs=model_specs(); requested=[x.strip() for x in a.models.split(',') if x.strip()]
 summaries=[];folds=[];params=[];splits=[];oofs=[];start=time.time()
 for name in requested:
  if name not in specs: print('Unavailable estimator skipped:',name);continue
  result=run_model(d,HEA_FEATURES,'strict_hea',name,specs[name],a.output_dir,a.candidate_budget,a.n_jobs)
  summaries.append(result[0]);folds.append(result[1]);params.append(result[2]);splits.append(result[3]);oofs.append(result[4])
 # Consolidate every completed per-model output.
 tables={k:[] for k in ['summary','folds','params','splits','oof']}
 for name in MODELS:
  paths={'summary':a.output_dir/f'summary__strict_hea__{name}.csv','folds':a.output_dir/f'folds__strict_hea__{name}.csv','params':a.output_dir/f'params__strict_hea__{name}.csv','splits':a.output_dir/f'splits__strict_hea__{name}.csv','oof':a.output_dir/f'oof__strict_hea__{name}.csv'}
  if all(x.exists() for x in paths.values()):
   for k,path in paths.items(): tables[k].append(pd.read_csv(path))
 summary=pd.concat(tables['summary'],ignore_index=True).sort_values('oof_r2',ascending=False)
 summary.to_csv(a.output_dir/'strict_model_summary.csv',index=False)
 pd.concat(tables['folds'],ignore_index=True).to_csv(a.output_dir/'strict_fold_metrics.csv',index=False)
 pd.concat(tables['params'],ignore_index=True).to_csv(a.output_dir/'strict_best_params.csv',index=False)
 pd.concat(tables['splits'],ignore_index=True).to_csv(a.output_dir/'strict_split_audit.csv',index=False)
 pd.concat(tables['oof'],ignore_index=True).to_csv(a.output_dir/'strict_oof_predictions.csv',index=False)
 (a.output_dir/'analysis_audit.json').write_text(json.dumps({'n_records':79,'n_publications':26,'features':HEA_FEATURES,'models_consolidated':summary.model.tolist(),'candidate_budget':a.candidate_budget,'elapsed_seconds':time.time()-start},indent=2),encoding='utf-8')
 print(summary.to_string(index=False))
if __name__=='__main__':main()
