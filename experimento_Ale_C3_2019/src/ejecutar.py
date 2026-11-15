import argparse,gc,time,pickle,shutil
from pathlib import Path
import numpy as np,pandas as pd,lightgbm as lgb,optuna
from sklearn.metrics import roc_auc_score
from comun import ROOT,read,write,sha,curve,policy,transfer
p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--mode',choices=['train','evaluate'],required=True);a=p.parse_args()
cfg=read(ROOT/'config_propuesta.json');out=ROOT/'resultados';out.mkdir(exist_ok=True);assert len(cfg['seeds'])==len(set(cfg['seeds']))==20;prep=a.parent/'preparado';ready=read(ROOT/'preparado/READY.json');assert ready['parent_manifest_sha256']==sha(prep/'manifest.json');assert ready['extra_sha256']==sha(ROOT/'preparado/extra.npy')
source_hashes={str(f.relative_to(ROOT)):sha(f) for f in sorted((ROOT/'src').glob('*.py')) if f.name in ['comun.py','preparar.py','ejecutar.py']};signature={'config':sha(ROOT/'config_propuesta.json'),'manifest':sha(ROOT/'variables_propuestas.csv'),'sources':source_hashes}
if (out/'RUN_SIGNATURE.json').exists():assert read(out/'RUN_SIGNATURE.json')==signature
else:write(out/'RUN_SIGNATURE.json',signature)
manifest=read(prep/'manifest.json');rows=pd.read_parquet(prep/'filas.parquet');dev=pd.read_parquet(prep/'meta_desarrollo.parquet');tr=rows.foto_mes.isin(cfg['train_months']).to_numpy();va=rows.foto_mes.eq(201908).to_numpy();te=rows.foto_mes.eq(201910).to_numpy();assert rows.loc[tr|va,['numero_de_cliente','foto_mes']].reset_index(drop=True).equals(dev[['numero_de_cliente','foto_mes']])
yt=dev.loc[dev.foto_mes.isin(cfg['train_months']),'clase_ternaria'].isin(cfg['train_and_auc_positive']).astype('int8').to_numpy();vc=dev.loc[dev.foto_mes.eq(201908),'clase_ternaria'].to_numpy();yv=np.isin(vc,cfg['train_and_auc_positive']);vid=rows.loc[va,'numero_de_cliente'].to_numpy();names=sum([manifest['families'][g] for g in ['original','lags','deltas']],[])
extra_names=pd.read_csv(ROOT/'variables_propuestas.csv').variable.tolist()
def matrix(rep,mask):
 arrays=[np.load(prep/(g+'.npy'),mmap_mode='r')[mask] for g in ['original','lags','deltas']]
 if rep=='enriquecido':arrays.append(np.load(ROOT/'preparado/extra.npy',mmap_mode='r')[mask])
 return np.concatenate(arrays,axis=1)
def params(seed):return {'objective':'binary','metric':'auc','verbosity':-1,'num_threads':8,'seed':seed,'bagging_seed':seed,'feature_fraction_seed':seed,'data_random_seed':seed,'bagging_freq':1,'feature_pre_filter':False,'deterministic':True,'force_col_wise':True,'max_bin':255}
def save_model(m,d,cols):
 m.save_model(str(d/'model.txt'));pd.DataFrame({'feature':cols,'gain':m.feature_importance('gain'),'split':m.feature_importance('split')}).to_csv(d/'importance.csv',index=False)
