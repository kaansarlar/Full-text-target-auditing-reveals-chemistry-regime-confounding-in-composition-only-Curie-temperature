#!/usr/bin/env python3
from pathlib import Path
import matplotlib.pyplot as plt,numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'figures'
models=pd.read_csv(ROOT/'results/strict_tc_grouped_cv/strict_model_summary.csv');repeats=pd.read_csv(ROOT/'results/strict_tc_robustness/repeated_partition_metrics.csv');family=pd.read_csv(ROOT/'results/strict_tc_robustness/within_family_metrics.csv')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.2,'axes.titlesize':9.3,'axes.labelsize':8.4,'xtick.labelsize':7.3,'ytick.labelsize':7.3})
blue,orange,green,gray,red='#4472C4','#ED7D31','#70AD47','#A5A5A5','#C0504D';fig,axes=plt.subplots(2,2,figsize=(7.15,6.2),dpi=180)
ax=axes[0,0];labels=['Strict experimental $T_C$','Néel temperature','Secondary-source only','Proxy temperature','State ambiguous','Other non-Curie','Conflict'];vals=[79,21,18,7,7,6,3];cols=[green,red,orange,gray,gray,gray,gray];left=0
for lab,v,c in zip(labels,vals,cols):ax.barh(['141 audited records'],v,left=left,height=.42,color=c,label=f'{lab} ({v})');left+=v
ax.text(39.5,0,'79',ha='center',va='center',color='white',fontweight='bold');ax.set_xlim(0,141);ax.set_xlabel('Records');ax.set_title('(a) Full-text target audit',loc='left',fontweight='bold');ax.legend(frameon=False,fontsize=6.4,ncol=2,loc='upper center',bbox_to_anchor=(.5,-.25));ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0)
ax=axes[0,1];order=['SVR','Ridge','LightGBM','RandomForest','XGBoost','GradientBoosting','DummyMean'];m=models.set_index('model').loc[order];bars=ax.bar(range(7),m.oof_r2,color=[blue,orange,green,gray,gray,gray,gray]);ax.axhline(0,color='black',lw=.7);ax.set_ylabel('Publication-grouped OOF $R^2$');ax.set_xticks(range(7),['SVR','Ridge','LGBM','RF','XGB','GBR','Dummy'],rotation=32,ha='right');ax.set_title('(b) Equal-budget strict-cohort models',loc='left',fontweight='bold')
for b,v in zip(bars,m.oof_r2):ax.text(b.get_x()+b.get_width()/2,v+(.025 if v>=0 else -.035),f'{v:.2f}',ha='center',va='bottom' if v>=0 else 'top',fontsize=6.8)
ax.spines[['top','right']].set_visible(False)
ax=axes[1,0];x=np.arange(len(repeats));ax.plot(x,repeats.r2,'o-',color=blue,label='SVR');ax.plot(x,repeats.family_mean_r2,'s--',color=orange,label='Training-only family mean');ax.axhline(0,color='black',lw=.7);ax.set_xticks(x,repeats.seed.astype(int));ax.set_xlabel('Grouped partition seed');ax.set_ylabel('OOF $R^2$');ax.set_title('(c) Partition sensitivity',loc='left',fontweight='bold');ax.legend(frameon=False,fontsize=7);ax.spines[['top','right']].set_visible(False)
ax=axes[1,1];f=family.set_index('chemistry_family').loc[['3d-TM','RE-rich','TM-metalloid']];bars=ax.bar(range(3),f.model_r2,color=[blue,green,orange]);ax.axhline(0,color='black',lw=.7);ax.set_ylabel('Within-family OOF $R^2$');ax.set_xticks(range(3),['3d-TM','RE-rich','TM–metalloid'],rotation=18,ha='right');ax.set_title('(d) Fixed-partition within-family skill',loc='left',fontweight='bold');ax.set_ylim(-2.15,.5);ax.spines[['top','right']].set_visible(False)
for b,v in zip(bars,f.model_r2):ax.text(b.get_x()+b.get_width()/2,v+(.05 if v>=0 else -.08),f'{v:.2f}',ha='center',va='bottom' if v>=0 else 'top',fontsize=7)
for ax in axes.flat:ax.grid(axis='y',alpha=.18,lw=.5)
fig.tight_layout(w_pad=1.8,h_pad=2.5);fig.savefig(OUT/'figure8_strict_tc_v34.png',dpi=400,bbox_inches='tight');fig.savefig(OUT/'figure8_strict_tc_v34.pdf',bbox_inches='tight');plt.close(fig)
