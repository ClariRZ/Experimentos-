"""Consolidated v8 training stage. No training without immutable approved contract.

Produces DEVELOPMENT_FROZEN, never claims the full experiment COMPLETE.
Checkpoints are committed directories; incomplete fits block automatic retries.
"""
import argparse, gc, hashlib, json, os, shutil, sys, time
from pathlib import Path

ARMS = ['B0', 'R3', 'T4', 'RR4']

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def save(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('w') as f:
        json.dump(value, f, indent=2, allow_nan=False); f.write('\n'); f.flush(); os.fsync(f.fileno())
    tmp.replace(path)

def validate_contract(c):
    if c['status'] != 'APPROVED' or not c['training_authorized']:
        raise ValueError('Contract is not APPROVED for training')
    if c.get('unresolved') or not c.get('preflight_passed'):
        raise ValueError('Preflight unresolved')
    if list(c['arms']) != ARMS: raise ValueError('Unexpected arms/order')
    if c['train_months'] != [201904,201905,201906]: raise ValueError('Calendar changed')
    search, confirm = c['search'], c['confirm']
    groups = [[search['model_seed']], confirm['seeds'], c['evaluation_seeds']]
    if [len(x) for x in groups] != [1,2,10] or len(set(sum(groups, []))) != 13:
        raise ValueError('Overlapping or incorrect seed groups')
    if (search['trials_per_arm'],confirm['top_trials'],c['planned_fits']) != (20,3,144):
        raise ValueError('Fit budget changed')
    budget=c['budget']
    if not budget['approved'] or any(not isinstance(budget.get(k),int) or budget[k]<=0 for k in ['required_free_disk_bytes','max_rss_bytes','requested_max_seconds']):
        raise ValueError('Resource limits not approved')
    for arm in ARMS:
        columns=c['arms'][arm]['columns']
        if not columns or len(set(columns))!=len(columns) or set(columns)&{'clase_ternaria','numero_de_cliente','foto_mes'}:
            raise ValueError('Invalid feature schema')

def choose_finalists(trials, count=3):
    import numpy as np
    if any(t['state']!='COMPLETE' or not np.isfinite(t['auc']) for t in trials):
        raise ValueError('Incomplete or invalid trials')
    if len(trials)<count: raise ValueError('Insufficient trials')
    return sorted(trials,key=lambda t:(-t['auc'],t['trial']))[:count]

def choose_confirmed(rows):
    import numpy as np
    for r in rows:
        if len(r['aucs'])!=2 or not np.isfinite(r['aucs']).all():raise ValueError('Invalid confirmations')
    return min(rows,key=lambda r:(-float(np.mean(r['aucs'])),float(np.std(r['aucs'],ddof=0)),r['rounds'],r['trial']))

def cutoff(k,n,month_n):
    if not 0<=k<=n or n<=0 or month_n<0:raise ValueError('Invalid policy')
    return int(k)*int(month_n)//int(n)

class Checkpoints:
    def __init__(self, root, identity):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        p=self.root/'identity.json'
        if p.exists():
            if json.loads(p.read_text())!=identity: raise ValueError('Resume identity changed')
        else:save(p,identity)
    def load(self,key,request):
        p=self.root/key
        if not p.exists():return None
        record=json.loads((p/'record.json').read_text())
        if record['request']!=request:raise ValueError('Checkpoint request changed')
        for name,h in record['hashes'].items():
            if sha(p/name)!=h:raise ValueError('Corrupt checkpoint: '+key)
        return record
    def run(self,key,request,callback):
        previous=self.load(key,request)
        if previous is not None:return previous
        partial=self.root/(key+'.pending')
        if partial.exists():raise RuntimeError('Interrupted fit requires review: '+str(partial))
        if len(list(self.root.glob('*/record.json')))>=144:raise RuntimeError('Fit cap')
        partial.mkdir();save(partial/'request.json',request)
        result=callback(partial)
        hashes={p.name:sha(p) for p in partial.iterdir() if p.is_file()}
        record={'request':request,'result':result,'hashes':hashes}
        save(partial/'record.json',record);partial.rename(self.root/key)
        return record

def main():
    import numpy as np
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--config',type=Path,required=True);ap.add_argument('--dataset',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();c=json.loads(a.config.read_text());validate_contract(c)
    import importlib.metadata, platform, resource
    if list(sys.version_info[:2])!=c['runtime_reference']['python_major_minor']:raise ValueError('Python mismatch')
    for package,version in c['runtime_reference']['packages'].items():
        if importlib.metadata.version(package)!=version:raise ValueError('Package mismatch: '+package)
    if sha(a.dataset)!=c['dataset_sha256']:raise ValueError('Dataset mismatch')
    evidence=c.get('preflight_evidence',{})
    if not evidence:raise ValueError('Missing signed preflight evidence')
    for relative,h in evidence.items():
        if sha(a.repo/relative)!=h:raise ValueError('Preflight evidence changed')
    # Executed code includes imported v7 helpers; all identities gate resumption.
    scripts=Path(__file__).parent;old=a.repo/'HISTORIA_2019_01/v7/scripts'
    identity={'contract_sha256':sha(a.config),'dataset_sha256':sha(a.dataset),'code':{str(p.relative_to(a.repo)):sha(p) for folder in [scripts,old] for p in sorted(folder.glob('*.py'))}}
    a.output.mkdir(parents=True,exist_ok=True)
    import fcntl
    lock=(a.output/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    try:
        cp=Checkpoints(a.output/'private/checkpoints',identity)
        (a.output/'private/.gitignore').write_text('*\n')
        started=a.output/'started.json'
        if not started.exists():save(started,{'epoch':time.time()})
        deadline=json.loads(started.read_text())['epoch']+c['budget']['requested_max_seconds']
        def guard(*args):
            if time.time()>=deadline:raise TimeoutError('Original deadline exceeded')
            if shutil.disk_usage(a.output).free<c['budget']['required_free_disk_bytes']:raise OSError('Disk guard')
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>c['budget']['max_rss_bytes']:raise MemoryError('RSS guard')
        guard.order=0;guard.before_iteration=True
        guard()
        frozen_config=a.output/'config_frozen.json'
        if frozen_config.exists() and sha(frozen_config)!=sha(a.config):raise ValueError('Frozen contract changed')
        if not frozen_config.exists():shutil.copy2(a.config,frozen_config)
        save(a.output/'environment.json',{'python':sys.version,'platform':platform.platform(),'packages':{d.metadata['Name']:d.version for d in importlib.metadata.distributions()}})
        sys.path.insert(0,str(old));import ejecutar_v7 as v7
        import polars as pl,lightgbm as lgb,optuna
        from sklearn.metrics import roc_auc_score
        from rr4 import rr4
        # Labels are removed before invoking the unchanged feature builder.
        cfg=json.loads((a.repo/'HISTORIA_2019_01/v7/resultados/agosto/config_frozen.json').read_text())
        data=v7.read_data(a.dataset,list(range(201901,201909)))
        meta=data.filter(pl.col(v7.MONTH).is_in(c['train_months']+[201908])).select([v7.ID,v7.MONTH,v7.LABEL]).sort([v7.ID,v7.MONTH])
        if meta[v7.LABEL].null_count() or not set(meta[v7.LABEL].unique())<={'BAJA+1','BAJA+2','CONTINUA'}:raise ValueError('Invalid labels')
        hist,_=v7.history(data.drop(v7.LABEL),cfg,c['train_months']+[201908]);del data;gc.collect()
        if not hist.select([v7.ID,v7.MONTH]).equals(meta.select([v7.ID,v7.MONTH])):raise ValueError('Key order')
        tr=meta[v7.MONTH].is_in(c['train_months']).to_numpy();va=(meta[v7.MONTH]==201908).to_numpy()
        yt=meta.filter(pl.Series(tr))[v7.LABEL].is_in(['BAJA+1','BAJA+2']).to_numpy().astype(np.int8)
        yv=(meta.filter(pl.Series(va))[v7.LABEL]=='BAJA+2').to_numpy().astype(np.int8);ids=meta.filter(pl.Series(va))[v7.ID].to_numpy()
        def fit(dest,hp,seed,rounds,early,xt,xv):
            guard();params={**c['search']['fixed'],**hp,'seed':seed,'feature_fraction_seed':seed,'bagging_seed':seed,'data_random_seed':seed,'verbosity':-1}
            ds=lgb.Dataset(xt,label=yt,feature_name=[f'f{i}' for i in range(xt.shape[1])]);callbacks=[guard];kw={}
            if early:callbacks.append(lgb.early_stopping(c['search']['early_stopping_rounds'],verbose=False));kw['valid_sets']=[lgb.Dataset(xv,label=yv,reference=ds)]
            start=time.monotonic();model=lgb.train(params,ds,num_boost_round=rounds,callbacks=callbacks,**kw)
            pred=model.predict(xv,num_threads=4)
            if not np.isfinite(pred).all():raise ValueError('Nonfinite predictions')
            model.save_model(str(dest/'model.txt'));np.savez_compressed(dest/'august.npz',ids=ids,prediction=pred)
            save(dest/'parameters.json',params)
            return {'auc':float(roc_auc_score(yv,pred)),'rounds':int(model.best_iteration if early else rounds),'seconds':time.monotonic()-start}
        models={};policy=None
        for arm in ARMS:
            guard();save(a.output/'status.json',{'status':'TRAINING','arm':arm})
            frame=hist
            if arm=='RR4':
                new={}
                for source in c['history_sources']:
                    values=rr4(hist.select([source,*[f'{source}__lag{k}' for k in range(1,4)]]).to_numpy()).astype(np.float32)
                    for j,operation in enumerate(['recency','zero_run','nonzero_run']):new[f'{source}__rr4_{operation}']=pl.Series(values[:,j],nan_to_null=True)
                frame=hist.hstack(pl.DataFrame(new));del new
            elif arm!='B0':frame,_=v7.extras(hist,arm,c['history_sources'])
            cols=c['arms'][arm]['columns'];frame=v7.numeric(frame.select(cols),cols)
            xt=frame.filter(pl.Series(tr)).to_numpy(order='c');xv=frame.filter(pl.Series(va)).to_numpy(order='c');del frame;gc.collect();guard()
            # Deterministic replay of ask/tell restores TPE RNG state without retraining.
            study=optuna.create_study(direction='maximize',sampler=optuna.samplers.TPESampler(seed=c['search']['sampler_seed'],n_startup_trials=c['search']['startup_trials']))
            trials=[]
            for i in range(c['search']['trials_per_arm']):
                trial=study.ask();hp={n:(trial.suggest_int if v['type']=='int' else trial.suggest_float)(n,v['low'],v['high'],log=v.get('log',False)) for n,v in c['search']['range'].items()}
                req={'hp':hp,'seed':c['search']['model_seed'],'rounds':c['search']['max_rounds'],'early':True}
                result=cp.run(f'{arm}_bo_{i:02d}',req,lambda dest:fit(dest,xt=xt,xv=xv,**req))['result']
                study.tell(trial,result['auc']);trials.append({'trial':i,'params':hp,'state':'COMPLETE',**result});save(a.output/arm/'trials.json',trials)
            finalists=choose_finalists(trials);confirmed=[]
            for t in finalists:
                aucs=[]
                for seed in c['confirm']['seeds']:
                    req={'hp':t['params'],'seed':seed,'rounds':t['rounds'],'early':False}
                    r=cp.run(f'{arm}_confirm_{t["trial"]:02d}_{seed}',req,lambda dest:fit(dest,xt=xt,xv=xv,**req));aucs.append(r['result']['auc'])
                confirmed.append({**t,'aucs':aucs})
            chosen=choose_confirmed(confirmed);save(a.output/arm/'confirmation.json',confirmed);save(a.output/arm/'chosen.json',chosen)
            predictions=[];models[arm]={}
            for seed in c['evaluation_seeds']:
                req={'hp':chosen['params'],'seed':seed,'rounds':chosen['rounds'],'early':False};key=f'{arm}_final_{seed}'
                r=cp.run(key,req,lambda dest:fit(dest,xt=xt,xv=xv,**req));models[arm][str(seed)]={'checkpoint':key,'hashes':r['hashes']}
                with np.load(cp.root/key/'august.npz') as f:
                    if not np.array_equal(f['ids'],ids):raise ValueError('Checkpoint IDs')
                    predictions.append(f['prediction'])
            ensemble=np.mean(predictions,axis=0)
            if arm=='B0':
                k=v7.evaluate_gain_curve(ids,ensemble,yv)['cut_contacts'];policy={'k_august':int(k),'n_august':len(ids)};save(a.output/'policy.json',policy)
            np.savez_compressed(a.output/'private'/f'{arm}_august_ensemble.npz',ids=ids,prediction=ensemble)
            k=policy['k_august'];save(a.output/arm/'august.json',{'ensemble_auc':float(roc_auc_score(yv,ensemble)),'common':v7.payoff(ids,ensemble,yv,k)[0],'seed_common':[v7.payoff(ids,p,yv,k)[0] for p in predictions]})
            del xt,xv,predictions;gc.collect()
        # Economic confirmation diagnostics are computed only after common B0 policy is fixed.
        for arm in ARMS:
            diagnostics=[]
            for trial in json.loads((a.output/arm/'confirmation.json').read_text()):
                for seed in c['confirm']['seeds']:
                    key=f'{arm}_confirm_{trial["trial"]:02d}_{seed}'
                    with np.load(cp.root/key/'august.npz') as f:
                        if not np.array_equal(ids,f['ids']):raise ValueError('Confirmation IDs')
                        p=f['prediction']
                        diagnostics.append({'trial':trial['trial'],'seed':seed,'common':v7.payoff(ids,p,yv,policy['k_august'])[0],'own_smoothed':v7.evaluate_gain_curve(ids,p,yv),'selection_role':'none'})
            save(a.output/arm/'confirmation_economics.json',diagnostics)
        guard();save(a.output/'policy_frozen.json',{'identity':identity,'policy':policy,'models':models,'epoch':time.time(),'completed_fits':len(list(cp.root.glob('*/record.json')))})
        if len(list(cp.root.glob('*/record.json')))!=144:raise ValueError('Incomplete planned fits')
        save(a.output/'status.json',{'status':'DEVELOPMENT_FROZEN','fits_completed':144,'evaluation_pending':[201909,201910]})
    finally:
        lock.close()

if __name__=='__main__':
    try:main()
    except Exception as error:
        # Preserve failed attempts; never silently resume or increase fit budget.
        if '--output' in sys.argv:
            target=Path(sys.argv[sys.argv.index('--output')+1])
            if target.exists():
                save(target/'failure_'+str(time.time_ns())+'.json',{'type':type(error).__name__,'message':str(error),'epoch':time.time()})
        raise
