"""Verificación independiente: recalcular selección, score ensemble y métricas."""
from pathlib import Path
import argparse,json,hashlib,re
import pandas as pd,numpy as np
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);a=p.parse_args();root=a.root;out=root/'resultados'
read=lambda f:json.loads(f.read_text())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
cfg=read(root/'config_propuesta.json');assert len(cfg['seeds'])==len(set(cfg['seeds']))==20;frozen=read(out/'FROZEN.json');assert read(out/'COMPLETE.json')['models']==40
for name,h in frozen['files'].items():assert sha(out/name)==h
assert frozen['signature']['config']==sha(root/'config_propuesta.json')
assert frozen['signature']['manifest']==sha(root/'variables_propuestas.csv')
for name,h in frozen['signature']['sources'].items():assert sha(root/name)==h
val=pd.read_parquet(a.parent/'preparado/meta_desarrollo.parquet');val=val[val.foto_mes.eq(201908)];test=pd.read_parquet(a.parent/'preparado/meta_test_sellado.parquet');summary=pd.read_csv(out/'resumen.csv').set_index('arm');per=pd.read_csv(out/'por_semilla.csv').set_index(['representation','seed']);hashes={}
def gain(meta,scores,k):
 order=np.lexsort((meta.numero_de_cliente.to_numpy(),-scores));hits=int((meta.clase_ternaria.to_numpy()[order[:k]]=='BAJA+2').sum());return 1100000*hits-27500*k
common=int(summary.loc['A','contacts_policy']);all_validation={};all_test={}
for rep,solo,ensemble in [('baseline','A','C'),('enriquecido','B','D')]:
 vs=[];ts=[];chosen=read(out/rep/'BO_COMPLETE.json');assert chosen['completed_trials']==20
 for seed in cfg['seeds']:
  d=out/rep/str(seed);r=read(d/'complete.json');assert r['model_sha256']==sha(d/'model.txt');assert r['scores_sha256']==sha(d/'validation_scores.npy');hashes[str((d/'model.txt').relative_to(root))]=sha(d/'model.txt');text=(d/'model.txt').read_text();assert len(re.findall(r'^Tree=\d+$',text,re.M))==chosen['trees']==r['trees'];pars=dict(re.findall(r'^\[([^:\n]+): (.*)\]$',text,re.M))
  for key in ['seed','bagging_seed','feature_fraction_seed','data_random_seed']:assert int(pars[key])==seed
  v=np.load(d/'validation_scores.npy');t=np.load(d/'test_scores.npy');vs.append(v);ts.append(t);rr=per.loc[(rep,seed)];assert gain(test,t,int(rr.contacts_policy))==int(rr.gain_policy);assert gain(test,t,common)==int(rr.gain_common_A);assert gain(test,t,11000)==int(rr.gain_11000)
 for arm,v,t in [(solo,vs[0],ts[0]),(ensemble,np.mean(vs,axis=0),np.mean(ts,axis=0))]:
  np.testing.assert_array_equal(t,np.load(out/arm/'test_scores.npy'))
  if arm==ensemble:np.testing.assert_array_equal(v,np.load(out/rep/'ensemble_validation.npy'))
  order=np.lexsort((val.numero_de_cliente.to_numpy(),-v));g=np.r_[0,np.cumsum(np.where(val.clase_ternaria.to_numpy()[order]=='BAJA+2',1072500,-27500))];k=int(g.argmax());pol=frozen['arms'][arm]['policy'];assert k==pol['validation_k'];kt=k*len(test)//len(val);r=summary.loc[arm];assert kt==int(r.contacts_policy)
  assert gain(test,t,kt)==int(r.gain_policy);assert gain(test,t,common)==int(r.gain_common_A);assert gain(test,t,11000)==int(r.gain_11000);assert int(r.hits_policy)*1100000-27500*kt==int(r.gain_policy)
# Aggregate replacement analysis at identical contact budgets, without exporting IDs.
selection=[]
for budget in [common,11000]:
 selected={}
 for arm in ['A','B','C','D']:
  scores=np.load(out/arm/'test_scores.npy');order=np.lexsort((test.numero_de_cliente.to_numpy(),-scores));selected[arm]=set(order[:budget].tolist())
 hit=test.clase_ternaria.eq('BAJA+2').to_numpy()
 for left,right in [('B','A'),('C','A'),('D','B'),('D','C'),('D','A')]:
  entered=selected[left]-selected[right];exited=selected[right]-selected[left];hin=sum(int(hit[i]) for i in entered);hout=sum(int(hit[i]) for i in exited)
  selection.append({'comparison':left+'-'+right,'contacts':budget,'retained':len(selected[left]&selected[right]),'entered':len(entered),'exited':len(exited),'BAJA2_entered':hin,'BAJA2_exited':hout,'delta_gain':1100000*(hin-hout)})
pd.DataFrame(selection).to_csv(out/'seleccion.csv',index=False)
assert len(hashes)==40;assert read(out/'B2_REPRODUCED_VALIDATION.json')['exact_scores'];assert read(out/'B2_REPRODUCED_TEST.json')['exact_curve']
oldv=pd.read_parquet(a.parent/'resultados/B2/validation_predictions.parquet');oldt=pd.read_parquet(a.parent/'resultados/B2/test_predictions.parquet')
assert np.array_equal(oldv.numero_de_cliente,val.numero_de_cliente) and np.array_equal(oldt.numero_de_cliente,test.numero_de_cliente)
same_A_validation=bool(np.array_equal(oldv.prob.to_numpy(),np.load(out/'baseline'/str(cfg['single_seed'])/'validation_scores.npy')))
same_A_test=bool(np.array_equal(oldt.prob.to_numpy(),np.load(out/'A/test_scores.npy')))
record={'new_A_equals_historical_B2_validation':same_A_validation,'new_A_equals_historical_B2_test':same_A_test,'models_verified':40,'all_scores_and_gains_recomputed':True,'ensembles_equal_mean_of_20':True,'validation_policies_recomputed':True,'baseline_historical_reproduction':True,'freeze_sha256':sha(out/'FROZEN.json'),'status':'verified'}
(root/'verificacion_final.json').write_text(json.dumps(record,indent=2));(root/'modelos_sha256.json').write_text(json.dumps(hashes,indent=2));print(json.dumps(record,indent=2))
