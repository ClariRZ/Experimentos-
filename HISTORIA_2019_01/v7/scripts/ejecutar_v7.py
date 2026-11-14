"""V7: fresh matrices, 150 fits, frozen common budget, inference-only October.

Requires reviewed real-data audit. This process never changes the approved config.
"""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time
import traceback
import numpy as np
import polars as pl
import lightgbm as lgb
import optuna
from sklearn.metrics import roc_auc_score
from fe_core import (sanitize_base, month_to_idx, add_baseline_lags_deltas,
    build_window_families, build_monthly_rankings, evaluate_gain_curve)

ID='numero_de_cliente'; MONTH='foto_mes'; LABEL='clase_ternaria'
ARMS=['B0','RK','P3','MIN3','RAN3','R3','R4','T4','H_T','H_S']
TRAIN=[201904,201905,201906]

def save(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    tmp.replace(path)

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def numeric(df,names):
    return df.with_columns([pl.when(pl.col(n).cast(pl.Float32,strict=True).is_finite())
        .then(pl.col(n).cast(pl.Float32,strict=True)).otherwise(None).alias(n) for n in names])

def trim(frame,names,priority=()):
    keep=[];reasons={};groups={}
    for c in list(priority)+sorted(set(names)-set(priority)):
        s=frame[c]
        if s.null_count()==len(s):reasons[c]='all_missing';continue
        if s.n_unique()==1:reasons[c]='constant_including_null_pattern';continue
        h=int(s.hash(seed=2026).sum())
        alias=next((n for n in groups.get(h,[]) if s.equals(frame[n],check_dtypes=False)),None)
        if alias:reasons[c]='exact_duplicate_of:'+alias;continue
        groups.setdefault(h,[]).append(c);keep.append(c)
    return keep,reasons

def read_data(dataset,months,labels=True):
    lf=pl.scan_csv(dataset,infer_schema_length=20000)
    if not labels:lf=lf.select([n for n in lf.collect_schema().names() if n!=LABEL])
    df=lf.filter(pl.col(MONTH).is_in(months)).collect()
    keys=df.select([ID,MONTH])
    if keys.is_duplicated().any() or any(keys.null_count().row(0)):raise ValueError('Invalid keys')
    if set(df[MONTH].unique())!=set(months):raise ValueError('Missing calendar month')
    return df

def history(df,cfg,target_months):
    """Label-free feature generation; exact-calendar lookups, at most three lags."""
    if LABEL in df.columns:raise ValueError('Outcome column in feature generator')
    raw=[n for n in df.columns if n not in [ID,MONTH]]
    df=df.with_columns([pl.col(n).cast(pl.Float64,strict=True) for n in raw])
    df=sanitize_base(df,raw,{int(k):v for k,v in cfg['data']['broken_masks'].items()})
    lookup=df.with_columns(month_to_idx().alias('_idx'))
    hist=lookup.filter(pl.col(MONTH).is_in(target_months))
    sources=cfg['data']['history_sources']
    for k in range(1,4):
        part=lookup.select(pl.col(ID),(pl.col('_idx')+k).alias('_idx'),
            *[pl.col(c).alias(f'{c}__lag{k}') for c in sources])
        hist=hist.join(part,on=[ID,'_idx'],how='left')
    hist=add_baseline_lags_deltas(hist.drop('_idx').sort([ID,MONTH]),sources)
    return hist,raw

def extras(hist,arm,sources):
    if arm=='RK':return build_monthly_rankings(hist,sources),[f'{c}__rk0' for c in sources]
    if arm in ['P3','MIN3','RAN3']:
        kind={'P3':'mean','MIN3':'min','RAN3':'range'}[arm]
        f=build_window_families(hist,sources,3,include_f1=True,include_f3=False)
        return f,[f'{c}__f1_{kind}_W3' for c in sources]
    if arm in ['R3','R4','T4']:
        w=int(arm[-1]);f=build_window_families(hist,sources,w,include_f1=False,
            include_f2=arm=='T4',include_f3=arm!='T4')
        tag='f2' if arm=='T4' else 'f3'
        return f,[c for c in f.columns if f'__{tag}_' in c and c.endswith(f'_W{w}')]
    if arm=='SYM':
        expr=[]
        for c in sources:
            for k in [1,2]:
                x=pl.col(c);z=pl.col(f'{c}__lag{k}');den=x.abs()+z.abs()
                expr.append(pl.when(x.is_null()|z.is_null()).then(None)
                    .when(den==0).then(0.).otherwise((x-z)/den).alias(f'{c}__sym_lag{k}'))
        return hist.with_columns(expr),[e.meta.output_name() for e in expr]
    raise ValueError(arm)

def materialize(hist,raw,cfg,private,check,registry=None):
    """Train-only selection or frozen inference. No label is available here."""
    sources=cfg['data']['history_sources']; keys=hist.select([ID,MONTH])
    base_names=raw+[f'{c}__{f}' for c in sources for f in ['lag1','lag2','delta1','delta2']]
    base=numeric(hist.select([ID,MONTH,*base_names]),base_names)
    selecting=registry is None
    if selecting:
        keep,ex=trim(base.filter(pl.col(MONTH).is_in(TRAIN)),base_names)
        registry={'B0':{'columns':keep,'excluded':ex}}
    base=base.select([ID,MONTH,*registry['B0']['columns']]);base.write_parquet(private/'B0.parquet')
    def persist(arm,frame,names,priority):
        if selecting:
            keep,ex=trim(frame.filter(pl.col(MONTH).is_in(TRAIN)),names,priority)
            registry[arm]={'columns':keep,'excluded':ex}
        cols=registry[arm]['columns']
        out=frame.select([ID,MONTH,*cols])
        if not out.select([ID,MONTH]).equals(keys):raise ValueError('Key mismatch '+arm)
        out.write_parquet(private/f'{arm}.parquet');check()
    for arm in ['RK','P3','MIN3','RAN3','R3','R4','T4']:
        f,names=extras(hist,arm,sources)
        frame=base.hstack(numeric(f.select(names),names))
        persist(arm,frame,names,registry['B0']['columns']);del f,frame;gc.collect()
    # Keep the same source/formula pairs for R3 and R4, using training only.
    if selecting:
        sets=[{n.rsplit('_W',1)[0] for n in registry[a]['columns'] if '__f3_' in n} for a in ['R3','R4']]
        common=set.intersection(*sets)
        for arm in ['R3','R4']:
            old=registry[arm]['columns'];kept=[n for n in old if '__f3_' not in n or n.rsplit('_W',1)[0] in common]
            for n in set(old)-set(kept):registry[arm]['excluded'][n]='not_common_R3_R4_pair'
            registry[arm]['columns']=kept
            pl.read_parquet(private/f'{arm}.parquet').select([ID,MONTH,*kept]).write_parquet(private/f'{arm}.parquet.tmp')
            (private/f'{arm}.parquet.tmp').replace(private/f'{arm}.parquet')
    r4=pl.read_parquet(private/'R4.parquet')
    t4=pl.read_parquet(private/'T4.parquet')
    added=[c for c in registry['T4']['columns'] if c not in registry['B0']['columns']]
    frame=r4.hstack(t4.select(added))
    persist('H_T',frame,added,registry['R4']['columns']);del frame,t4
    f,names=extras(hist,'SYM',sources)
    persist('H_S',r4.hstack(numeric(f.select(names),names)),names,registry['R4']['columns'])
    for arm in ARMS:
        check();path=private/f'{arm}.parquet';frame=pl.read_parquet(path);cols=registry[arm]['columns']
        if not cols:raise ValueError('Empty arm')
        coverage={}
        for m in sorted(frame[MONTH].unique()):
            part=frame.filter(pl.col(MONTH)==m)
            coverage[str(m)]={c:part[c].null_count()/len(part) for c in cols}
        if selecting:
            registry[arm]['missing_fraction_by_month']=coverage
            registry[arm]['matrix_sha256']=sha(path)
            registry[arm]['n_columns']=len(cols)
            if arm!='B0' and cols==registry['B0']['columns']:raise ValueError('Non-identifiable arm '+arm)
    return registry

def payoff(ids,scores,y,cut):
    if not (0<=cut<=len(ids)) or len(set(ids))!=len(ids):raise ValueError('Invalid cut/IDs')
    if not np.isfinite(scores).all() or not np.isin(y,[0,1]).all():raise ValueError('Invalid predictions/outcomes')
    order=np.lexsort((ids,-scores));selected=order[:cut]
    d=np.zeros(len(ids),dtype=np.int64);d[selected]=np.where(y[selected],1072500,-27500)
    hits=int(y[selected].sum());gain=int(d.sum())
    assert gain==1100000*hits-27500*cut
    return {'contacts':int(cut),'hits':hits,'gain':gain},d

def bootstrap_joint(differences,replicates,seed):
    """Exact multinomial reduction of client resampling, preserving all paired contrasts."""
    patterns,counts=np.unique(differences,axis=0,return_counts=True)
    rng=np.random.default_rng(seed)
    draws=rng.multinomial(len(differences),counts/len(differences),size=replicates)
    return draws@patterns

class Runner:
    def __init__(self,a):
        self.cfg=json.loads(a.config.read_text());self.out=a.output;self.deadline=a.deadline
        self.start=time.time();self.fits=0
        c=self.cfg
        if not c.get('training_authorized') or not c.get('real_audit_approved'):raise ValueError('Real audit gate not approved')
        if c['data']['train_months']!=TRAIN or [x['id'] for x in c['arms']]!=ARMS:raise ValueError('Scope mismatch')
        if c['budget']['max_total_fits']!=150:raise ValueError('Fit budget mismatch')
        if c['hyperparameter_search']['trials_per_arm']!=10:raise ValueError('Trial budget mismatch')
        if len(c['evaluation']['seeds'])!=5 or len(set(c['evaluation']['seeds']))!=5 or c['hyperparameter_search']['model_seed'] in c['evaluation']['seeds']:raise ValueError('Invalid seeds')
        if not time.time()<a.deadline<=time.time()+21600:raise ValueError('Invalid deadline')
        if sha(a.dataset)!=c['data']['sha256']:raise ValueError('Dataset mismatch')
        audit_path=a.config.parent/c['real_audit_file']
        if sha(audit_path)!=c['real_audit_sha256']:raise ValueError('Audit report mismatch')
        if not c.get('sanitation_review',{}).get('resolved'):raise ValueError('Sanitation review unresolved')
        self.out.mkdir(parents=True,exist_ok=False);self.private=self.out/'private';self.private.mkdir()
        self.dataset=a.dataset
        save(self.out/'config_frozen.json',c)
        save(self.out/'code_identity.json',{p.name:sha(p) for p in Path(__file__).parent.glob('*.py')})
        from importlib.metadata import version
        save(self.out/'environment.json',{'python':sys.version,'platform':platform.platform(),
            'packages':{n:version(n) for n in ['numpy','polars','lightgbm','optuna','scikit-learn']},
            'threads':4,'argv':sys.argv})
        self.state('PREPARING')
        df=read_data(a.dataset,list(range(201901,201909)))
        meta=df.filter(pl.col(MONTH).is_in(TRAIN+[201908])).select([ID,MONTH,LABEL]).sort([ID,MONTH])
        if meta[LABEL].null_count() or not set(meta[LABEL].unique())<={'BAJA+1','BAJA+2','CONTINUA'}:raise ValueError('Invalid outcomes')
        hist,raw=history(df.drop(LABEL),c,TRAIN+[201908]);del df;gc.collect()
        self.registry=materialize(hist,raw,c,self.private,self.check);del hist;gc.collect()
        save(self.out/'feature_manifest.json',self.registry)
        meta.write_parquet(self.private/'meta.parquet')
        tr=meta.filter(pl.col(MONTH).is_in(TRAIN));va=meta.filter(pl.col(MONTH)==201908)
        self.yt=tr[LABEL].is_in(['BAJA+1','BAJA+2']).to_numpy().astype(np.int8)
        self.yv=(va[LABEL]=='BAJA+2').to_numpy().astype(np.int8);self.ids=va[ID].to_numpy()
        np.savez_compressed(self.private/'august_labels.npz',ids=self.ids,y=self.yv)
        save(self.out/'data_identity.json',{'train_rows':len(tr),'valid_rows':len(va),
            'train_keys_sha256':hashlib.sha256(tr.select([ID,MONTH]).to_numpy().tobytes()).hexdigest(),
            'valid_ids_sha256':hashlib.sha256(self.ids.tobytes()).hexdigest()})
        save(self.out/'audit_gate.json',{'passed':True,'fits_before_gate':0,'real_audit_sha256':c['real_audit_sha256']})
    def state(self,status,**kw):
        save(self.out/'status.json',{'status':status,'fits_started':self.fits,'epoch':time.time(),**kw});print(status,kw,flush=True)
    def check(self):
        import resource,shutil
        if time.time()>=self.deadline:raise TimeoutError('Hard deadline')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>48*2**30:raise MemoryError('48 GiB memory guard')
        if shutil.disk_usage(self.out).free<10*2**30:raise OSError('10 GiB disk guard')
    def params(self,hp,seed):
        return {**self.cfg['hyperparameter_search']['fixed'],**hp,'seed':seed,'feature_fraction_seed':seed,
            'bagging_seed':seed,'data_random_seed':seed,'feature_pre_filter':False,'verbosity':-1}
    def fit(self,xt,xv,hp,seed,rounds,early):
        self.check();self.fits+=1
        if self.fits>150:raise RuntimeError('Fit cap exceeded')
        self.state('FIT',seed=seed)
        ds=lgb.Dataset(xt,label=self.yt,feature_name=[f'f{i}' for i in range(xt.shape[1])])
        def guard(env):self.check()
        guard.order=0;guard.before_iteration=True
        callbacks=[guard];kw={}
        if early:
            callbacks.append(lgb.early_stopping(self.cfg['hyperparameter_search']['early_stopping_rounds'],verbose=False))
            kw['valid_sets']=[lgb.Dataset(xv,label=self.yv,reference=ds)]
        start=time.time();m=lgb.train(self.params(hp,seed),ds,num_boost_round=rounds,callbacks=callbacks,**kw)
        pred=m.predict(xv,num_threads=4)
        if not np.isfinite(pred).all():raise ValueError('Nonfinite scores')
        return m,pred,time.time()-start
    def train(self):
        self.policies={};self.common_k=None
        for arm in ARMS:
            frame=pl.read_parquet(self.private/f'{arm}.parquet');cols=self.registry[arm]['columns']
            xt=frame.filter(pl.col(MONTH).is_in(TRAIN)).select(cols).to_numpy(order='c')
            xv=frame.filter(pl.col(MONTH)==201908).select(cols).to_numpy(order='c');del frame
            path=self.out/arm;path.mkdir();dest=self.private/arm;dest.mkdir()
            search=self.cfg['hyperparameter_search'];trials=[]
            study=optuna.create_study(direction='maximize',sampler=optuna.samplers.TPESampler(
                seed=search['sampler_seed'],n_startup_trials=search['startup_trials']))
            def objective(trial):
                hp={n:(trial.suggest_int if v['type']=='int' else trial.suggest_float)(n,v['low'],v['high'],log=v.get('log',False)) for n,v in search['range'].items()}
                row={'trial':trial.number,'params':hp,'state':'RUNNING'};trials.append(row);save(path/'trials.json',trials)
                try:
                    m,p,seconds=self.fit(xt,xv,hp,search['model_seed'],search['max_rounds'],True)
                    auc=float(roc_auc_score(self.yv,p));row.update(state='COMPLETE',auc=auc,rounds=int(m.best_iteration),seconds=seconds)
                    trial.set_user_attr('rounds',int(m.best_iteration));return auc
                except Exception as e:row.update(state='FAIL',error=str(e));raise
                finally:save(path/'trials.json',trials)
            study.optimize(objective,n_trials=search['trials_per_arm'])
            best=study.best_trial;save(path/'best.json',{'trial':best.number,'auc':best.value,'params':best.params,'rounds':best.user_attrs['rounds']})
            predictions=[];seed_rows=[];pol={'seeds':{}};hashes={}
            for seed in self.cfg['evaluation']['seeds']:
                self.state('SEED',arm=arm,seed=seed)
                m,p,seconds=self.fit(xt,xv,best.params,seed,best.user_attrs['rounds'],False)
                m.save_model(str(dest/f'seed_{seed}.txt'))
                np.savez_compressed(dest/f'seed_{seed}.npz',ids=self.ids,prediction=p)
                own=evaluate_gain_curve(self.ids,p,self.yv)
                pol['seeds'][str(seed)]=own['contact_proportion'];predictions.append(p)
                seed_rows.append({'seed':seed,'auc':float(roc_auc_score(self.yv,p)),'own_policy_august':own,'seconds':seconds})
                hashes[str(seed)]={q.name:sha(q) for q in [dest/f'seed_{seed}.txt',dest/f'seed_{seed}.npz']}
                save(path/'seeds.json',seed_rows);save(path/'model_hashes.json',hashes)
                save(path/f'params_seed_{seed}.json',self.params(best.params,seed));del m
            ensemble=np.mean(predictions,axis=0);own=evaluate_gain_curve(self.ids,ensemble,self.yv)
            pol['ensemble']=own['contact_proportion'];pol['august_ensemble_cut']=own['cut_contacts'];self.policies[arm]=pol
            if arm=='B0':
                self.common_k=int(own['cut_contacts']);self.common_prop=self.common_k/len(self.ids)
                save(self.out/'common_policy.json',{'source':'B0 ensemble August','k_august':self.common_k,'n_august':len(self.ids),'proportion':self.common_prop})
            np.savez_compressed(dest/'ensemble.npz',ids=self.ids,prediction=ensemble)
            for row,p in zip(seed_rows,predictions):row['common']=payoff(self.ids,p,self.yv,self.common_k)[0]
            save(path/'result_august.json',{'arm':arm,'seeds':seed_rows,'ensemble_auc':float(roc_auc_score(self.yv,ensemble)),
                'common':payoff(self.ids,ensemble,self.yv,self.common_k)[0],'own_policy_august':own})
            save(self.out/'policies_draft.json',self.policies)
            del xt,xv,predictions,ensemble;gc.collect()
        self.compare_month(201908,self.ids,self.yv,self.common_k,self.private)
        frozen={'policies':self.policies,'common_proportion':self.common_prop,'common_august_k':self.common_k,
            'source_hashes':{p.name:sha(p) for p in [self.out/'config_frozen.json',self.out/'feature_manifest.json',self.out/'comparisons_201908.json']},
            'models':{arm:json.loads((self.out/arm/'model_hashes.json').read_text()) for arm in ARMS}}
        save(self.out/'policy_frozen.json',frozen)
        self.state('DEVELOPMENT_FROZEN')
    def compare_month(self,month,ids,y,cut,private):
        rows=[];diffs=[]
        for arm,control in self.cfg['comparisons']:
            a=np.load(private/arm/'ensemble.npz')['prediction'];b=np.load(private/control/'ensemble.npz')['prediction']
            ga,pa=payoff(ids,a,y,cut);gb,pb=payoff(ids,b,y,cut);d=pa-pb;diffs.append(d)
            seed_deltas=[]
            for seed in self.cfg['evaluation']['seeds']:
                x=np.load(private/arm/f'seed_{seed}.npz')['prediction'];z=np.load(private/control/f'seed_{seed}.npz')['prediction']
                seed_deltas.append(payoff(ids,x,y,cut)[0]['gain']-payoff(ids,z,y,cut)[0]['gain'])
            rows.append({'arm':arm,'control':control,'month':month,'common_contacts':cut,'ensemble_delta':int(d.sum()),
                'paired_seed_deltas':seed_deltas,'mean_seed_delta':float(np.mean(seed_deltas)),
                'median_seed_delta':float(np.median(seed_deltas)),'sd_seed_delta':float(np.std(seed_deltas,ddof=1)),
                'worst_seed_delta':min(seed_deltas),'wins':sum(v>0 for v in seed_deltas),
                'descriptive_favorable':bool(d.sum()>0 and np.mean(seed_deltas)>0),
                'primary':[arm,control] in self.cfg['primary_comparisons']})
        self.check();bs=self.cfg['evaluation']['bootstrap']
        dist=bootstrap_joint(np.stack(diffs,axis=1),bs['replicates'],bs['seed'])
        for j,row in enumerate(rows):
            row['ci95_fixed_selection']=np.quantile(dist[:,j],[.025,.975]).tolist()
            if row['primary']:row['ci_bonferroni_3']=np.quantile(dist[:,j],[1/120,119/120]).tolist()
        save(self.out/f'comparisons_{month}.json',{'rows':rows,'replicates':bs['replicates'],'seed':bs['seed'],
            'scope':'conditional fixed-contribution client bootstrap; exploratory, not full fitting uncertainty'})
    def october(self):
        self.check();frozen=json.loads((self.out/'policy_frozen.json').read_text())
        for name,h in frozen['source_hashes'].items():
            if sha(self.out/name)!=h:raise ValueError('Frozen source mismatch')
        for arm,hashes in frozen['models'].items():
            for files in hashes.values():
                for name,h in files.items():
                    if sha(self.private/arm/name)!=h:raise ValueError('Frozen artifact mismatch')
        octdir=self.private/'october';octdir.mkdir()
        # Read features without October labels, rebuild August+October with frozen columns.
        df=read_data(self.dataset,list(range(201901,201911)),labels=False)
        hist,raw=history(df,self.cfg,[201908,201910]);del df;gc.collect()
        materialize(hist,raw,self.cfg,octdir,self.check,self.registry);del hist;gc.collect()
        verification={};octids=None
        for arm in ARMS:
            self.state('VERIFY_AUGUST_AND_SCORE_OCTOBER',arm=arm)
            frame=pl.read_parquet(octdir/f'{arm}.parquet');cols=self.registry[arm]['columns']
            va=frame.filter(pl.col(MONTH)==201908);ot=frame.filter(pl.col(MONTH)==201910)
            if not np.array_equal(va[ID].to_numpy(),self.ids):raise ValueError('August IDs changed')
            ids=ot[ID].to_numpy()
            if octids is None:octids=ids
            if not np.array_equal(ids,octids):raise ValueError('October IDs differ between arms')
            x=va.select(cols).to_numpy(order='c');xo=ot.select(cols).to_numpy(order='c');preds=[]
            dest=octdir/arm;dest.mkdir();verification[arm]={}
            for seed in self.cfg['evaluation']['seeds']:
                self.check();m=lgb.Booster(model_file=str(self.private/arm/f'seed_{seed}.txt'))
                p=m.predict(x,num_threads=4);stored=np.load(self.private/arm/f'seed_{seed}.npz')
                if not np.array_equal(p,stored['prediction']):raise ValueError('August predictions not exactly reproduced')
                verification[arm][str(seed)]={'exact':True,'max_error':0.0}
                po=m.predict(xo,num_threads=4);preds.append(po)
                np.savez_compressed(dest/f'seed_{seed}.npz',ids=ids,prediction=po)
            np.savez_compressed(dest/'ensemble.npz',ids=ids,prediction=np.mean(preds,axis=0))
            save(self.out/'august_verification.json',verification)
            del frame,va,ot,x,xo,preds;gc.collect()
        # Outcome labels become available only after policies/model checks and prediction regeneration.
        labels=pl.scan_csv(self.dataset,infer_schema_length=20000).select([ID,MONTH,LABEL]).filter(pl.col(MONTH)==201910).sort(ID).collect()
        if not np.array_equal(labels[ID].to_numpy(),octids):raise ValueError('October label mismatch')
        if labels[LABEL].null_count() or not set(labels[LABEL].unique())<={'BAJA+1','BAJA+2','CONTINUA'}:raise ValueError('Invalid October labels')
        y=(labels[LABEL]=='BAJA+2').to_numpy().astype(np.int8);cut=int(np.floor(self.common_prop*len(y)))
        np.savez_compressed(octdir/'labels.npz',ids=octids,y=y)
        for arm in ARMS:
            rows=[]
            for seed in self.cfg['evaluation']['seeds']:
                pred=np.load(octdir/arm/f'seed_{seed}.npz')['prediction'];owncut=int(np.floor(self.policies[arm]['seeds'][str(seed)]*len(y)))
                rows.append({'seed':seed,'auc':float(roc_auc_score(y,pred)),'common':payoff(octids,pred,y,cut)[0],
                    'own':payoff(octids,pred,y,owncut)[0]})
            pred=np.load(octdir/arm/'ensemble.npz')['prediction'];owncut=int(np.floor(self.policies[arm]['ensemble']*len(y)))
            save(self.out/arm/'result_october.json',{'arm':arm,'seeds':rows,'ensemble_auc':float(roc_auc_score(y,pred)),
                'common':payoff(octids,pred,y,cut)[0],'own':payoff(octids,pred,y,owncut)[0]})
        self.compare_month(201910,octids,y,cut,octdir)
        save(self.out/'private_manifest.json',{str(p.relative_to(self.private)):sha(p) for p in self.private.rglob('*') if p.is_file()})
        save(self.out/'FINAL.json',{'status':'COMPLETE_EXPLORATORY','fits':self.fits,'seconds':time.time()-self.start,
            'arms':ARMS,'common_august_contacts':self.common_k,'common_october_contacts':cut,
            'independent_full_rerun':False,'august_predictions_regenerated':50})
        self.state('COMPLETE')

def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);p.add_argument('--config',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--deadline',type=float,required=True);a=p.parse_args()
    try:
        runner=Runner(a);runner.train();runner.october()
    except Exception as e:
        if a.output.exists():save(a.output/'ERROR.json',{'error':str(e),'epoch':time.time()})
        traceback.print_exc();raise
if __name__=='__main__':main()
