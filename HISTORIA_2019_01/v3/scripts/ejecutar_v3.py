"""V3 autorizado: variables, confirmación y combinación; octubre inaccesible."""
from pathlib import Path
import sys,json,hashlib,os,time,shutil,fcntl,traceback,tarfile,gc
import numpy as np
import polars as pl
import lightgbm as lgb
from sklearn.metrics import roc_auc_score
from auditar_v3 import ROOT,V2,ID,MONTH,LABEL,TRAIN,sha,save,main as build
sys.path.insert(0,str(V2/'vendor'))
from historia import lgb_params
OUT=ROOT/'resultados';ART=ROOT/'artefactos'
class BudgetExceeded(RuntimeError):pass

def policy(ids,y,p,window=2001):
 ids,y,p=np.asarray(ids),np.asarray(y),np.asarray(p)
 if len(y)<window or window%2!=1 or len(set(ids.tolist()))!=len(ids):raise ValueError('Ventana o claves invalidas')
 if len(ids)!=len(p) or not np.isfinite(p).all() or not np.isin(y,[0,1]).all():raise ValueError('Scores/target invalidos')
 order=np.lexsort((ids,-p));g=np.cumsum(np.where(y[order]==1,1072500.,-27500.));cs=np.r_[0.,np.cumsum(g)]
 sm=(cs[window:]-cs[:-window])/window;i=int(np.argmax(sm));k=i+window//2+1
 return {'gain_smoothed':float(sm[i]),'n_send':k,'fraction':k/len(y),'gain_at_n':float(g[k-1]),'window':window}
def gain_at(ids,y,p,k):
 order=np.lexsort((ids,-p));return float(np.where(y[order[:k]]==1,1072500.,-27500.).sum())
def bootstrap(ids,y,a,b,reps,seed,window,check=lambda:None):
 oa=np.lexsort((ids,-a));ob=np.lexsort((ids,-b));n=len(y);rng=np.random.default_rng(seed);ds=[]
 def best(order,w):
  yy=np.repeat(y[order],w[order]);g=np.cumsum(np.where(yy==1,1072500.,-27500.));cs=np.r_[0.,np.cumsum(g)]
  return ((cs[window:]-cs[:-window])/window).max()
 for _ in range(reps):
  check();w=np.bincount(rng.integers(n,size=n),minlength=n);ds.append(float(best(oa,w)-best(ob,w)))
 return {'replicas_validas':len(ds),'seed':seed,'ci90':np.quantile(ds,[.05,.95]).tolist(),'method':'paired_clients_with_multiplicity_reoptimized_full_window'}
def verdict(dg,da,ci,ensemble):
 if np.mean(dg)>np.std(dg,ddof=1) and np.mean(np.asarray(dg)>0)>=.8 and ci[0]>0 and ensemble>0:return 'APORTA'
 if np.mean(dg)>0 and np.median(dg)>0 and np.mean(np.asarray(dg)>0)>=.6:return 'INDICIO_ECONOMICO'
 if np.mean(np.asarray(da)>0)>=.8:return 'INDICIO_AUC'
 return 'NO_APORTA'
def log(s):print(time.strftime('%Y-%m-%dT%H:%M:%S%z'),s,flush=True)
def bytesha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def identity_hash(d):return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()

