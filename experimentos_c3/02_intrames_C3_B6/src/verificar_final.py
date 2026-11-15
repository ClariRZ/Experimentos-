"""Verificaciones independientes sobre artefactos finales, sin reentrenar."""
from pathlib import Path
import argparse,json,hashlib,re
import numpy as np,pandas as pd
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--parent-prep',type=Path);a=p.parse_args();r=a.root
read=lambda p:json.loads(p.read_text());checks={};hashes={}
for series in ['B6','C3']:assert read(r/'resultados'/series/'COMPLETE.json')['status']=='completed'
for cp in (r/'resultados').glob('*/*/**/complete.json'):
 d=read(cp);mp=cp.parent/'model.txt';assert hashlib.sha256(mp.read_bytes()).hexdigest()==d['model_sha256'];hashes[str(mp.relative_to(r))]=d['model_sha256']
 text=mp.read_text();trees=len(re.findall(r'^Tree=\d+$',text,re.M))
 if d['arm'].startswith('C3_'):
  assert trees==300
  params=dict(re.findall(r'^\[([^:\n]+): (.*)\]$',text,re.M))
  assert int(params['min_data_in_leaf'])==(2500 if d['arm']=='C3_HOJA2500' else 100)
 else:assert trees==d['trees']
checks['models_verified']=len(hashes)
assert len(hashes)==62
per=pd.read_csv(r/'resultados/C3/por_seed.csv');old=pd.read_csv(r/'referencia_s3/por_seed.csv');control=per[per.arm.eq('C3_CONTROL')].set_index('seed').sort_index();old=old.set_index('seed').sort_index();assert control.index.equals(old.index)
checks['c3_original_gain_by_seed_exact']={str(k):bool(np.array_equal(control['gain_'+str(k)],old['ganancia_'+str(k)])) for k in [10500,11000,11500]}
checks['c3_original_differences']={str(k):{str(s):int(v) for s,v in (control['gain_'+str(k)]-old['ganancia_'+str(k)]).items()} for k in [10500,11000,11500]}
new=read(r/'resultados/C3/ensemble.json')[0];oldens=read(r/'referencia_s3/ensemble.json');checks['c3_ensemble_gain_exact']=all(new['cuts'][str(k)]['ganancia']==oldens['cuts'][str(k)]['ganancia'] for k in [10500,11000,11500])
for arm in ['C3_CONTROL','C3_HOJA2500','C3_INTRAMES']:
 assert len(per[per.arm.eq(arm)])==20
checks['B5_curve_exact']=read(r/'resultados/B6/COMPLETE.json')['B5_curve_exact_match']
for b in read(r/'resultados/B6/comparacion.json'):
 for k,x in b['cuts'].items():assert x['ganancia']==1100000*x['aciertos']-27500*int(k)
for b in read(r/'resultados/C3/ensemble.json'):
 for k,x in b['cuts'].items():assert x['ganancia']==1100000*x['aciertos']-27500*int(k)
checks['economic_identities']=True
if a.parent_prep:
 test=pd.read_parquet(a.parent_prep/'meta_test_sellado.parquet')
 dev=pd.read_parquet(a.parent_prep/'meta_desarrollo.parquet');val=dev[dev.foto_mes.eq(201908)]
 frozen=read(r/'resultados/B6/FROZEN.json')
 assert frozen['config_sha256']==hashlib.sha256((r/'config/protocolo.json').read_bytes()).hexdigest()
 for arm in ['B6_FIJO','B6_BO']:
  dest=r/'resultados/B6'/arm;decision=read(dest/'complete.json');vp=np.load(dest/'validation_scores.npy')
  assert frozen['models'][arm]==decision['model_sha256']
  order=np.lexsort((val.numero_de_cliente.to_numpy(),-vp));g=np.r_[0,np.cumsum(np.where(val.clase_ternaria.to_numpy()[order]=='BAJA+2',1072500,-27500))];k=int(g.argmax())
  assert decision['policy']['validation_k']==k and decision['policy']['fraction']==k/len(val)
 checks['validation_policies_recomputed']=True
 def gain(ids,labels,scores,n):
  order=np.lexsort((np.asarray(ids),-scores));return int(1100000*(np.asarray(labels)[order[:n]]=='BAJA+2').sum()-27500*n)
 for b in read(r/'resultados/B6/comparacion.json'):
  scores=np.load(r/'resultados/B6'/b['arm']/'test_scores.npy')
  for k,x in b['cuts'].items():assert gain(test.numero_de_cliente,test.clase_ternaria,scores,int(k))==x['ganancia']
  assert gain(test.numero_de_cliente,test.clase_ternaria,scores,b['policy_contacts'])==b['policy_gain']
 rows=pd.read_parquet(r/'preparado/c3_filas.parquet');ev=rows[rows.foto_mes.eq(202106)]
 for b in read(r/'resultados/C3/ensemble.json'):
  arm=r/'resultados/C3'/b['arm'];scores=[]
  for d in sorted(arm.iterdir()):
   if d.is_dir() and d.name.isdigit():
    v=np.load(d/'scores.npy');s=read(d/'complete.json');scores.append(v)
    for k,x in s['cuts'].items():assert gain(ev.numero_de_cliente,ev.clase_ternaria,v,int(k))==x['ganancia']
  avg=np.mean(scores,axis=0);saved=np.load(arm/'ensemble_scores.npy');np.testing.assert_allclose(avg,saved,rtol=1e-14,atol=1e-15)
  for k,x in b['cuts'].items():assert gain(ev.numero_de_cliente,ev.clase_ternaria,saved,int(k))==x['ganancia']
 checks['gains_recomputed_from_all_scores']=True
(r/'verificacion_final.json').write_text(json.dumps(checks,indent=2));(r/'modelos_sha256.json').write_text(json.dumps(hashes,indent=2));print(json.dumps(checks,indent=2))
