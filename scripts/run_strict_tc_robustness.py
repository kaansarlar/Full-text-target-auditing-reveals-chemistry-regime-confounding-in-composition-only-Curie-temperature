#!/usr/bin/env python3
"""Repeated partitions, family baselines, within-family, LOFO, and bootstrap checks."""
from pathlib import Path
import argparse,json,os
import numpy as np,pandas as pd
from sklearn.base import clone
from sklearn.metrics import r2_score,mean_absolute_error,mean_squared_error,confusion_matrix,matthews_corrcoef
from sklearn.model_selection import GridSearchCV
from publication_grouped_analysis import HEA_FEATURES,grouped_splits,model_specs,sample_grid,RANDOM_STATE

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'results/strict_tc_audit/strict_experimental_tc_79.csv'; CV=ROOT/'results/strict_tc_grouped_cv'; OUT=ROOT/'results/strict_tc_robustness'
def reg(y,p):return {'r2':r2_score(y,p),'rmse_K':mean_squared_error(y,p)**.5,'mae_K':mean_absolute_error(y,p),'bias_K':float(np.mean(np.asarray(p)-np.asarray(y)))}
def cls(y,p):
 tn,fp,fn,tp=confusion_matrix(y,p,labels=[0,1]).ravel();rec=tp/(tp+fn) if tp+fn else np.nan;spec=tn/(tn+fp) if tn+fp else np.nan;prec=tp/(tp+fp) if tp+fp else 0;prev=np.mean(y)
 return {'tp':tp,'tn':tn,'fp':fp,'fn':fn,'precision':prec,'recall':rec,'specificity':spec,'balanced_accuracy':np.mean([rec,spec]) if np.isfinite(rec) else np.nan,'mcc':matthews_corrcoef(y,p) if len(set(y))>1 else np.nan,'enrichment':prec/prev if prev and sum(p) else np.nan}
