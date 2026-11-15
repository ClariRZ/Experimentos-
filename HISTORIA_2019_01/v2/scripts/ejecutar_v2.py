"""HISTORIA v2: ejecución por etapas, checkpoints y octubre sellado.
La fase inicial entrena la escalera identificable con HP comunes de B4.
No importa ni ejecuta el pipeline de v1 ni evalúa octubre.
"""
from pathlib import Path
import sys,json,time,hashlib,gc,os,traceback
import numpy as np
import polars as pl
import lightgbm as lgb
from sklearn.metrics import roc_auc_score
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from historia_features import load_and_audit,add_lags_deltas,ID,MONTH,LABEL
from historia import optimize,Budget,lgb_params
from historia_metrics import diagnostic_plateau

def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp')
 tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def log(s):print(time.strftime('%Y-%m-%d %H:%M:%S'),s,flush=True)
def policy(ids,y,p,window=2001):return diagnostic_plateau(ids,y,p,window,1072500,-27500)

def coverage(frame,cols):
 return {int(m):dict(zip(cols,frame.filter(pl.col(MONTH)==m).select([pl.col(c).is_finite().fill_null(False).mean() for c in cols]).row(0))) for m in [201903,201904,201905,201906,201908]}

def bootstrap_pair(ids,y,a,b,reps,seed,window=2001):
 rng=np.random.default_rng(seed);n=len(y);dg=[];da=[]
 # Mismos clientes remuestreados para ambos modelos; se reelige el corte en cada réplica.
 oa=np.lexsort((ids,-a));ob=np.lexsort((ids,-b))
 def smooth_for_order(order,w):
  yy=np.repeat(y[order],w[order]);g=np.cumsum(np.where(yy==1,1072500.,-27500.));s=np.r_[0.,np.cumsum(g)]
  return float(((s[window:]-s[:-window])/window).max())
 for i in range(reps):
  w=np.bincount(rng.integers(n,size=n),minlength=n)
  if len(np.unique(y[w>0]))<2:raise ValueError('Bootstrap sin ambas clases')
  dg.append(smooth_for_order(oa,w)-smooth_for_order(ob,w))
  da.append(roc_auc_score(y,a,sample_weight=w)-roc_auc_score(y,b,sample_weight=w))
 return {'replicas':reps,'semilla':seed,'delta_gain_ci90':np.quantile(dg,[.05,.95]).tolist(),'delta_auc_ci90':np.quantile(da,[.05,.95]).tolist(),'method':'paired_client_resampling_reoptimize_smoothed_cut'}

def compare(out,name,control,ids,y,pa,pb,reps=1000):
 assert pa.shape==pb.shape and pa.shape[1]==len(y)
 target=out/'comparaciones'/f'{name}_vs_{control}_{len(pa)}semillas.json'
 recipe=hashlib.sha256(pa.tobytes()+pb.tobytes()+y.tobytes()).hexdigest()
 if target.exists():
  d=json.loads(target.read_text());assert d['recipe']==recipe;return d
 ga=np.array([policy(ids,y,p)['gain_smoothed'] for p in pa]);gb=np.array([policy(ids,y,p)['gain_smoothed'] for p in pb]);delta=ga-gb
 auca=np.array([roc_auc_score(y,p) for p in pa]);aucb=np.array([roc_auc_score(y,p) for p in pb]);boot=bootstrap_pair(ids,y,pa.mean(0),pb.mean(0),reps,20261110)
 aporta=delta.mean()>delta.std(ddof=1) and np.mean(delta>0)>=.8 and boot['delta_gain_ci90'][0]>0
 verdict='APORTA' if aporta else ('INDICIO' if np.mean(auca>aucb)>=.8 else 'NO APORTA')
 d={'candidate':name,'control':control,'recipe':recipe,'n_seeds':len(pa),'delta_gain_mean':float(delta.mean()),'delta_gain_std':float(delta.std(ddof=1)),'wins_gain':int((delta>0).sum()),'delta_auc_mean':float((auca-aucb).mean()),'wins_auc':int((auca>aucb).sum()),'verdict':verdict,'confirmed':len(pa)==20,**boot}
 save(target,d);log(f'{name} vs {control}: {verdict}, dG={delta.mean():.0f}');return d

