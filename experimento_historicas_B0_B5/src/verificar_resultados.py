"""Auditoría independiente posterior a la evaluación: etiquetas por conjuntos y ganancia."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.metrics import roc_auc_score

p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--results',required=True);p.add_argument('--out',required=True);a=p.parse_args()
rdir=Path(a.results);assert (rdir/'EVALUATED.json').exists(),'No abrir test antes del cierre'
frozen=json.loads((rdir/'FROZEN.json').read_text());end=json.loads((rdir/'EVALUATED.json').read_text());assert frozen['unix_time']<=end['unix_time']
assert frozen['config_sha256']==end['config_sha256']==hashlib.sha256((rdir.parent/'config.json').read_bytes()).hexdigest()
r=pd.read_csv(rdir/'resultados.csv')
keys=pq.read_table(a.data,columns=['numero_de_cliente','foto_mes'],filters=[('foto_mes','>=',201908),('foto_mes','<=',201912)]).to_pandas()
sets={m:set(g.numero_de_cliente) for m,g in keys.groupby('foto_mes')}
def independent_label(m):
 ids=keys.loc[keys.foto_mes==m,'numero_de_cliente'];return pd.DataFrame({'numero_de_cliente':ids,'baja2':[int(i in sets[m+1] and i not in sets[m+2]) for i in ids],'positive':[int(i not in sets[m+1] or i not in sets[m+2]) for i in ids]})
valid=independent_label(201908);test=independent_label(201910);checks=[]
for _,row in r.iterrows():
 e=row.experimento;d=rdir/e;c=json.loads((d/'complete.json').read_text())
 assert hashlib.sha256((d/'model.txt').read_bytes()).hexdigest()==frozen['models'][e]
 assert hashlib.sha256((d/'complete.json').read_bytes()).hexdigest()==frozen['decisions'][e]
 pv=pd.read_parquet(d/'validation_predictions.parquet').merge(valid,on='numero_de_cliente',validate='one_to_one')
 pt=pd.read_parquet(d/'test_predictions.parquet').merge(test,on='numero_de_cliente',validate='one_to_one')
 assert len(pv)==len(valid) and len(pt)==len(test)
 assert pv.prob.notna().all() and pt.prob.notna().all()
 assert ((pt.prob>=0)&(pt.prob<=1)).all()
 assert abs(roc_auc_score(pv.positive,pv.prob)-row.auc_agosto)<1e-12
 v=pv.sort_values(['prob','numero_de_cliente'],ascending=[False,True]);vg=np.r_[0,np.cumsum(1100000*v.baja2.to_numpy()-27500)]
 vk=int(np.argmax(vg));assert vk==c['policy']['validation_k']
 k=int(np.floor(vk/len(valid)*len(test)+.5));assert k==row.contactos
 t=pt.sort_values(['prob','numero_de_cliente'],ascending=[False,True]);hits=int(t.head(k).baja2.sum());gain=1100000*hits-27500*k
 assert hits==row.aciertos_BAJA2 and gain==row.ganancia_octubre
 kc=int(row.contactos_comunes);assert kc==int(np.floor(frozen['common_contact_fraction']*len(test)+.5));assert 1100000*int(t.head(kc).baja2.sum())-27500*kc==row.ganancia_presupuesto_comun_B2
 trials=pd.read_csv(d/'trials.csv');assert (trials.state=='COMPLETE').sum()==20
 assert abs(trials.value.max()-row.auc_agosto)<1e-12
 checks.append({'experimento':e,'verificado':True,'filas_test':len(pt),'contactos':k,'aciertos':hits,'ganancia':gain,'auc':float(row.auc_agosto)})
Path(a.out).write_text(json.dumps({'all_passed':True,'method':'Etiquetas independientes por presencia en conjuntos; ganancia bruta menos costo, orden pandas; hashes de congelación y BO','checks':checks},indent=2))
print('VERIFICACION_INDEPENDIENTE_OK',len(checks),'modelos')