def fitpred(X,y,g,tr,te,name,budget,seed,jobs):
 spec=model_specs()[name];idx=list(model_specs()).index(name);cand=sample_grid(spec['grid'],budget,seed+idx*17);inner=grouped_splits(y.iloc[tr],g[tr],5,seed)
 s=GridSearchCV(clone(spec['pipeline']),cand,scoring='r2',cv=inner,n_jobs=jobs,refit=True,error_score=np.nan).fit(X.iloc[tr],y.iloc[tr],groups=g[tr]);return s.predict(X.iloc[te])
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--n-jobs',type=int,default=max(1,min(8,os.cpu_count() or 1)));ap.add_argument('--candidate-budget',type=int,default=30);a=ap.parse_args();OUT.mkdir(parents=True,exist_ok=True)
 d=pd.read_csv(DATA).reset_index(drop=True);X=d[HEA_FEATURES].astype(float);y=d.TC.astype(float);g=d.reference_id.astype(str).to_numpy();name=pd.read_csv(CV/'strict_model_summary.csv').sort_values('oof_r2',ascending=False).iloc[0].model
 rows=[];po=[]
 for seed in range(5):
  pred=np.zeros(len(d));fam=np.zeros(len(d))
  for fold,(tr,te) in enumerate(grouped_splits(y,g,10,seed),1):
   pred[te]=fitpred(X,y,g,tr,te,name,a.candidate_budget,seed+fold,a.n_jobs);means=d.iloc[tr].groupby('chemistry_family').TC.mean();fam[te]=d.iloc[te].chemistry_family.map(means).fillna(y.iloc[tr].mean())
   for i in te:po.append({'seed':seed,'fold':fold,'source_row':d.iloc[i].source_row,'reference_id':d.iloc[i].reference_id,'chemistry_family':d.iloc[i].chemistry_family,'TC':y.iloc[i],'prediction_K':pred[i],'family_mean_prediction_K':fam[i]})
  r={'seed':seed,'model':name,**reg(y,pred),**{f'family_mean_{k}':v for k,v in reg(y,fam).items()}};yb=y.between(250,350).astype(int).to_numpy();pb=((pred>=250)&(pred<=350)).astype(int);r.update({f'window_{k}':v for k,v in cls(yb,pb).items()})
  for f in sorted(d.chemistry_family.unique()):m=d.chemistry_family.eq(f);r[f'{f}_r2']=r2_score(y[m],pred[m]);r[f'{f}_mae_K']=mean_absolute_error(y[m],pred[m])
  rows.append(r);print(seed,r['r2'],flush=True)
 pd.DataFrame(rows).to_csv(OUT/'repeated_partition_metrics.csv',index=False);pd.DataFrame(po).to_csv(OUT/'repeated_partition_oof.csv',index=False)
 o=pd.read_csv(CV/'strict_oof_predictions.csv');o=o[o.model.eq(name)][['source_row','y_pred_TC']];m=d.merge(o,on='source_row');sp=pd.read_csv(CV/'strict_split_audit.csv');sp=sp[sp.model.eq(name)];m['fold']=0
 for _,z in sp.iterrows():m.loc[m.reference_id.isin(str(z.test_references).split(';')),'fold']=int(z.fold)
 fp=np.zeros(len(m))
 for fold in sorted(m.fold.unique()):tr=m.fold.ne(fold);te=m.fold.eq(fold);means=m.loc[tr].groupby('chemistry_family').TC.mean();fp[te]=m.loc[te,'chemistry_family'].map(means).fillna(m.loc[tr,'TC'].mean())
 m['family_mean_prediction_K']=fp;m.to_csv(OUT/'fixed_partition_family_predictions.csv',index=False)
 fr=[]
 for f,z in m.groupby('chemistry_family'):
  rr={'chemistry_family':f,'n':len(z),'n_publications':z.reference_id.nunique(),'TC_mean_K':z.TC.mean(),'TC_sd_K':z.TC.std()};rr.update({f'model_{k}':v for k,v in reg(z.TC,z.y_pred_TC).items()});rr.update({f'family_mean_{k}':v for k,v in reg(z.TC,z.family_mean_prediction_K).items()});fr.append(rr)
 pd.DataFrame(fr).to_csv(OUT/'within_family_metrics.csv',index=False)
 total=((m.TC-m.TC.mean())**2).sum();within=((m.TC-m.groupby('chemistry_family').TC.transform('mean'))**2).sum();pd.DataFrame([{'n':79,'n_publications':26,'between_family_variance_share':1-within/total,'within_family_variance_share':within/total,**{f'model_{k}':v for k,v in reg(m.TC,m.y_pred_TC).items()},**{f'family_mean_{k}':v for k,v in reg(m.TC,m.family_mean_prediction_K).items()}}]).to_csv(OUT/'family_variance_decomposition.csv',index=False)
 targ=[];true=m.TC.between(250,350).astype(int).to_numpy()
 for lo,hi,label in [(250,350,'250-350 K'),(225,375,'225-375 K'),(270,330,'270-330 K')]:
  pp=m.y_pred_TC.between(lo,hi).astype(int).to_numpy()
  for scope in ['all',*sorted(m.chemistry_family.unique())]:
   mask=np.ones(len(m),bool) if scope=='all' else m.chemistry_family.eq(scope).to_numpy();targ.append({'model':name,'prediction_window':label,'scope':scope,'n':mask.sum(),**cls(true[mask],pp[mask])})
 pd.DataFrame(targ).to_csv(OUT/'threshold_targeting_metrics.csv',index=False)
 lr=[];lp=[]
 for f in sorted(d.chemistry_family.unique()):te=np.flatnonzero(d.chemistry_family.eq(f));tr=np.flatnonzero(d.chemistry_family.ne(f));p=fitpred(X,y,g,tr,te,name,a.candidate_budget,42,a.n_jobs);lr.append({'held_out_family':f,'n_test':len(te),'n_test_publications':d.iloc[te].reference_id.nunique(),**reg(y.iloc[te],p)})
 pd.DataFrame(lr).to_csv(OUT/'leave_family_out_metrics.csv',index=False)
 refs=m.reference_id.unique();rng=np.random.default_rng(42);bs=[]
 for _ in range(10000):z=pd.concat([m[m.reference_id.eq(r)] for r in rng.choice(refs,len(refs),replace=True)]);bs.append(reg(z.TC,z.y_pred_TC))
 bs=pd.DataFrame(bs);obs=reg(m.TC,m.y_pred_TC);pd.DataFrame([{'metric':k,'observed':obs[k],'cluster_bootstrap_95pct_low':bs[k].quantile(.025),'cluster_bootstrap_95pct_high':bs[k].quantile(.975),'n_bootstrap':10000,'cluster_unit':'reference_id'} for k in obs]).to_csv(OUT/'publication_cluster_bootstrap.csv',index=False)
 (OUT/'analysis_audit.json').write_text(json.dumps({'best_model':name,'repeat_seeds':list(range(5)),'candidate_budget':a.candidate_budget},indent=2))
if __name__=='__main__':main()
