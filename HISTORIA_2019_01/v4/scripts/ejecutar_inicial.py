"""Ensayo v4 acotado; enero-agosto exclusivamente. Sin evaluador de octubre."""
import argparse, gc, hashlib, importlib.util, json, os, time, traceback
from pathlib import Path
import numpy as np
import polars as pl
import lightgbm as lgb
import optuna
from sklearn.metrics import roc_auc_score
from fe_core import *

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('audit',ROOT/'scripts/01_full_audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
ID='numero_de_cliente';MONTH='foto_mes';LABEL='clase_ternaria';TRAIN=[201903,201904,201905,201906]

def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def trim_columns(train, proposed, priority=()):
 """Exact equality in model Float32 representation; keep finite constant plus NA."""
 keep=[];excluded={};groups={}
 for c in list(priority)+sorted(set(proposed)-set(priority)):
  if c in keep:continue
  s=train[c]
  if s.null_count()==len(s):excluded[c]='all_missing';continue
  if s.n_unique()==1:excluded[c]='constant_including_null_pattern';continue
  sig=int(s.hash(seed=2026).sum())
  duplicate=next((old for old in groups.get(sig,[]) if s.equals(train[old],check_dtypes=False)),None)
  if duplicate:excluded[c]='exact_duplicate_of:'+duplicate;continue
  groups.setdefault(sig,[]).append(c);keep.append(c)
 return keep,excluded

def model_values(df,cols):
 return df.with_columns([pl.when(pl.col(c).cast(pl.Float32,strict=True).is_finite()).then(pl.col(c).cast(pl.Float32,strict=True)).otherwise(None).alias(c) for c in cols])

def prepare(df,cfg,art,out,check):
 audit.validate(df);df,_=audit.normalize_mobile_count(df)
 # tmobile_app is a documented binary field, sometimes inferred as string.
 if not df['tmobile_app'].dtype.is_numeric():df=df.with_columns(pl.col('tmobile_app').cast(pl.Float64,strict=True))
 raw=[c for c in df.columns if c not in [ID,MONTH,LABEL]]
 if any(not df[c].dtype.is_numeric() for c in raw):raise ValueError('Raw nonnumeric field needs explicit mapping')
 df=sanitize_base(df,raw,{int(k):v for k,v in cfg['data']['broken_masks'].items()}).sort([ID,MONTH])
 sources=cfg['data']['history_sources'];assert set(sources)<=set(raw)
 active=pl.col(MONTH).is_in(TRAIN+[201908])
 meta=df.filter(active).select([ID,MONTH,LABEL]);meta.write_parquet(art/'meta.parquet')
 hist=add_baseline_lags_deltas(build_exact_lags(df,sources,2),sources)
 base_names=raw+[f'{c}__{f}' for c in sources for f in ['lag1','lag2','delta1','delta2']]
 base=model_values(hist.filter(active).select([ID,MONTH,*base_names]),base_names)
 assert base.select([ID,MONTH]).equals(meta.select([ID,MONTH]))
 tr=base.filter(pl.col(MONTH).is_in(TRAIN));base_keep,excluded=trim_columns(tr,base_names);del tr
 base=base.select([ID,MONTH,*base_keep]);base.write_parquet(art/'B0.parquet')
 registry={'B0':{'columns':base_keep,'excluded':excluded}}
 check()
 for arm,f1,f3 in [('F1',True,False),('F3',False,True)]:
  w=build_window_families(hist,sources,3,include_f1=f1,include_f2=False,include_f3=f3)
  names=[c for c in w.columns if '__f1_' in c or '__f3_' in c]
  extra=model_values(w.filter(active).select([ID,MONTH,*names]),names)
  assert extra.select([ID,MONTH]).equals(base.select([ID,MONTH]))
  joined=base.hstack(extra.select(names));tr=joined.filter(pl.col(MONTH).is_in(TRAIN))
  kept,excluded=trim_columns(tr,names,base_keep);assert kept[:len(base_keep)]==base_keep
  joined.select([ID,MONTH,*kept]).write_parquet(art/f'{arm}.parquet')
  registry[arm]={'columns':kept,'excluded':excluded}
  del w,extra,joined,tr;gc.collect();check()
 del hist;gc.collect()
 ranks=build_monthly_rankings(df.select([ID,MONTH,*sources]),sources)
 rc=[f'{c}__rk0' for c in sources];ranks=ranks.select([ID,MONTH,*rc])
 current=model_values(ranks.filter(active),rc)
 assert current.select([ID,MONTH]).equals(base.select([ID,MONTH]))
 current=base.hstack(current.select(rc));tr=current.filter(pl.col(MONTH).is_in(TRAIN))
 kept,excluded=trim_columns(tr,rc,base_keep);current=current.select([ID,MONTH,*kept]);current.write_parquet(art/'F4a.parquet');registry['F4a']={'columns':kept,'excluded':excluded};del tr
 ranks=add_baseline_lags_deltas(build_exact_lags(ranks,rc,2),rc)
 ranks=build_window_families(ranks,rc,3,include_f1=True,include_f2=False,include_f3=False)
 names=[c for c in ranks.columns if c not in [ID,MONTH,*rc]]
 extra=model_values(ranks.filter(active).select([ID,MONTH,*names]),names)
 assert extra.select([ID,MONTH]).equals(current.select([ID,MONTH]))
 joined=current.hstack(extra.select(names));tr=joined.filter(pl.col(MONTH).is_in(TRAIN))
 all_kept,excluded=trim_columns(tr,names,kept);assert all_kept[:len(kept)]==kept
 joined.select([ID,MONTH,*all_kept]).write_parquet(art/'F4b.parquet');registry['F4b']={'columns':all_kept,'excluded':excluded}
 # Coverage on train only; no threshold and no selection on validation.
 for arm,entry in registry.items():
  frame=pl.read_parquet(art/f'{arm}.parquet')
  entry['coverage_by_month']=audit.coverage(frame,entry['columns'],TRAIN)
  entry['matrix_file_sha256']=sha(art/f'{arm}.parquet')
  del frame;check()
 save(out/'feature_manifest.json',registry)
 return registry

class Run:
 def __init__(self,args):
  self.cfg=json.loads(args.config.read_text());self.start=time.time();self.deadline=args.deadline
  assert self.cfg['training_authorized'] is True and self.cfg['data']['test_locked_in_initial_stage']
  assert [a['id'] for a in self.cfg['arms']]==['B0','F1','F3','F4a','F4b']
  self.out=args.output;self.out.mkdir(parents=True,exist_ok=False)
  self.art=self.out/'private';self.art.mkdir();self.fits=0;self.results={}
  save(self.out/'config_frozen.json',self.cfg)
  save(self.out/'code_identity.json',{p.name:sha(p) for p in sorted((ROOT/'scripts').glob('*.py'))})
  self.state('PREPARANDO')
  assert sha(args.dataset)==self.cfg['data']['sha256']
  df=pl.scan_csv(args.dataset,infer_schema_length=20000).filter(pl.col(MONTH).is_between(201901,201908)).collect()
  self.registry=prepare(df,self.cfg,self.art,self.out,self.check);del df;gc.collect()
  meta=pl.read_parquet(self.art/'meta.parquet');train=meta.filter(pl.col(MONTH).is_in(TRAIN));valid=meta.filter(pl.col(MONTH)==201908)
  self.yt=train[LABEL].is_in(['BAJA+1','BAJA+2']).to_numpy().astype(np.int8)
  self.yv=(valid[LABEL]=='BAJA+2').to_numpy().astype(np.int8);self.ids=valid[ID].to_numpy()
  assert len(np.unique(self.ids))==len(self.ids) and len(np.unique(self.yv))==2
  save(self.out/'data_identity.json',{'n_train':len(train),'n_valid':len(valid),'train_months':TRAIN,'validation_month':201908,'train_keys_sha256':hashlib.sha256(train.select([ID,MONTH]).to_numpy().tobytes()).hexdigest(),'valid_ids_sha256':hashlib.sha256(self.ids.tobytes()).hexdigest(),'versions':{'lightgbm':lgb.__version__,'polars':pl.__version__,'numpy':np.__version__,'optuna':optuna.__version__},'october_used':False})
 def check(self):
  if time.time()>=self.deadline:raise TimeoutError('Limite de tiempo')
  import shutil
  if shutil.disk_usage(self.out).free<10*2**30:raise RuntimeError('Disco libre menor a 10 GiB')
 def state(self,status,**details):
  save(self.out/'status.json',{'status':status,'fits_started':self.fits,'updated':time.time(),'october_used':False,**details});print(status,details,flush=True)
 def matrices(self,arm):
  df=pl.read_parquet(self.art/f'{arm}.parquet');cols=self.registry[arm]['columns']
  xt=df.filter(pl.col(MONTH).is_in(TRAIN)).select(cols).to_numpy(order='c');xv=df.filter(pl.col(MONTH)==201908).select(cols).to_numpy(order='c')
  assert xt.shape[0]==len(self.yt) and xv.shape[0]==len(self.yv)
  return xt,xv
 def params(self,hp,seed):
  return {**self.cfg['hyperparameter_search']['fixed'],**hp,'seed':seed,'feature_fraction_seed':seed,'bagging_seed':seed,'data_random_seed':seed,'verbosity':-1,'feature_pre_filter':False}
 def fit(self,xt,xv,hp,seed,rounds,early=False):
  self.check();self.fits+=1
  if self.fits>77:raise RuntimeError('Fit cap exceeded')
  ds=lgb.Dataset(xt,label=self.yt,feature_name=[f'f{i}' for i in range(xt.shape[1])]);callbacks=[]
  def cb(env):self.check()
  cb.order=0;cb.before_iteration=True;callbacks.append(cb)
  kwargs={}
  if early:
   callbacks.append(lgb.early_stopping(100,verbose=False));kwargs['valid_sets']=[lgb.Dataset(xv,label=self.yv,reference=ds)]
  start=time.time();m=lgb.train(self.params(hp,seed),ds,num_boost_round=rounds,callbacks=callbacks,**kwargs)
  seconds=time.time()-start;pred=m.predict(xv,num_threads=4);assert np.isfinite(pred).all()
  return m,pred,seconds
 def execute(self):
  self.state('MEDICION');pilots=[]
  for arm in ['B0','F4b']:
   xt,xv=self.matrices(arm);m,p,t=self.fit(xt,xv,self.cfg['budget']['pilot_fixed_parameters'],101,100)
   pilots.append({'arm':arm,'fit_seconds':t,'seconds_per_round':t/100,'columns':xt.shape[1]});del xt,xv,m,p;gc.collect()
  # Max-round projection, 20% margin for dataset construction and exports.
  worst=max(p['seconds_per_round'] for p in pilots)
  projected=75*1500*worst*1.2
  gate={'pilots':pilots,'remaining_seconds':self.deadline-time.time(),'projected_seconds_max_rounds_with_margin':projected,'decision':'CONTINUE' if projected<self.deadline-time.time() else 'PAUSE_BUDGET'}
  save(self.out/'pilot_budget.json',gate)
  if gate['decision']!='CONTINUE':self.state('PAUSADO_PRESUPUESTO',reason='Conservative full-budget projection exceeds remaining cap');return
  for arm in ['B0','F1','F3','F4a','F4b']:
   self.state('OPTUNA',arm=arm);xt,xv=self.matrices(arm);path=self.out/arm;path.mkdir()
   study=optuna.create_study(direction='maximize',sampler=optuna.samplers.TPESampler(seed=20261111,n_startup_trials=5))
   trials=[]
   def objective(trial):
    hp={}
    for name,s in self.cfg['hyperparameter_search']['range'].items():
     fn=trial.suggest_int if s['type']=='int' else trial.suggest_float
     hp[name]=fn(name,s['low'],s['high'],log=s.get('log',False))
    m,p,t=self.fit(xt,xv,hp,101,1500,early=True);auc=float(roc_auc_score(self.yv,p));trial.set_user_attr('rounds',int(m.best_iteration));trials.append({'trial':trial.number,'auc':auc,'params':hp,'rounds':int(m.best_iteration),'seconds':t});save(path/'trials.json',trials);self.state('OPTUNA',arm=arm,trial=trial.number+1,auc=auc);return auc
   study.optimize(objective,n_trials=10)
   best=study.best_trial;save(path/'best.json',{'params':best.params,'rounds':best.user_attrs['rounds'],'trial':best.number,'auc':best.value})
   seeds=[];predictions=[]
   for seed in self.cfg['evaluation']['seeds']:
    self.state('SEMILLAS',arm=arm,seed=seed)
    m,p,t=self.fit(xt,xv,best.params,seed,best.user_attrs['rounds']);private=self.art/arm;private.mkdir(exist_ok=True)
    m.save_model(str(private/f'seed_{seed}.txt'));np.savez_compressed(private/f'seed_{seed}.npz',ids=self.ids,prediction=p)
    seeds.append({'seed':seed,'auc':float(roc_auc_score(self.yv,p)),'gain':evaluate_gain_curve(self.ids,p,self.yv),'seconds':t});predictions.append(p);save(path/'seeds.json',seeds);del m
   ensemble=np.mean(predictions,axis=0)
   result={'arm':arm,'columns':len(self.registry[arm]['columns']),'seeds':seeds,'ensemble_auc':float(roc_auc_score(self.yv,ensemble)),'ensemble_gain':evaluate_gain_curve(self.ids,ensemble,self.yv)}
   save(path/'result.json',result);self.results[arm]=result;del xt,xv,predictions,ensemble;gc.collect()
  comparisons=[]
  for arm,control in [('F1','B0'),('F3','B0'),('F4a','B0'),('F4b','B0'),('F4b','F4a')]:
   a=self.results[arm]['seeds'];b=self.results[control]['seeds'];da=np.array([u['auc']-v['auc'] for u,v in zip(a,b)]);dg=np.array([u['gain']['smoothed_gain_max']-v['gain']['smoothed_gain_max'] for u,v in zip(a,b)])
   comparisons.append({'arm':arm,'control':control,'delta_auc':da.tolist(),'delta_gain':dg.tolist(),'delta_auc_mean':float(da.mean()),'delta_auc_median':float(np.median(da)),'delta_auc_sd':float(da.std(ddof=1)),'auc_wins':int((da>0).sum()),'delta_gain_mean':float(dg.mean()),'delta_gain_median':float(np.median(dg)),'delta_gain_sd':float(dg.std(ddof=1)),'gain_wins':int((dg>0).sum()),'eligible_by_operational_auc_rule':bool(da.mean()>0 and (da>0).sum()>=4)})
  save(self.out/'comparisons.json',comparisons)
  eligible=[a for a in ['F1','F3','F4a','F4b'] if all(c['eligible_by_operational_auc_rule'] for c in comparisons if c['arm']==a)]
  save(self.out/'eligible_candidates.json',{'operational_only':True,'candidates':eligible,'confirmation_pending':True})
  save(self.out/'FINAL.json',{'status':'EXPLORATORIO_COMPLETO','fits':self.fits,'seconds':time.time()-self.start,'october_used':False,'arms':list(self.results),'comparisons':comparisons,'warning':'August reused for development in earlier experiments; five seeds do not establish significance; no test results.'})
  self.state('COMPLETO')

def main():
 p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--deadline',type=float,required=True);args=p.parse_args()
 r=None
 try:r=Run(args);r.execute()
 except Exception as e:
  if args.output.exists():save(args.output/'status.json',{'status':'ERROR_O_LIMITE','error':str(e),'october_used':False,'updated':time.time()})
  traceback.print_exc();raise
if __name__=='__main__':main()
