"""Optimiza con agosto. Evaluación de octubre sólo tras congelar todos los modelos."""
import argparse,json,time,hashlib,gc,platform,resource,pickle
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb
import optuna
from sklearn.metrics import roc_auc_score
from historicas import gain

FAMILIES=['original','lags','deltas','medias','pendientes','ratios']
def save_json(p,obj):p.write_text(json.dumps(obj,indent=2))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def load_matrix(prep,manifest,exp):
 groups=FAMILIES[:int(exp[1:])+1]
 arrays=[np.load(prep/(g+'.npy'),mmap_mode='r') for g in groups]
 X=np.concatenate(arrays,axis=1)
 columns=sum([manifest['families'][g] for g in groups],[])
 cats=[i for i,c in enumerate(columns) if c in manifest['categorical']]
 return X,columns,cats

def policy(y,pred,ids):
 order=np.lexsort((np.asarray(ids),-pred));g=np.r_[0,np.cumsum(gain(np.asarray(y)[order]))]
 k=int(np.argmax(g)) # empate: menos contactos; incluye cero
 return {'validation_k':k,'fraction':k/len(y),'validation_gain':int(g[k]),'method':'max_validation_gain_transfer_fraction','tie_break':'numero_de_cliente_ascending'}

def run(a):
 prep=Path(a.prep);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((prep/'manifest.json').read_text());cfg=json.loads(Path(a.config).read_text())
 rows=pd.read_parquet(prep/'filas.parquet');dev=pd.read_parquet(prep/'meta_desarrollo.parquet')
 train=rows.foto_mes.isin(cfg['train_months']).to_numpy();val=(rows.foto_mes==cfg['validation_month']).to_numpy()
 y=dev.set_index(['numero_de_cliente','foto_mes']).clase_ternaria
 devkeys=pd.MultiIndex.from_frame(rows.loc[train|val,['numero_de_cliente','foto_mes']]);assert y.index.equals(devkeys)
 ytrain=dev.loc[dev.foto_mes.isin(cfg['train_months']),'clase_ternaria'].isin(['BAJA+1','BAJA+2']).astype(int).to_numpy()
 yval=dev.loc[dev.foto_mes==cfg['validation_month'],'clase_ternaria'].isin(['BAJA+1','BAJA+2']).astype(int).to_numpy()
 valclass=dev.loc[dev.foto_mes==cfg['validation_month'],'clase_ternaria'].to_numpy()
 fixed={'objective':'binary','metric':'auc','verbosity':-1,'num_threads':cfg['threads'],'seed':cfg['seed'],'bagging_seed':cfg['seed'],'feature_fraction_seed':cfg['seed'],'data_random_seed':cfg['seed'],'bagging_freq':1,'feature_pre_filter':False,'deterministic':True,'force_col_wise':True,'max_bin':255}
 config_hash=sha(Path(a.config))
 marker=out/'config_hash.txt'
 if marker.exists() and marker.read_text()!=config_hash:raise ValueError('Configuracion cambió; usar nueva carpeta')
 marker.write_text(config_hash)
 if a.mode in ['pilot','train']:
  if (out/'FROZEN.json').exists():raise ValueError('Modelos ya congelados; no reoptimizar')
  experiments=['B0'] if a.mode=='pilot' else cfg['experiments']
  for exp in experiments:
   dest=out/exp;dest.mkdir(exist_ok=True)
   if (dest/'complete.json').exists():continue
   start=time.time();X,cols,cats=load_matrix(prep,manifest,exp)
   Xt=X[train];Xv=X[val];del X;gc.collect()
   dt=lgb.Dataset(Xt,label=ytrain,feature_name=cols,categorical_feature=cats,params=fixed,free_raw_data=True)
   dv=lgb.Dataset(Xv,label=yval,reference=dt,feature_name=cols,categorical_feature=cats,free_raw_data=True)
   dt.construct();dv.construct();del Xt;gc.collect()
   def objective(trial):
    sp=cfg['search_space']
    pars={**fixed,'num_leaves':trial.suggest_int('num_leaves',*sp['num_leaves'],log=True),'learning_rate':trial.suggest_float('learning_rate',*sp['learning_rate'],log=True),'min_data_in_leaf':trial.suggest_int('min_data_in_leaf',*sp['min_data_in_leaf'],log=True),'feature_fraction':trial.suggest_float('feature_fraction',*sp['feature_fraction']),'bagging_fraction':trial.suggest_float('bagging_fraction',*sp['bagging_fraction'])}
    t=time.time();model=lgb.train(pars,dt,num_boost_round=cfg['max_rounds'] if a.mode=='train' else 100,valid_sets=[dv],valid_names=['validation'],callbacks=[lgb.early_stopping(cfg['early_stopping'],first_metric_only=True,verbose=False)])
    auc=float(model.best_score['validation']['auc']);trial.set_user_attr('best_iteration',model.best_iteration);trial.set_user_attr('seconds',time.time()-t)
    model.save_model(str(dest/f'trial_{trial.number}.txt'))
    print(exp,'trial',trial.number,'auc',auc,'trees',model.best_iteration,'seconds',round(time.time()-t,1),flush=True)
    return auc
   sampler_path=dest/'sampler.pkl'
   sampler=pickle.loads(sampler_path.read_bytes()) if sampler_path.exists() else optuna.samplers.TPESampler(seed=cfg['seed'],n_startup_trials=cfg['startup_trials'])
   study=optuna.create_study(study_name=exp,direction='maximize',storage='sqlite:///'+str((out/'studies.sqlite').resolve()),load_if_exists=True,sampler=sampler)
   target=1 if a.mode=='pilot' else cfg['trials']
   finished=sum(t.state==optuna.trial.TrialState.COMPLETE for t in study.trials)
   # trials anteriores completos se preservan; se registran reinicios.
   def checkpoint(study,trial):
    tmp=sampler_path.with_suffix('.tmp');tmp.write_bytes(pickle.dumps(study.sampler));tmp.replace(sampler_path)
   study.optimize(objective,n_trials=max(0,target-finished),callbacks=[checkpoint])
   best=study.best_trial;model=lgb.Booster(model_file=str(dest/f'trial_{best.number}.txt'))
   pred=model.predict(Xv);pol=policy(valclass,pred,rows.loc[val,'numero_de_cliente'])
   model.save_model(str(dest/'model.txt'))
   pd.DataFrame({'numero_de_cliente':rows.loc[val,'numero_de_cliente'].to_numpy(),'prob':pred}).to_parquet(dest/'validation_predictions.parquet',index=False)
   record={'experiment':exp,'n_features':len(cols),'auc_validation':float(roc_auc_score(yval,pred)),'policy':pol,'best_params':best.params,'best_iteration':best.user_attrs['best_iteration'],'best_trial':best.number,'elapsed_seconds_this_invocation':time.time()-start,'completed_trials':target,'peak_rss_mib_process':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'model_sha256':sha(dest/'model.txt'),'feature_names':cols}
   save_json(dest/'complete.json',record);study.trials_dataframe().to_csv(dest/'trials.csv',index=False)
   pd.DataFrame({'feature':cols,'gain':model.feature_importance('gain'),'split':model.feature_importance('split')}).to_csv(dest/'importance.csv',index=False)
   del dt,dv,Xv,model;gc.collect()
  if a.mode=='train':
   records=[json.loads((out/e/'complete.json').read_text()) for e in cfg['experiments']]
   save_json(out/'FROZEN.json',{'config_sha256':config_hash,'models':{r['experiment']:r['model_sha256'] for r in records},'decisions':{r['experiment']:sha(out/r['experiment']/'complete.json') for r in records},'manifest_sha256':sha(prep/'manifest.json'),'unix_time':time.time(),'common_contact_fraction':records[2]['policy']['fraction'],'test_opened':False})
  return
 if a.mode=='evaluate':
  frozen=json.loads((out/'FROZEN.json').read_text());assert frozen['config_sha256']==config_hash
  assert sha(prep/'manifest.json')==frozen['manifest_sha256']
  for exp in cfg['experiments']:
   assert sha(out/exp/'model.txt')==frozen['models'][exp]
   assert sha(out/exp/'complete.json')==frozen['decisions'][exp]
  test=pd.read_parquet(prep/'meta_test_sellado.parquet');testmask=(rows.foto_mes==cfg['test_month']).to_numpy()
  assert np.array_equal(test.numero_de_cliente,rows.loc[testmask,'numero_de_cliente'])
  results=[]
  for exp in cfg['experiments']:
   dest=out/exp;r=json.loads((dest/'complete.json').read_text());X,cols,cats=load_matrix(prep,manifest,exp);Xt=X[testmask];del X;gc.collect()
   model=lgb.Booster(model_file=str(dest/'model.txt'));pred=model.predict(Xt)
   order=np.lexsort((test.numero_de_cliente.to_numpy(),-pred));g=np.r_[0,np.cumsum(gain(test.clase_ternaria.to_numpy()[order]))]
   k=min(len(test),int(np.floor(r['policy']['fraction']*len(test)+.5)));kc=min(len(test),int(np.floor(frozen['common_contact_fraction']*len(test)+.5)))
   hits=int((test.clase_ternaria.to_numpy()[order[:k]]=='BAJA+2').sum())
   results.append({'experimento':exp,'variables':len(cols),'auc_agosto':r['auc_validation'],'ganancia_octubre':int(g[k]),'contactos':k,'aciertos_BAJA2':hits,'ganancia_presupuesto_comun_B2':int(g[kc]),'contactos_comunes':kc,'maximo_retrospectivo':int(g.max()),'k_maximo_retrospectivo':int(np.argmax(g)),'segundos':r['elapsed_seconds_this_invocation'],'arboles':r['best_iteration'],'trials':r['completed_trials'],'pico_ram_mib_proceso':r['peak_rss_mib_process']})
   pd.DataFrame({'numero_de_cliente':test.numero_de_cliente,'prob':pred}).to_parquet(dest/'test_predictions.parquet',index=False)
   pd.DataFrame({'contactos':np.arange(len(g)),'ganancia':g}).to_csv(dest/'curva_octubre.csv',index=False)
   del Xt,model;gc.collect()
  result=pd.DataFrame(results);result['delta_anterior']=result.ganancia_octubre.diff();result['delta_B0']=result.ganancia_octubre-result.ganancia_octubre.iloc[0];result['delta_B2']=result.ganancia_octubre-result.ganancia_octubre.iloc[2];result.to_csv(out/'resultados.csv',index=False)
  save_json(out/'EVALUATED.json',{'unix_time':time.time(),'config_sha256':config_hash});print(result.to_string(index=False),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prep',required=True);p.add_argument('--out',required=True);p.add_argument('--config',required=True);p.add_argument('--mode',choices=['pilot','train','evaluate'],required=True);run(p.parse_args())
