import argparse,json,hashlib,time,gc,pickle
from pathlib import Path
import numpy as np,pandas as pd,lightgbm as lgb,optuna
from sklearn.metrics import roc_auc_score
from ratios_intrames import NAMES
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,indent=2))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def metrics(ids,classes,pred):
 order=np.lexsort((np.asarray(ids),-pred));hit=np.asarray(classes)=='BAJA+2';g=np.r_[0,np.cumsum(np.where(hit[order],1072500,-27500))]
 return {str(k):{'ganancia':int(g[k]),'aciertos':int(hit[order[:k]].sum())} for k in [10500,11000,11500]}
def policy(ids,classes,pred):
 order=np.lexsort((np.asarray(ids),-pred));g=np.r_[0,np.cumsum(np.where(np.asarray(classes)[order]=='BAJA+2',1072500,-27500))];k=int(g.argmax());return {'fraction':k/len(pred),'validation_k':k,'validation_gain':int(g[k])}
def save_model(model,dest,cols):
 model.save_model(str(dest/'model.txt'))
 pd.DataFrame({'feature':cols,'gain':model.feature_importance('gain'),'split':model.feature_importance('split')}).to_csv(dest/'importance.csv',index=False)
def c3(a):
 prep=Path(a.prep);out=Path(a.out)/'C3';out.mkdir(parents=True,exist_ok=True)
 plan=read(ROOT/'config/c3_original.json');rows=pd.read_parquet(prep/'c3_filas.parquet');tr=rows.foto_mes.isin([202103,202104]).to_numpy();ev=rows.foto_mes.eq(202106).to_numpy();names=plan['schema'];base=np.load(prep/'c3.npy',mmap_mode='r');extra=np.load(prep/'c3_intrames.npy');y=rows.clase_ternaria.eq('BAJA+2').astype('int8').to_numpy();ids=rows.loc[ev,'numero_de_cliente'].to_numpy();classes=rows.loc[ev,'clase_ternaria'].to_numpy()
 summary=[];per=[]
 for arm in ['C3_CONTROL','C3_HOJA2500','C3_INTRAMES']:
  d=out/arm;d.mkdir(exist_ok=True);cols=names+(NAMES[:4] if arm=='C3_INTRAMES' else [])
  xt=np.array(base[tr],order='C');xv=np.array(base[ev],order='C')
  if arm=='C3_INTRAMES':xt=np.concatenate([xt,extra[tr]],axis=1);xv=np.concatenate([xv,extra[ev]],axis=1)
  preds=[]
  for seed in plan['seeds']:
   dest=d/str(seed);dest.mkdir(exist_ok=True);cp=dest/'complete.json';start=time.time()
   if cp.exists():
    r=read(cp);assert sha(dest/'model.txt')==r['model_sha256'];pred=np.load(dest/'scores.npy')
   else:
    pars={**plan['params'],'seed':seed}
    if arm=='C3_HOJA2500':pars['min_data_in_leaf']=2500
    ds=lgb.Dataset(xt,label=y[tr],feature_name=cols,free_raw_data=True)
    model=lgb.train(pars,ds,num_boost_round=300);pred=model.predict(xv,num_threads=6)
    save_model(model,dest,cols);np.save(dest/'scores.npy',pred)
    r={'arm':arm,'seed':seed,'auc':float(roc_auc_score(y[ev],pred)),'cuts':metrics(ids,classes,pred),'seconds':time.time()-start,'model_sha256':sha(dest/'model.txt')};write(cp,r)
    del model,ds;gc.collect()
   preds.append(pred);per.append({'arm':arm,'seed':seed,'auc':r['auc'],**{'gain_'+k:v['ganancia'] for k,v in r['cuts'].items()},'seconds':r['seconds']})
   print('C3_DONE',arm,seed,'seconds',round(r['seconds'],1),flush=True)
  ens=np.mean(preds,axis=0);np.save(d/'ensemble_scores.npy',ens)
  summary.append({'arm':arm,'features':len(cols),'seeds':len(preds),'auc_ensemble':float(roc_auc_score(y[ev],ens)),'cuts':metrics(ids,classes,ens)})
  del xt,xv,preds;gc.collect()
 pd.DataFrame(per).to_csv(out/'por_seed.csv',index=False);write(out/'ensemble.json',summary)
 per=pd.DataFrame(per);control=per[per.arm=='C3_CONTROL'].set_index('seed');deltas=[]
 for arm in ['C3_HOJA2500','C3_INTRAMES']:
  other=per[per.arm==arm].set_index('seed');delta=other.gain_11000-control.gain_11000
  deltas.append({'arm':arm,'mean_delta_11000':float(delta.mean()),'median_delta_11000':float(delta.median()),'sd_delta_11000':float(delta.std()),'wins':int((delta>0).sum()),'ties':int((delta==0).sum()),'losses':int((delta<0).sum())})
 write(out/'comparacion.json',deltas);write(out/'COMPLETE.json',{'status':'completed','evaluation':'June2021_reused_exploratory'})