class Experiment:
 def __init__(self,frame,raw,cfg,out,identity):
  self.frame,self.raw,self.cfg,self.out,self.identity=frame,raw,cfg,out,identity
  self.train=frame.filter(pl.col(MONTH).is_in([201903,201904,201905,201906]));self.valid=frame.filter(pl.col(MONTH)==201908)
  self.yt=self.train[LABEL].is_in(['BAJA+1','BAJA+2']).to_numpy().astype(np.int8);self.yv=(self.valid[LABEL]=='BAJA+2').to_numpy().astype(np.int8);self.ids=self.valid[ID].to_numpy()
 def fit(self,name,columns,hp,n=5):
  assert len(columns)==len(set(columns)) and not set(columns)&{ID,MONTH,LABEL,'_month_index'}
  folder=self.out/name;folder.mkdir(parents=True,exist_ok=True)
  recipe={'identity':self.identity,'columns':columns,'hyperparams':hp,'train_months':[201903,201904,201905,201906],'validation':201908,'target_train':'BAJA+1+BAJA+2','target_validation':'BAJA+2','seeds':self.cfg['seeds']}
  digest=hashlib.sha256(json.dumps(recipe,sort_keys=True).encode()).hexdigest()
  rp=folder/'recipe.json'
  if rp.exists():assert json.loads(rp.read_text())==recipe,'Receta cambiada'
  else:save(rp,recipe)
  preds=[];xt=None;xv=None;infos=[]
  for seed in self.cfg['seeds'][:n]:
   cp=folder/f'seed_{seed}.json';pp=folder/f'seed_{seed}.npz';mp=folder/f'seed_{seed}.txt'
   if cp.exists():
    d=json.loads(cp.read_text());assert d['recipe']==digest and d['model_sha256']==sha(mp) and d['scores_sha256']==sha(pp)
    with np.load(pp,allow_pickle=False) as z:
     assert np.array_equal(z['ids'],self.ids);pv=z['prediction']
   else:
    if xt is None:
     xt=self.train.select(columns).to_numpy().astype(np.float32,copy=False);xv=self.valid.select(columns).to_numpy().astype(np.float32,copy=False)
     assert not np.isinf(xt).any() and not np.isinf(xv).any()
    t=time.time();ds=lgb.Dataset(xt,label=self.yt,feature_name=[f'f{i}' for i in range(len(columns))])
    model=lgb.train(lgb_params(self.cfg,hp['params'],seed),ds,num_boost_round=hp['rounds']);pv=model.predict(xv)
    assert np.isfinite(pv).all();model.save_model(str(mp));np.savez_compressed(pp,ids=self.ids,prediction=pv)
    d={'seed':seed,'recipe':digest,'model_sha256':sha(mp),'scores_sha256':sha(pp),'auc':float(roc_auc_score(self.yv,pv)),'gain':policy(self.ids,self.yv,pv),'seconds':time.time()-t}
    save(cp,d);log(f'{name} seed {seed}: AUC={d["auc"]:.6f}, G={d["gain"]["gain_smoothed"]:.0f}');del model,ds;gc.collect()
   preds.append(pv);infos.append(d)
  preds=np.asarray(preds);save(folder/f'resultado_{n}.json',{'name':name,'n_features':len(columns),'n_seeds':n,'auc_ensemble':float(roc_auc_score(self.yv,preds.mean(0))),'gain_ensemble':policy(self.ids,self.yv,preds.mean(0)),'seeds':infos})
  del xt,xv;gc.collect();return preds