if a.mode=='train':
 if (out/'FROZEN.json').exists():
  assert read(out/'FROZEN.json')['signature']==signature;print('Already frozen');raise SystemExit(0)
 for rep in ['baseline','enriquecido']:
  d=out/rep;d.mkdir(exist_ok=True);cols=names+(extra_names if rep=='enriquecido' else []);cats=[i for i,c in enumerate(cols) if c in manifest['categorical']]
  xt=matrix(rep,tr);xv=matrix(rep,va);pars=params(cfg['single_seed']);ds=lgb.Dataset(xt,label=yt,feature_name=cols,categorical_feature=cats,params=pars,free_raw_data=True);dv=lgb.Dataset(xv,label=yv,reference=ds,feature_name=cols,categorical_feature=cats,free_raw_data=True);ds.construct();dv.construct()
  # A baseline reproduction check on August before opening any test labels.
  if rep=='baseline':
   old=read(a.parent/'resultados/B2/complete.json');assert cols==old['feature_names'];oldmodel=lgb.Booster(model_file=str(a.parent/'resultados/B2/model.txt'));assert sha(a.parent/'resultados/B2/model.txt')==old['model_sha256']
   oldp=oldmodel.predict(xv,num_threads=8);reference=pd.read_parquet(a.parent/'resultados/B2/validation_predictions.parquet');assert np.array_equal(reference.numero_de_cliente,vid);np.testing.assert_allclose(oldp,reference.prob.to_numpy(),rtol=0,atol=0)
   assert policy(vid,vc,oldp)['validation_k']==old['policy']['validation_k'];write(out/'B2_REPRODUCED_VALIDATION.json',{'exact_scores':True,'policy_equal':True,'original_model_sha256':old['model_sha256']});del oldmodel,oldp
  if not (d/'BO_COMPLETE.json').exists():
   sp=cfg['search_space'];sf=d/'sampler.pkl';sampler=pickle.loads(sf.read_bytes()) if sf.exists() else optuna.samplers.TPESampler(seed=cfg['single_seed'],n_startup_trials=cfg['bo_startup_trials'])
   study=optuna.create_study(study_name=rep,direction='maximize',storage='sqlite:///'+str((d/'study.sqlite').resolve()),sampler=sampler,load_if_exists=True)
   # Interrupted trials are explicit failures, not invisible successes.
   for t in study.get_trials(states=(optuna.trial.TrialState.RUNNING,)):study.tell(t.number,state=optuna.trial.TrialState.FAIL)
   def objective(t):
    hp={'num_leaves':t.suggest_int('num_leaves',*sp['num_leaves'],log=True),'learning_rate':t.suggest_float('learning_rate',*sp['learning_rate'],log=True),'min_data_in_leaf':t.suggest_int('min_data_in_leaf',*sp['min_data_in_leaf'],log=True),'feature_fraction':t.suggest_float('feature_fraction',*sp['feature_fraction']),'bagging_fraction':t.suggest_float('bagging_fraction',*sp['bagging_fraction'])}
    start=time.time();m=lgb.train({**pars,**hp},ds,num_boost_round=cfg['max_rounds'],valid_sets=[dv],valid_names=['validation'],callbacks=[lgb.early_stopping(cfg['early_stopping'],first_metric_only=True,verbose=False)]);m.save_model(str(d/f'trial_{t.number}.txt'));t.set_user_attr('best_iteration',m.best_iteration);t.set_user_attr('seconds',time.time()-start);print('TRIAL',rep,t.number,m.best_score['validation']['auc'],m.best_iteration,flush=True);return float(m.best_score['validation']['auc'])
   def checkpoint(study,t):
    tmp=sf.with_suffix('.tmp');tmp.write_bytes(pickle.dumps(study.sampler));tmp.replace(sf)
   n=sum(t.state==optuna.trial.TrialState.COMPLETE for t in study.trials);assert n<=cfg['bo_trials_per_representation'];study.optimize(objective,n_trials=cfg['bo_trials_per_representation']-n,callbacks=[checkpoint]);best=sorted(study.get_trials(states=(optuna.trial.TrialState.COMPLETE,)),key=lambda t:(-t.value,t.number))[0]
   study.trials_dataframe().to_csv(d/'trials.csv',index=False);write(d/'BO_COMPLETE.json',{'best_params':best.params,'trees':best.user_attrs['best_iteration'],'best_trial':best.number,'auc':best.value,'completed_trials':cfg['bo_trials_per_representation']})
  chosen=read(d/'BO_COMPLETE.json');del ds,dv;gc.collect();scores=[]
  for seed in cfg['seeds']:
   dest=d/str(seed);dest.mkdir(exist_ok=True);cp=dest/'complete.json';start=time.time()
   if cp.exists():
    r=read(cp);assert sha(dest/'model.txt')==r['model_sha256'];pred=np.load(dest/'validation_scores.npy');assert sha(dest/'validation_scores.npy')==r['scores_sha256']
   else:
    fixed={**params(seed),**chosen['best_params']};dt=lgb.Dataset(xt,label=yt,feature_name=cols,categorical_feature=cats,params=fixed,free_raw_data=True);m=lgb.train(fixed,dt,num_boost_round=chosen['trees']);pred=m.predict(xv,num_threads=8);save_model(m,dest,cols);np.save(dest/'validation_scores.npy',pred)
    if seed==cfg['single_seed']:
     bm=lgb.Booster(model_file=str(d/f"trial_{chosen['best_trial']}.txt"));np.testing.assert_allclose(pred,bm.predict(xv,num_threads=8),rtol=0,atol=0);del bm
    r={'representation':rep,'seed':seed,'features':len(cols),'trees':m.num_trees(),'params':fixed,'auc_validation':float(roc_auc_score(yv,pred)),'policy':policy(vid,vc,pred),'seconds':time.time()-start,'model_sha256':sha(dest/'model.txt'),'scores_sha256':sha(dest/'validation_scores.npy')};write(cp,r);del dt,m;gc.collect()
   scores.append(pred);print('SEED_DONE',rep,seed,r['auc_validation'],round(r['seconds'],1),flush=True)
  ens=np.mean(scores,axis=0);np.save(d/'ensemble_validation.npy',ens);write(d/'ENSEMBLE.json',{'n_seeds':len(scores),'auc_validation':float(roc_auc_score(yv,ens)),'policy':policy(vid,vc,ens),'scores_sha256':sha(d/'ensemble_validation.npy')});del xt,xv,scores;gc.collect()
 arms={}
 for arm,rep,ensemble in [('A','baseline',False),('B','enriquecido',False),('C','baseline',True),('D','enriquecido',True)]:
  r=read(out/rep/('ENSEMBLE.json' if ensemble else str(cfg['single_seed'])+'/complete.json'));arms[arm]={'representation':rep,'ensemble':ensemble,'auc_validation':r['auc_validation'],'policy':r['policy']}
 files={str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file() and (f.name in ['model.txt','complete.json','BO_COMPLETE.json','ENSEMBLE.json','validation_scores.npy','ensemble_validation.npy'])}
 write(out/'FROZEN.json',{'signature':signature,'unix_time':time.time(),'arms':arms,'files':files,'october_labels_opened_in_this_run':False,'prior_october_exposure':True});print('FROZEN',flush=True)