class Run:
 def __init__(self):
  self.cfg=json.loads((ROOT/'configuraciones/protocolo.json').read_text())
  assert not self.cfg['october_authorized'] and not self.cfg['reoptimization'] and not self.cfg['temporal_june']
  self.start=time.time();self.deadline=self.start+self.cfg['max_hours']*3600
  self.state('AUDITANDO')
  frame,audit=build(False)
  assert audit['arm_new_columns']==self.cfg['new_columns'],'Receta de cobertura diferente de la aprobada'
  assert audit['dataset_sha256']==self.cfg['dataset_sha256']
  assert max(frame[MONTH])==201908,'Octubre bloqueado'
  self.frame=frame;self.train=frame.filter(pl.col(MONTH).is_in(TRAIN));self.valid=frame.filter(pl.col(MONTH)==201908)
  self.ids=self.valid[ID].to_numpy();self.y=(self.valid[LABEL]=='BAJA+2').to_numpy().astype(np.int8)
  self.yt=self.train[LABEL].is_in(['BAJA+1','BAJA+2']).to_numpy().astype(np.int8)
  old=json.loads((V2/'resultados/B4/recipe.json').read_text());self.oldrecipe=old
  assert old['train_months']==TRAIN and old['validation']==201908 and old['target_train']=='BAJA+1+BAJA+2' and old['target_validation']=='BAJA+2'
  assert old['hyperparams']==self.cfg['hyperparams'] and old['seeds']==self.cfg['seeds']
  self.base=old['columns'];assert len(self.base)==588
  self.columns={'C0':self.base,**{k:self.base+v for k,v in self.cfg['new_columns'].items()}}
  hp=lgb_params(self.cfg,self.cfg['hyperparams']['params'],101);assert hp['bagging_freq']>0 and hp['deterministic']
  identity={'dataset':self.cfg['dataset_sha256'],'config':sha(ROOT/'configuraciones/protocolo.json'),'code':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'scripts').glob('*.py'))},'vendor':{p:sha(V2/'vendor'/p) for p in ['historia.py','historia_features.py','historia_metrics.py']},'control_recipe':sha(V2/'resultados/B4/recipe.json'),'ids_train':bytesha(self.train[ID].to_numpy()),'months_train':bytesha(self.train[MONTH].to_numpy()),'labels_train':bytesha(self.yt),'ids_validation':bytesha(self.ids),'labels_validation':bytesha(self.y),'versions':{'numpy':np.__version__,'polars':pl.__version__,'lightgbm':lgb.__version__},'octubre_abierto':False}
  self.identity=identity_hash(identity);identity['identity']=self.identity
  path=ROOT/'manifiestos/identidad.json'
  if path.exists():assert json.loads(path.read_text())==identity,'Identidad diferente: no reanudar'
  else:save(path,identity)
  # Wall-clock budget remains fixed on same-identity restarts, including downtime.
  budget=OUT/'presupuesto.json'
  if budget.exists():
   b=json.loads(budget.read_text());assert b['identity']==self.identity;self.start=b['started'];self.deadline=b['deadline']
  else:save(budget,{'identity':self.identity,'started':self.start,'deadline':self.deadline,'max_hours':self.cfg['max_hours']})
  self.check();self.results={};self.comparisons={};self.registry={};self.milestones=[]
  save(ROOT/'auditoria/preflight_ejecucion.json',audit)
 def check(self):
  if time.time()>=self.deadline:raise BudgetExceeded('Limite de 6 horas alcanzado; checkpoints conservados')
 def state(self,s,**extra):save(OUT/'estado.json',{'estado':s,'updated':time.time(),'pid':os.getpid(),'octubre_abierto':False,**extra});log(s)
 def fit(self,name,n):
  self.check();cols=self.columns[name]
  assert len(cols)==len(set(cols)) and not set(cols)&{ID,MONTH,LABEL,'_month_index'}
  recipe={'identity':self.identity,'columns':cols,'hyperparams':self.cfg['hyperparams'],'seeds':self.cfg['seeds']};dig=identity_hash(recipe)
  rp=OUT/name/'recipe.json'
  if rp.exists():assert json.loads(rp.read_text())==recipe,'Receta diferente'
  else:save(rp,recipe)
  art=ART/name;art.mkdir(parents=True,exist_ok=True)
  xt=xv=None;preds=[];infos=[]
  def matrices():
   nonlocal xt,xv
   if xt is None:
    xt=self.train.select(cols).to_numpy().astype(np.float32,copy=False);xv=self.valid.select(cols).to_numpy().astype(np.float32,copy=False)
    assert not np.isinf(xt).any() and not np.isinf(xv).any()
   return xt,xv
  for seed in self.cfg['seeds'][:n]:
   self.check();cp=OUT/name/f'seed_{seed}.json';pp=art/f'seed_{seed}.npz';mp=art/f'seed_{seed}.txt'
   if cp.exists():
    info=json.loads(cp.read_text());assert info['recipe']==dig and info['scores_sha256']==sha(pp) and info['model_sha256']==sha(mp),'Checkpoint corrupto'
    with np.load(pp,allow_pickle=False) as z:assert np.array_equal(z['ids'],self.ids);pv=z['prediction']
   else:
    self.state('ENTRENANDO',arm=name,seed=seed);t=time.time();xtrain,xvalid=matrices();source='entrenamiento_v3'
    oldcp=V2/'resultados/B4'/f'seed_{seed}.json'
    if name=='C0' and oldcp.exists():
     oldinfo=json.loads(oldcp.read_text());oldpp=oldcp.with_suffix('.npz');oldmp=oldcp.with_suffix('.txt')
     assert oldinfo['recipe']==identity_hash(self.oldrecipe) and oldinfo['scores_sha256']==sha(oldpp) and oldinfo['model_sha256']==sha(oldmp),'Control v2 corrupto'
     with np.load(oldpp,allow_pickle=False) as z:assert np.array_equal(z['ids'],self.ids);pv=z['prediction']
     model=lgb.Booster(model_file=str(oldmp));actual=model.predict(xvalid,num_threads=4)
     assert np.array_equal(actual,pv),'Predicciones B4 no reproducibles con matriz actual'
     assert abs(roc_auc_score(self.y,pv)-oldinfo['auc'])<1e-12
     assert policy(self.ids,self.y,pv)['gain_smoothed']==oldinfo['gain']['gain_smoothed']
     shutil.copy2(oldmp,mp.with_suffix('.tmp'));mp.with_suffix('.tmp').replace(mp)
     source='v2_validado_hash_receta_claves_modelo_y_prediccion_exacta';del model
    else:
     params=lgb_params(self.cfg,self.cfg['hyperparams']['params'],seed)
     ds=lgb.Dataset(xtrain,label=self.yt,feature_name=[f'f{i}' for i in range(len(cols))])
     def budget_callback(env):self.check()
     budget_callback.order=0;budget_callback.before_iteration=True
     model=lgb.train(params,ds,num_boost_round=self.cfg['hyperparams']['rounds'],callbacks=[budget_callback]);pv=model.predict(xvalid,num_threads=4)
     model.save_model(str(mp.with_suffix('.tmp')));mp.with_suffix('.tmp').replace(mp);del ds,model
    assert np.isfinite(pv).all()
    with pp.with_suffix('.tmp').open('wb') as f:np.savez_compressed(f,ids=self.ids,prediction=pv)
    pp.with_suffix('.tmp').replace(pp)
    info={'seed':seed,'recipe':dig,'source':source,'model_sha256':sha(mp),'scores_sha256':sha(pp),'auc':float(roc_auc_score(self.y,pv)),'gain':policy(self.ids,self.y,pv),'seconds':time.time()-t}
    save(cp,info);log(f'{name} seed {seed}: AUC={info["auc"]:.6f}, G={info["gain"]["gain_smoothed"]:.0f} ({source})')
   preds.append(pv);infos.append(info)
  pa=np.asarray(preds);summary={'name':name,'n_seeds':n,'n_features':len(cols),'auc_ensemble':float(roc_auc_score(self.y,pa.mean(0))),'gain_ensemble':policy(self.ids,self.y,pa.mean(0)),'seeds':infos}
  save(OUT/name/f'resultado_{n}.json',summary);self.results[(name,n)]=pa;del xt,xv;gc.collect();return pa
 def compare(self,a,b,n):
  # Deduplicate exact recipes, including a single-family combination against C0.
  key=identity_hash([self.columns[a],self.columns[b]])
  if (key,n) in self.comparisons:return self.comparisons[(key,n)]
  if self.columns[a]==self.columns[b]:return {'verdict':'IDENTICO','candidate':a,'control':b}
  self.registry.setdefault(key,{'candidate':a,'control':b,'revisions':[]})
  if n not in self.registry[key]['revisions']:self.registry[key]['revisions'].append(n)
  assert len(self.registry)<=self.cfg['max_unique_contrasts'],'Presupuesto de contrastes agotado'
  self.state('COMPARANDO',candidate=a,control=b,n_seeds=n)
  pa=self.results[(a,n)];pb=self.results[(b,n)];path=OUT/'comparaciones'/f'{a}_vs_{b}_{n}.json'
  digest=identity_hash({'identity':self.identity,'a':bytesha(pa),'b':bytesha(pb),'n':n,'contrast':key})
  if path.exists():
   d=json.loads(path.read_text());assert d['identity']==digest
  else:
   ga=np.array([policy(self.ids,self.y,p)['gain_smoothed'] for p in pa]);gb=np.array([policy(self.ids,self.y,p)['gain_smoothed'] for p in pb]);dg=ga-gb
   da=np.array([roc_auc_score(self.y,p) for p in pa])-np.array([roc_auc_score(self.y,p) for p in pb]);ea=pa.mean(0);eb=pb.mean(0)
   ma=policy(self.ids,self.y,ea);mb=policy(self.ids,self.y,eb);de=ma['gain_smoothed']-mb['gain_smoothed']
   boot=bootstrap(self.ids,self.y,ea,eb,self.cfg['bootstrap_replicas'],self.cfg['bootstrap_seed'],self.cfg['window'],self.check)
   d={'identity':digest,'candidate':a,'control':b,'n_seeds':n,'delta_gain':dg.tolist(),'delta_gain_mean':float(dg.mean()),'delta_gain_median':float(np.median(dg)),'delta_gain_std':float(dg.std(ddof=1)),'wins_gain':int((dg>0).sum()),'delta_auc':da.tolist(),'delta_auc_mean':float(da.mean()),'delta_auc_median':float(np.median(da)),'delta_auc_std':float(da.std(ddof=1)),'wins_auc':int((da>0).sum()),'delta_ensemble':de,'bootstrap':boot,'diagnostic_same_control_cut':{'k':mb['n_send'],'delta_point_gain':gain_at(self.ids,self.y,ea,mb['n_send'])-gain_at(self.ids,self.y,eb,mb['n_send'])},'verdict':verdict(dg,da,boot['ci90'],de),'confirmed':n==20}
   save(path,d)
  self.comparisons[(key,n)]=d;save(OUT/'registro_contrastes.json',list(self.registry.values()));log(f'{a}-{b} n={n}: {d["verdict"]}; dG={d["delta_gain_mean"]:.0f}')
  return d
 def milestone(self,name):
  self.milestones.append(name);save(OUT/'hitos.json',{'completed':self.milestones,'last':name,'identity':self.identity})
  # Only explicit aggregate JSON/text; no customer arrays, models, logs or credentials.
  dest=Path('/tmp/historia_v3_agregados.tar.gz');tmp=dest.with_suffix('.tmp')
  with tarfile.open(tmp,'w:gz') as t:
   for folder in ['resultados','manifiestos','auditoria','configuraciones']:
    for p in sorted((ROOT/folder).rglob('*.json')):t.add(p,arcname=str(p.relative_to(ROOT)))
  tmp.chmod(0o644);tmp.replace(dest)
  log('HITO_EXPORTADO '+name)
 def execute(self):
  for arm in ['C0','A','B','C','D']:self.fit(arm,5)
  screen={tuple(c):self.compare(*c,5) for c in self.cfg['contrasts']};self.milestone('screening')
  interested={'APORTA','INDICIO_ECONOMICO','INDICIO_AUC'}
  promote={a for (a,b),d in screen.items() if d['verdict'] in interested}
  if 'B' in promote:promote.add('A')
  final='C0';n=5
  if promote:
   n=20
   for arm in ['C0','A','B','C','D']:
    if arm=='C0' or arm in promote:self.fit(arm,20)
   confirm={tuple(c):self.compare(*c,20) for c in self.cfg['contrasts'] if c[0] in promote}
   self.milestone('confirmacion')
   def contributes(a,b):return confirm.get((a,b),{}).get('verdict')=='APORTA'
   ranking='B' if contributes('B','A') and contributes('B','C0') else ('A' if contributes('A','C0') else None)
   choices=[a for a in [ranking,'C' if contributes('C','C0') else None,'D' if contributes('D','C0') else None] if a]
   for i,arm in enumerate(choices,1):
    new=self.columns[final]+[c for c in self.columns[arm] if c not in self.columns[final]]
    if new==self.columns[final]:continue
    if new==self.columns[arm]:candidate=arm
    else:
     candidate=f'COMPUESTO_{i}';self.columns[candidate]=new;self.fit(candidate,20)
    result=self.compare(candidate,final,20)
    if result['verdict']=='APORTA':final=candidate
   if final!='C0' and self.compare(final,'C0',20)['verdict']!='APORTA':final='C0'
   self.milestone('combinaciones')
  result=json.loads((OUT/final/f'resultado_{n}.json').read_text())
  freeze={'estado':'CANDIDATA_CONGELADA_OCTUBRE_PENDIENTE','candidate':final,'n_seeds':n,'columns':self.columns[final],'hyperparams':self.cfg['hyperparams'],'seeds':self.cfg['seeds'][:n],'contact_fraction_ensemble':result['gain_ensemble']['fraction'],'contact_fraction_per_seed':{str(d['seed']):d['gain']['fraction'] for d in result['seeds']},'identity':self.identity,'artifacts':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ART/final).glob('*')) if p.suffix in ['.txt','.npz']},'octubre_abierto':False,'BOF':'PENDIENTE_EQUIVALENCIA_588_760','reoptimization':'NO_PRESUPUESTADA','temporal_june':'NO_PRESUPUESTADO','seconds_total':time.time()-self.start,'unique_contrasts':len(self.registry),'limits':'Agosto ya seleccionado en v2/v3; bootstrap condicional, sin control formal de multiplicidad; no es test independiente.'}
  save(ROOT/'manifiestos/FINAL.json',freeze);self.state('FINALIZADO',candidate=final,n_seeds=n);self.milestone('cierre')

def main():
 OUT.mkdir(exist_ok=True);ART.mkdir(exist_ok=True);lock=(OUT/'ejecucion.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 r=None
 try:r=Run();r.execute()
 except Exception as e:
  save(OUT/'estado.json',{'estado':'PAUSADO_PRESUPUESTO' if isinstance(e,BudgetExceeded) else 'ERROR','error':str(e),'octubre_abierto':False,'updated':time.time()});traceback.print_exc()
  if r is not None:r.milestone('pausa_presupuesto' if isinstance(e,BudgetExceeded) else 'error')
  raise
if __name__=='__main__':main()