def main():
 cfg=json.loads((ROOT/'configuraciones/protocolo.json').read_text());out=ROOT/'resultados';out.mkdir(exist_ok=True)
 import fcntl
 lock=(out/'ejecucion.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 save(out/'estado.json',{'estado':'VERIFICANDO_DATOS','pid':os.getpid(),'octubre_abierto':False})
 original=Path(cfg['data']);actual=sha(original)
 assert actual==cfg['expected_data_sha256'],'Dataset diferente del manifiesto original'
 for name,digest in cfg['vendor_sha256'].items():assert sha(ROOT/'vendor'/name)==digest
 identity=hashlib.sha256((sha(ROOT/'configuraciones/protocolo.json')+sha(Path(__file__))+actual).encode()).hexdigest()
 old=out/'identidad.json'
 if old.exists():assert json.loads(old.read_text())['identity']==identity,'Código/config cambió, no reutilizar corrida'
 else:save(old,{'identity':identity,'dataset_sha256':actual,'code_sha256':sha(Path(__file__)),'config_sha256':sha(ROOT/'configuraciones/protocolo.json'),'authorization':'Usuaria: corré dale; ejecución aprobada, octubre fuera de selección'})
 frame,raw,audit=load_and_audit(cfg);table=audit.pop('variables_by_month');pl.DataFrame(table).write_csv(ROOT/'auditoria/calidad_vm_saneada.csv');save(ROOT/'auditoria/auditoria_vm_v2.json',audit)
 assert audit['partitions']['validation']==131887,'Universo de agosto difiere del original'
 log(f'Datos verificados: {audit["partitions"]}')
 frame=add_lags_deltas(frame,raw);derived=[f'{c}__{op}{k}' for c in raw for k in (1,2) for op in ['lag','delta']]
 cov=coverage(frame,derived);save(ROOT/'auditoria/cobertura_saneada_v2.json',cov)
 # Congelar por fuente: todas sus cuatro transformaciones cumplen R2 en TODOS los meses train.
 eligible=[c for c in raw if all(cov[m][f'{c}__{op}{k}']>=.9 for m in [201903,201904,201905,201906] for k in [1,2] for op in ['lag','delta'])]
 if not eligible:raise ValueError('No hay fuentes elegibles')
 arms={'B0':raw.copy()};cols=raw.copy()
 for i,(op,k) in enumerate([('lag',1),('delta',1),('lag',2),('delta',2)],1):cols=cols+[f'{c}__{op}{k}' for c in eligible];arms[f'B{i}']=cols.copy()
 save(ROOT/'configuraciones/escalera_congelada.json',{'raw':raw,'eligible':eligible,'arms':arms,'B5_B12':'NO IDENTIFICABLE en marzo–junio: falta historia anterior a enero','baseline_equivalence':'B4 de v2 restringe derivadas por R2; NO idéntico a 000 de v1 (760). Originales conservadas. HP deben optimizarse para B4 elegible; no reutilizar 304 rondas automáticamente.','bias':'HP comunes optimizados en B4 favorecen a B4; feature_fraction constante cambia regularización efectiva.'})
 save(out/'estado.json',{'estado':'OPTUNA_B4','n_raw':len(raw),'n_eligible':len(eligible),'n_B4':len(arms['B4']),'octubre_abierto':False})
 budget=Budget(out,time.time()+cfg['max_hours']*3600)
 hp=optimize(frame,arms['B4'],cfg,out/'optuna_B4',budget)
 exp=Experiment(frame,raw,cfg,out,identity);preds={}
 save(out/'estado.json',{'estado':'ESCALERA_5_SEMILLAS','octubre_abierto':False})
 for name,columns in arms.items():budget.check();preds[name]=exp.fit(name,columns,hp,5)
 for i in range(1,5):compare(out,f'B{i}',f'B{i-1}',exp.ids,exp.yv,preds[f'B{i}'],preds[f'B{i-1}'],cfg['bootstrap_replicas'])
 # Contrastes secundarios únicos, sin duplicar los adyacentes.
 for a,b in [('B2','B0'),('B3','B0'),('B4','B0'),('B1','B4'),('B2','B4')]:compare(out,a,b,exp.ids,exp.yv,preds[a],preds[b],cfg['bootstrap_replicas'])
 save(out/'estado.json',{'estado':'ESCALERA_COMPLETA_PENDIENTE_FAMILIAS','octubre_abierto':False,'nota':'No es experimento completo. Continuar etapas 2–6 con módulo posterior validado.'})
 log('Escalera inicial completada; octubre sigue sellado.')

if __name__=='__main__':
 try:main()
 except BaseException as e:
  save(ROOT/'resultados/error.json',{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc(),'octubre_abierto':False});raise