else:
 frozen=read(out/'FROZEN.json');assert frozen['signature']==signature
 for name,h in frozen['files'].items():assert sha(out/name)==h
 test=pd.read_parquet(prep/'meta_test_sellado.parquet');assert np.array_equal(test.numero_de_cliente,rows.loc[te,'numero_de_cliente']);tid=test.numero_de_cliente.to_numpy();tc=test.clase_ternaria.to_numpy();common=transfer(frozen['arms']['A']['policy'],len(test));per=[];summaries=[]
 for rep,solo,ensarm in [('baseline','A','C'),('enriquecido','B','D')]:
  x=matrix(rep,te);d=out/rep;predictions=[]
  if rep=='baseline':
   oldmodel=lgb.Booster(model_file=str(a.parent/'resultados/B2/model.txt'));oldpred=oldmodel.predict(x,num_threads=8);oldcurve=curve(tid,tc,oldpred);reference=pd.read_csv(a.parent/'resultados/B2/curva_octubre.csv');np.testing.assert_array_equal(oldcurve,reference.ganancia.to_numpy());write(out/'B2_REPRODUCED_TEST.json',{'exact_curve':True,'only_after_frozen':True});del oldmodel
  for seed in cfg['seeds']:
   dest=d/str(seed);m=lgb.Booster(model_file=str(dest/'model.txt'));pred=m.predict(x,num_threads=8);np.save(dest/'test_scores.npy',pred);g=curve(tid,tc,pred);r=read(dest/'complete.json');k=transfer(r['policy'],len(test));per.append({'representation':rep,'seed':seed,'auc_validation':r['auc_validation'],'contacts_policy':k,'gain_policy':int(g[k]),'contacts_common_A':common,'gain_common_A':int(g[common]),'gain_11000':int(g[11000])});predictions.append(pred);del m
  for arm,pred in [(solo,predictions[0]),(ensarm,np.mean(predictions,axis=0))]:
   dest=out/arm;dest.mkdir(exist_ok=True);np.save(dest/'test_scores.npy',pred);r=frozen['arms'][arm];k=transfer(r['policy'],len(test));g=curve(tid,tc,pred)
   summaries.append({'arm':arm,'features':len(names)+(43 if rep=='enriquecido' else 0),'seeds':20 if r['ensemble'] else 1,'auc_validation':r['auc_validation'],'validation_contacts':r['policy']['validation_k'],'contacts_policy':k,'gain_policy':int(g[k]),'hits_policy':int((g[k]+27500*k)//1100000),'contacts_common_A':common,'gain_common_A':int(g[common]),'gain_11000':int(g[11000])})
   pd.DataFrame({'contactos':np.arange(len(g)),'ganancia':g}).to_csv(dest/'curva_octubre.csv',index=False)
  del x,predictions;gc.collect()
 result=pd.DataFrame(summaries).sort_values('arm');result.to_csv(out/'resumen.csv',index=False);pp=pd.DataFrame(per);pp.to_csv(out/'por_semilla.csv',index=False);pairs=[]
 for metric in ['gain_policy','gain_common_A','gain_11000']:
  indexed=result.set_index('arm')
  for left,right in [('B','A'),('C','A'),('D','B'),('D','C'),('D','A')]:pairs.append({'metric':metric,'comparison':left+'-'+right,'delta':int(indexed.loc[left,metric]-indexed.loc[right,metric])})
 pd.DataFrame(pairs).to_csv(out/'contrastes.csv',index=False)
 wide=pp.pivot(index='seed',columns='representation',values='gain_common_A');delta=wide.enriquecido-wide.baseline
 write(out/'pareadas.json',{'metric':'gain_common_A','mean_delta':float(delta.mean()),'median_delta':float(delta.median()),'sd_delta':float(delta.std()),'wins':int((delta>0).sum()),'ties':int((delta==0).sum()),'losses':int((delta<0).sum()),'note':'Same month; seeds are not independent temporal samples'})
 write(out/'COMPLETE.json',{'status':'completed','models':40,'trials':40,'freeze_sha256':sha(out/'FROZEN.json'),'finished_unix':time.time(),'test':'201910 already observed; exploratory'});print(result.to_string(index=False),flush=True)