def b6(a):
 prep=Path(a.prep);parent=Path(a.parent);orig=parent/'preparado';out=Path(a.out)/'B6';out.mkdir(parents=True,exist_ok=True)
 cfg=read(ROOT/'config/b5_original.json');b5=read(ROOT/'config/b5_complete.json');manifest=read(orig/'manifest.json');families=['original','lags','deltas','medias','pendientes','ratios'];cols=sum([manifest['families'][g] for g in families],[])+NAMES
 arrays=[np.load(orig/(g+'.npy'),mmap_mode='r') for g in families]+[np.load(prep/'b6_intrames.npy',mmap_mode='r')];X=np.concatenate(arrays,axis=1)
 rows=pd.read_parquet(orig/'filas.parquet');dev=pd.read_parquet(orig/'meta_desarrollo.parquet');tr=rows.foto_mes.isin(cfg['train_months']).to_numpy();va=rows.foto_mes.eq(cfg['validation_month']).to_numpy();assert rows.loc[tr|va,['numero_de_cliente','foto_mes']].reset_index(drop=True).equals(dev[['numero_de_cliente','foto_mes']])
 yt=dev.loc[dev.foto_mes.isin(cfg['train_months']),'clase_ternaria'].isin(['BAJA+1','BAJA+2']).astype(int).to_numpy();vc=dev.loc[dev.foto_mes.eq(cfg['validation_month']),'clase_ternaria'].to_numpy();yv=np.isin(vc,['BAJA+1','BAJA+2']);ids=rows.loc[va,'numero_de_cliente'].to_numpy();cats=[i for i,c in enumerate(cols) if c in manifest['categorical']]
 fixed={'objective':'binary','metric':'auc','verbosity':-1,'num_threads':8,'seed':cfg['seed'],'bagging_seed':cfg['seed'],'feature_fraction_seed':cfg['seed'],'data_random_seed':cfg['seed'],'bagging_freq':1,'feature_pre_filter':False,'deterministic':True,'force_col_wise':True,'max_bin':255}
 xt=X[tr];xv=X[va];dt=lgb.Dataset(xt,label=yt,feature_name=cols,categorical_feature=cats,params=fixed,free_raw_data=True);dv=lgb.Dataset(xv,label=yv,reference=dt,feature_name=cols,categorical_feature=cats,free_raw_data=True);dt.construct();dv.construct();del xt;gc.collect()
 for arm in ['B6_FIJO','B6_BO']:
  d=out/arm;d.mkdir(exist_ok=True)
  if (d/'complete.json').exists():continue
  start=time.time()
  if arm=='B6_FIJO':
   pars={**fixed,**b5['best_params']};model=lgb.train(pars,dt,num_boost_round=b5['best_iteration']);bestpars=b5['best_params'];nt=0
  else:
   sp=cfg['search_space'];samplerfile=d/'sampler.pkl';sampler=pickle.loads(samplerfile.read_bytes()) if samplerfile.exists() else optuna.samplers.TPESampler(seed=cfg['seed'],n_startup_trials=5)
   study=optuna.create_study(study_name='B6_BO',direction='maximize',storage='sqlite:///'+str((d/'study.sqlite').resolve()),load_if_exists=True,sampler=sampler)
   def objective(t):
    pars={**fixed,'num_leaves':t.suggest_int('num_leaves',*sp['num_leaves'],log=True),'learning_rate':t.suggest_float('learning_rate',*sp['learning_rate'],log=True),'min_data_in_leaf':t.suggest_int('min_data_in_leaf',*sp['min_data_in_leaf'],log=True),'feature_fraction':t.suggest_float('feature_fraction',*sp['feature_fraction']),'bagging_fraction':t.suggest_float('bagging_fraction',*sp['bagging_fraction'])}
    m=lgb.train(pars,dt,num_boost_round=cfg['max_rounds'],valid_sets=[dv],callbacks=[lgb.early_stopping(100,verbose=False)]);m.save_model(str(d/f'trial_{t.number}.txt'));t.set_user_attr('best_iteration',m.best_iteration);return float(m.best_score['valid_0']['auc'])
   study.optimize(objective,n_trials=20-sum(t.state==optuna.trial.TrialState.COMPLETE for t in study.trials),callbacks=[lambda s,t:samplerfile.write_bytes(pickle.dumps(s.sampler))]);best=study.best_trial;model=lgb.Booster(model_file=str(d/f'trial_{best.number}.txt'));bestpars=best.params;nt=20;study.trials_dataframe().to_csv(d/'trials.csv',index=False)
  pred=model.predict(xv,num_threads=8);pol=policy(ids,vc,pred);save_model(model,d,cols);np.save(d/'validation_scores.npy',pred)
  write(d/'complete.json',{'arm':arm,'features':len(cols),'auc':float(roc_auc_score(yv,pred)),'policy':pol,'best_params':bestpars,'trees':model.num_trees(),'trials':nt,'seconds':time.time()-start,'model_sha256':sha(d/'model.txt')});print('B6_DONE',arm,flush=True)
 del dt,dv,xv;gc.collect()
 write(out/'FROZEN.json',{'models':{arm:sha(out/arm/'model.txt') for arm in ['B6_FIJO','B6_BO']},'config_sha256':sha(ROOT/'config/protocolo.json'),'note':'October2019 already observed in previous experiment; exploratory extension'})
 test=pd.read_parquet(orig/'meta_test_sellado.parquet');tm=rows.foto_mes.eq(cfg['test_month']).to_numpy();assert np.array_equal(test.numero_de_cliente,rows.loc[tm,'numero_de_cliente']);xt=X[tm];del X;gc.collect();results=[]
 for arm in ['B5_CONTROL','B6_FIJO','B6_BO']:
  if arm=='B5_CONTROL':
   d=parent/'resultados/B5';model=lgb.Booster(model_file=str(d/'model.txt'));assert sha(d/'model.txt')==b5['model_sha256'];pred=model.predict(xt[:,:-7],num_threads=8);pol=b5['policy'];auc=b5['auc_validation']
  else:
   d=out/arm;r=read(d/'complete.json');model=lgb.Booster(model_file=str(d/'model.txt'));pred=model.predict(xt,num_threads=8);pol=r['policy'];auc=r['auc']
  dest=out/arm;dest.mkdir(exist_ok=True);np.save(dest/'test_scores.npy',pred)
  k=int(np.floor(pol['fraction']*len(test)+.5));order=np.lexsort((test.numero_de_cliente.to_numpy(),-pred));g=np.r_[0,np.cumsum(np.where(test.clase_ternaria.to_numpy()[order]=='BAJA+2',1072500,-27500))]
  if arm=='B5_CONTROL':
   reference=pd.read_csv(parent/'resultados/B5/curva_octubre.csv');assert np.array_equal(g,reference.ganancia.to_numpy())
  pd.DataFrame({'contactos':np.arange(len(g)),'ganancia':g}).to_csv(dest/'curva_octubre.csv',index=False)
  results.append({'arm':arm,'auc_validation':auc,'cuts':metrics(test.numero_de_cliente,test.clase_ternaria,pred),'policy_contacts':k,'policy_gain':int(g[k]),'features':model.num_feature()})
 write(out/'comparacion.json',results);write(out/'COMPLETE.json',{'status':'completed','B5_curve_exact_match':True})
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['c3','b6'],required=True);p.add_argument('--prep',required=True);p.add_argument('--out',required=True);p.add_argument('--parent',required=True);a=p.parse_args();get=Path(a.out);get.mkdir(parents=True,exist_ok=True);h=sha(ROOT/'config/protocolo.json');marker=get/'config_hash.txt'
if marker.exists():assert marker.read_text()==h
else:marker.write_text(h)
if a.mode=='c3':c3(a)
else:b6(a)
