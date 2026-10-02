#!/usr/bin/env python3
"""Direct nested publication-grouped classification for 250--350 K."""
from pathlib import Path
import argparse,json,os
import numpy as np,pandas as pd
from lightgbm import LGBMClassifier
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingClassifier,RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix,matthews_corrcoef,make_scorer
from sklearn.model_selection import GridSearchCV,ParameterGrid,ParameterSampler,StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from publication_grouped_analysis import HEA_FEATURES
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'results/strict_tc_audit/strict_experimental_tc_79.csv';OUT=ROOT/'results/strict_tc_classification'
def met(y,p):
 tn,fp,fn,tp=confusion_matrix(y,p,labels=[0,1]).ravel();pre=tp/(tp+fp) if tp+fp else 0;rec=tp/(tp+fn);spec=tn/(tn+fp);return {'tp':tp,'tn':tn,'fp':fp,'fn':fn,'precision':pre,'recall':rec,'specificity':spec,'balanced_accuracy':(rec+spec)/2,'f1':2*pre*rec/(pre+rec) if pre+rec else 0,'mcc':matthews_corrcoef(y,p),'enrichment':pre/np.mean(y) if sum(p) else np.nan}
def specs():return {
 'Logistic':(Pipeline([('scale',StandardScaler()),('clf',LogisticRegression(max_iter=10000,class_weight='balanced',random_state=42))]),{'clf__C':np.logspace(-4,4,41).tolist()}),
 'SVC':(Pipeline([('scale',StandardScaler()),('clf',SVC(class_weight='balanced',random_state=42))]),{'clf__C':[.1,.3,1,3,10,30,100,300],'clf__gamma':['scale',.003,.01,.03,.1,.3,1],'clf__kernel':['rbf']}),
 'RandomForest':(Pipeline([('clf',RandomForestClassifier(class_weight='balanced',random_state=42,n_jobs=1))]),{'clf__n_estimators':[100,200,400,600],'clf__max_depth':[None,3,5,10,20],'clf__min_samples_leaf':[1,2,3,5],'clf__max_features':['sqrt',.8,1.0]}),
 'GradientBoosting':(Pipeline([('clf',GradientBoostingClassifier(random_state=42))]),{'clf__n_estimators':[50,100,200,400],'clf__learning_rate':[.01,.03,.1,.3],'clf__max_depth':[1,2,3,4],'clf__min_samples_leaf':[1,2,3]}),
 'LightGBM':(Pipeline([('clf',LGBMClassifier(random_state=42,n_jobs=1,verbosity=-1,class_weight='balanced'))]),{'clf__n_estimators':[50,100,200,400],'clf__learning_rate':[.01,.03,.1],'clf__num_leaves':[3,7,15,31],'clf__min_child_samples':[3,5,10,20],'clf__subsample':[.7,1.0],'clf__colsample_bytree':[.7,1.0]})}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate-budget',type=int,default=30);ap.add_argument('--n-jobs',type=int,default=max(1,min(8,os.cpu_count() or 1)));a=ap.parse_args();OUT.mkdir(parents=True,exist_ok=True);d=pd.read_csv(DATA);X=d[HEA_FEATURES];y=d.TC.between(250,350).astype(int);g=d.reference_id.astype(str).to_numpy();outer=list(StratifiedGroupKFold(10,shuffle=True,random_state=42).split(X,y,g));rows=[];fo=[];oo=[]
 for mi,(name,(est,grid)) in enumerate(specs().items()):
  pred=np.full(len(d),-1)
  sampled=[{k:[v] for k,v in z.items()} for z in ParameterSampler(grid,n_iter=min(a.candidate_budget,len(list(ParameterGrid(grid)))),random_state=42+17*mi)]
  for fold,(tr,te) in enumerate(outer,1):
   inner=list(StratifiedGroupKFold(5,shuffle=True,random_state=42+fold).split(X.iloc[tr],y.iloc[tr],g[tr]));s=GridSearchCV(clone(est),sampled,scoring=make_scorer(matthews_corrcoef),cv=inner,n_jobs=a.n_jobs,refit=True,error_score=np.nan).fit(X.iloc[tr],y.iloc[tr],groups=g[tr]);pred[te]=s.predict(X.iloc[te]);fo.append({'model':name,'fold':fold,'n_test':len(te),**met(y.iloc[te],pred[te])})
  rows.append({'model':name,'candidate_budget':min(a.candidate_budget,len(list(ParameterGrid(grid)))),'n':79,'n_publications':26,**met(y,pred)})
  for i in range(len(d)):oo.append({'model':name,'source_row':d.iloc[i].source_row,'reference_id':d.iloc[i].reference_id,'target':y.iloc[i],'prediction':pred[i]})
 pd.DataFrame(rows).sort_values(['mcc','balanced_accuracy'],ascending=False).to_csv(OUT/'direct_classifier_summary.csv',index=False);pd.DataFrame(fo).to_csv(OUT/'direct_classifier_fold_metrics.csv',index=False);pd.DataFrame(oo).to_csv(OUT/'direct_classifier_oof.csv',index=False);(OUT/'analysis_audit.json').write_text(json.dumps({'target':'250 <= TC <= 350 K','outer_splits':10,'inner_splits':5,'group':'reference_id','candidate_budget':a.candidate_budget},indent=2))
if __name__=='__main__':main()
