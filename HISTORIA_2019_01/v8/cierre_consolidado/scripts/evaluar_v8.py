"""Frozen-model September/October scoring; no LightGBM training methods."""
import argparse,gc,json,sys,time
from pathlib import Path
import numpy as np
from ejecutar_v8 import ARMS,sha,save,cutoff

def contributions(ids,scores,y,k):
    if len(np.unique(ids))!=len(ids) or not np.isfinite(scores).all() or not np.isin(y,[0,1]).all() or not 0<=k<=len(ids):raise ValueError('Invalid ranking input')
    selected=np.zeros(len(ids),dtype=bool);selected[np.lexsort((ids,-scores))[:k]]=True
    return np.where(selected,np.where(y==1,1072500,-27500),0).astype(np.int64),selected

def bootstrap(d,replicates,seed,guard=None):
    """Literal paired client resampling; shared indices for all contrasts."""
    rng=np.random.default_rng(seed);out=np.empty((replicates,d.shape[1]),dtype=np.int64)
    for i in range(replicates):
        if guard is not None and i%64==0:guard()
        out[i]=d[rng.integers(0,len(d),size=len(d))].sum(axis=0)
    return out

def classify(octrow,seprow):
    if octrow['ensemble_delta']<0:return 'DESFAVORABLE_EN_ESTE_ESCENARIO'
    if octrow['ensemble_delta']==0:return 'SIN_MEJORA_OBSERVADA'
    if octrow['ci_adjusted'][0]>0 and seprow['ensemble_delta']>0 and octrow['seed_delta_mean']>0 and seprow['seed_delta_mean']>0 and sum(d>=0 for d in octrow['sensitivity_deltas'])>=4:return 'FAVORABLE_DENTRO_DE_ESTE_ANALISIS'
    return 'PROMETEDOR_INCONCLUSO'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--run',type=Path,required=True);ap.add_argument('--dataset',type=Path,required=True);a=ap.parse_args()
    frozen=json.loads((a.run/'policy_frozen.json').read_text());c=json.loads((a.run/'config_frozen.json').read_text())
    if frozen['completed_fits']!=144 or sha(a.run/'config_frozen.json')!=frozen['identity']['contract_sha256']:raise ValueError('Frozen identity mismatch')
    if sha(a.dataset)!=c['dataset_sha256']:raise ValueError('Dataset mismatch')
    for relative,h in frozen['identity']['code'].items():
        if sha(a.repo/relative)!=h:raise ValueError('Code changed since training: '+relative)
    import fcntl,resource,shutil
    lock=(a.run/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    try:
        deadline=json.loads((a.run/'started.json').read_text())['epoch']+c['budget']['requested_max_seconds']
        def guard():
            if time.time()>=deadline:raise TimeoutError('Original deadline')
            if shutil.disk_usage(a.run).free<c['budget']['required_free_disk_bytes']:raise OSError('Disk guard')
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>c['budget']['max_rss_bytes']:raise MemoryError('RSS guard')
        import polars as pl,lightgbm as lgb
        from scipy.stats import rankdata,t
        from sklearn.metrics import roc_auc_score
        sys.path.insert(0,str(a.repo/'HISTORIA_2019_01/v7/scripts'));import ejecutar_v7 as old
        from rr4 import rr4
        from diagnostico_octubre import VARS
        cfg=json.loads((a.repo/'HISTORIA_2019_01/v7/resultados/agosto/config_frozen.json').read_text())
        private=a.run/'private/evaluation';private.mkdir(exist_ok=True)
        policy=frozen['policy'];allrows={}
        def frame(hist,arm):
            f=hist
            if arm=='RR4':
                new={}
                for source in c['history_sources']:
                    values=rr4(hist.select([source,*[f'{source}__lag{k}' for k in range(1,4)]]).to_numpy()).astype(np.float32)
                    for j,op in enumerate(['recency','zero_run','nonzero_run']):new[f'{source}__rr4_{op}']=pl.Series(values[:,j],nan_to_null=True)
                f=hist.hstack(pl.DataFrame(new))
            elif arm!='B0':f,_=old.extras(hist,arm,c['history_sources'])
            cols=c['arms'][arm]['columns'];return old.numeric(f.select(cols),cols).to_numpy(order='c')
        def predict(hist,arm):
            x=frame(hist,arm);pred=[]
            for seed in c['evaluation_seeds']:
                guard();info=frozen['models'][arm][str(seed)];path=a.run/'private/checkpoints'/info['checkpoint']
                for name,h in info['hashes'].items():
                    if sha(path/name)!=h:raise ValueError('Checkpoint changed')
                model=lgb.Booster(model_file=str(path/'model.txt'));pred.append(model.predict(x,num_threads=4));del model
            del x;gc.collect();return np.asarray(pred)
        # Reproduce saved August scores before evaluating later months.
        guard()
        aug=old.read_data(a.dataset,list(range(201905,201909)))
        augmeta=aug.filter(pl.col(old.MONTH)==201908).select([old.ID,old.MONTH]).sort([old.ID,old.MONTH])
        aughist,_=old.history(aug.drop(old.LABEL),cfg,[201908])
        if not aughist.select([old.ID,old.MONTH]).equals(augmeta):raise ValueError('August ID order')
        verification={}
        for arm in ARMS:
            predictions=predict(aughist,arm)
            for i,seed in enumerate(c['evaluation_seeds']):
                info=frozen['models'][arm][str(seed)]
                with np.load(a.run/'private/checkpoints'/info['checkpoint']/'august.npz') as saved:
                    if not np.array_equal(saved['ids'],augmeta[old.ID].to_numpy()):raise ValueError('August IDs changed')
                    if not np.array_equal(saved['prediction'],predictions[i]):raise ValueError('August predictions not reproduced')
            verification[arm]={'seeds_verified':len(predictions),'max_absolute_error':0.0}
        save(a.run/'august_reproduction.json',verification)
        del aug,augmeta,aughist,predictions;gc.collect()
        for month in [201909,201910]:
            guard();save(a.run/'status.json',{'status':'EVALUATING','month':month,'fits_completed':144})
            data=old.read_data(a.dataset,list(range(month-3,month+1)))
            meta=data.filter(pl.col(old.MONTH)==month).select([old.ID,old.MONTH,old.LABEL]).sort([old.ID,old.MONTH])
            if meta[old.LABEL].null_count() or not set(meta[old.LABEL].unique())<={'BAJA+1','BAJA+2','CONTINUA'}:raise ValueError('Invalid labels')
            hist,_=old.history(data.drop(old.LABEL),cfg,[month])
            if not hist.select([old.ID,old.MONTH]).equals(meta.select([old.ID,old.MONTH])):raise ValueError('ID order')
            ids=meta[old.ID].to_numpy();labels=meta[old.LABEL].to_numpy();y=(labels=='BAJA+2').astype(np.int8);n=len(ids);k=cutoff(policy['k_august'],policy['n_august'],n)
            preds={};rows={};vectors={};selections={};bands={};seedgains={}
            for arm in ARMS:
                pred=predict(hist,arm);ens=pred.mean(axis=0);preds[arm]=ens
                np.savez_compressed(private/f'{arm}_{month}.npz',ids=ids,predictions=pred,ensemble=ens,labels=labels)
                d,sel=contributions(ids,ens,y,k);vectors[arm]=d;selections[arm]=sel
                sg=[int(contributions(ids,p,y,k)[0].sum()) for p in pred];seedgains[arm]=sg;hits=int(y[sel].sum())
                bands[arm]=[int(contributions(ids,ens,y,(policy['k_august']*n*num)//(policy['n_august']*den))[0].sum()) for num,den in [(85,100),(925,1000),(1,1),(1075,1000),(115,100)]]
                rows[arm]={'month':month,'N':n,'positives':int(y.sum()),'K':k,'hits':hits,'gain':int(d.sum()),'auc':float(roc_auc_score(y,ens)),'capture':hits/int(y.sum()),'lift':(hits/k)/(int(y.sum())/n) if k else None,'seed_aucs':[float(roc_auc_score(y,p)) for p in pred],'seed_gains':sg,'seed_gain_mean':float(np.mean(sg)),'seed_gain_sd':float(np.std(sg,ddof=1)),'contacted_classes':{label:int(np.sum(labels[sel]==label)) for label in ['BAJA+1','BAJA+2','CONTINUA']}}
                del pred;gc.collect()
            contrasts=np.column_stack([vectors[arm]-vectors['B0'] for arm in ARMS[1:]])
            bs=c['inference']['bootstrap'];dist=bootstrap(contrasts,bs['replicates'],bs['seed'],guard)
            for j,arm in enumerate(ARMS[1:]):
                sd=np.array(seedgains[arm])-np.array(seedgains['B0']);mean=float(sd.mean());se=float(sd.std(ddof=1)/np.sqrt(len(sd)));delta=int(contrasts[:,j].sum())
                rows[arm].update(ensemble_delta=delta,percent_vs_B0=100*delta/rows['B0']['gain'] if rows['B0']['gain'] else None,seed_deltas=sd.tolist(),seed_delta_mean=mean,seed_delta_sd=float(sd.std(ddof=1)),seed_ci95=[mean-float(t.ppf(.975,9))*se,mean+float(t.ppf(.975,9))*se],wins=int((sd>0).sum()),ties=int((sd==0).sum()),losses=int((sd<0).sum()),ci95=np.quantile(dist[:,j],[.025,.975],method='linear').tolist(),ci_adjusted=np.quantile(dist[:,j],[bs['alpha']/2,1-bs['alpha']/2],method='linear').tolist(),sensitivity_deltas=[x-z for x,z in zip(bands[arm],bands['B0'])],shared_contacts=int((selections[arm]&selections['B0']).sum()),added_contacts=int((selections[arm]&~selections['B0']).sum()),removed_contacts=int((~selections[arm]&selections['B0']).sum()))
            blend=(rankdata(preds['R3'],method='average')/n+rankdata(preds['T4'],method='average')/n)/2
            rows['BLEND_DESCRIPTIVE']={'gain':int(contributions(ids,blend,y,k)[0].sum()),'K':k,'auc':float(roc_auc_score(y,blend)),'promotion_eligible':False}
            save(a.run/f'evaluation_{month}.json',rows);allrows[month]=rows
            if month==201910:
                pert=data.drop(old.LABEL).with_columns([pl.when(pl.col(old.MONTH)==month).then(None).otherwise(pl.col(v)).alias(v) for v in VARS]);ph,_=old.history(pert,cfg,[month]);diag={}
                for arm in ['B0','RR4']:diag[arm]=int(contributions(ids,predict(ph,arm).mean(axis=0),y,k)[0].sum())
                diag['delta']=diag['RR4']-diag['B0'];diag['scope']='Sensitivity only, not a corrected result';save(a.run/'rr4_october_coherent.json',diag);del ph,pert
            del hist,data;gc.collect()
        guard();save(a.run/'FINAL.json',{'fits_completed':144,'classifications':{arm:classify(allrows[201910][arm],allrows[201909][arm]) for arm in ARMS[1:]},'exposed_months':True,'economic_evaluation_complete':True,'backup_verified':False,'vm_shutdown_verified':False})
        save(a.run/'status.json',{'status':'EVALUATED_BACKUP_PENDING','fits_completed':144})
    finally:
        lock.close()

if __name__=='__main__':main()
