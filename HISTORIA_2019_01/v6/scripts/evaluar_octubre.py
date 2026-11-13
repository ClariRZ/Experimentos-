"""Inference only: frozen v6 columns/models and August policies; never fits/selects."""
import argparse,gc,json,time,sys
from pathlib import Path
import numpy as np
import polars as pl
import lightgbm as lgb
from sklearn.metrics import roc_auc_score
from ejecutar_etapa1 import save,sha,model_values,audit,ID,MONTH,LABEL
from fe_core import sanitize_base,month_to_idx,add_baseline_lags_deltas,build_window_families,evaluate_gain_curve

def build_history(df,cfg):
    df,_=audit.normalize_mobile_count(df)
    if not df['tmobile_app'].dtype.is_numeric():df=df.with_columns(pl.col('tmobile_app').cast(pl.Float64,strict=True))
    raw=[c for c in df.columns if c not in [ID,MONTH,LABEL]]
    df=sanitize_base(df,raw,{int(k):v for k,v in cfg['data']['broken_masks'].items()}).sort([ID,MONTH])
    sources=cfg['data']['history_sources'];lookup=df.with_columns(month_to_idx().alias('_idx'))
    hist=lookup.filter(pl.col(MONTH).is_in([201908,201910]))
    for k in range(1,6):
        part=lookup.select(pl.col(ID),(pl.col('_idx')+k).alias('_idx'),*[pl.col(c).cast(pl.Float64).alias(f'{c}__lag{k}') for c in sources])
        hist=hist.join(part,on=[ID,'_idx'],how='left').sort([ID,MONTH])
    return add_baseline_lags_deltas(hist.drop('_idx'),sources)

def arm_frame(hist,arm,cols,sources):
    if arm[0] in 'STR':
        family=arm[0];w=int(arm[1:]);frame=build_window_families(hist,sources,w,include_f1=family=='S',include_f2=family=='T',include_f3=family=='R')
    else:frame=hist
    return model_values(frame.select([ID,MONTH,*cols]),cols)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--policy',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    started=time.time();s=a.source;o=a.output;o.mkdir(parents=True,exist_ok=False);private=o/'private';private.mkdir()
    policy=json.loads(a.policy.read_text());cfg=json.loads((s/'config_frozen.json').read_text());manifest=json.loads((s/'feature_manifest.json').read_text())
    assert policy['training_authorized'] is False and policy['test_month']==201910
    for name,h in policy['source_hashes'].items():assert sha(s/name)==h,('source_hash',name)
    assert sha(a.dataset)==cfg['data']['sha256']
    save(o/'policy_frozen.json',policy);save(o/'code_identity.json',{x.name:sha(x) for x in Path(__file__).parent.glob('*.py')})
    # All arms, seed policies and feature names were frozen before reading outcomes.
    for arm,pol in policy['arms'].items():
        hashes=json.loads((s/arm/'private_artifacts_sha256.json').read_text())
        for files in hashes.values():
            for name,h in files.items():assert sha(s/'private'/arm/name)==h,(arm,name)
    save(o/'integrity_gate.json',{'passed':True,'dataset_sha256':sha(a.dataset),'models_verified':len(policy['arms'])*5,'training_fits':0})
    df=pl.scan_csv(a.dataset,infer_schema_length=20000).filter(pl.col(MONTH).is_between(201901,201910)).collect()
    assert set(df[MONTH].unique())==set(range(201901,201911))
    assert not df.select([ID,MONTH]).is_duplicated().any()
    meta=df.filter(pl.col(MONTH).is_in([201908,201910])).select([ID,MONTH,LABEL]).sort([ID,MONTH])
    assert meta[LABEL].null_count()==0 and set(meta[LABEL].unique())<={'CONTINUA','BAJA+1','BAJA+2'}
    hist=build_history(df.drop(LABEL),cfg);del df;gc.collect()
    ids={m:meta.filter(pl.col(MONTH)==m)[ID].to_numpy() for m in [201908,201910]}
    y=(meta.filter(pl.col(MONTH)==201910)[LABEL]=='BAJA+2').to_numpy().astype(np.int8)
    np.savez_compressed(private/'october_labels.npz',ids=ids[201910],is_baja2=y)
    # Gate: rebuild August features with frozen columns and reproduce all 55 predictions exactly.
    verification={}
    for arm,pol in policy['arms'].items():
        frame=arm_frame(hist,arm,manifest[arm]['columns'],cfg['data']['history_sources'])
        assert frame.select([ID,MONTH]).equals(meta.select([ID,MONTH]))
        x=frame.filter(pl.col(MONTH)==201908).select(manifest[arm]['columns']).to_numpy(order='c')
        xo=frame.filter(pl.col(MONTH)==201910).select(manifest[arm]['columns']).to_numpy(order='c')
        np.save(private/f'{arm}_october.npy',xo);del xo
        verification[arm]={}
        for seed in pol['seeds']:
            m=lgb.Booster(model_file=str(s/'private'/arm/f'seed_{seed}.txt'));stored=np.load(s/'private'/arm/f'seed_{seed}.npz')
            pred=m.predict(x,num_threads=4)
            assert np.array_equal(ids[201908],stored['ids'])
            assert np.array_equal(pred,stored['prediction']),(arm,seed,'August prediction mismatch')
            verification[arm][seed]={'exact':True,'max_error':float(np.max(np.abs(pred-stored['prediction'])))}
        save(o/'august_verification.json',verification);print('AUGUST_VERIFIED',arm,flush=True);del frame,x;gc.collect()
    del hist;gc.collect();save(o/'october_gate.json',{'all_55_august_predictions_exact':True,'training_fits':0})
    results={}
    for arm,pol in policy['arms'].items():
        x=np.load(private/f'{arm}_october.npy',mmap_mode='r');rows=[];preds=[]
        for seed,prop in pol['seeds'].items():
            m=lgb.Booster(model_file=str(s/'private'/arm/f'seed_{seed}.txt'));pred=m.predict(x,num_threads=4);assert np.isfinite(pred).all()
            gain=evaluate_gain_curve(ids[201910],pred,y,frozen_prop=prop)
            rows.append({'seed':int(seed),'frozen_august_proportion':prop,'auc':float(roc_auc_score(y,pred)),'gain':gain});preds.append(pred)
            np.savez_compressed(private/f'{arm}_{seed}.npz',ids=ids[201910],prediction=pred)
        ensemble=np.mean(preds,axis=0);np.savez_compressed(private/f'{arm}_ensemble.npz',ids=ids[201910],prediction=ensemble)
        result={'arm':arm,'seeds':rows,'ensemble_auc':float(roc_auc_score(y,ensemble)),'frozen_august_proportion':pol['ensemble'],'ensemble_gain':evaluate_gain_curve(ids[201910],ensemble,y,frozen_prop=pol['ensemble'])}
        save(o/arm/'result.json',result);results[arm]=result;print('OCTOBER_SCORED',arm,flush=True);del x,preds;gc.collect()
    comparisons=[]
    for arm,control in cfg['comparisons']:
        aa=results[arm];bb=results[control];d=[a['gain']['point_gain']-b['gain']['point_gain'] for a,b in zip(aa['seeds'],bb['seeds'])]
        comparisons.append({'arm':arm,'control':control,'ensemble_gain_delta':aa['ensemble_gain']['point_gain']-bb['ensemble_gain']['point_gain'],'paired_seed_deltas':d,'mean_seed_delta':float(np.mean(d)),'gain_wins':sum(x>0 for x in d)})
    save(o/'private_artifacts_sha256.json',{q.name:sha(q) for q in private.glob('*.npz')})
    save(o/'FINAL.json',{'status':'OCTOBER_EVALUATED','training_fits':0,'n_october':len(y),'arms':list(results),'comparisons':comparisons,'seconds':time.time()-started,'warning':'Exploratory: October was observed in earlier experiments; no tuning, threshold selection or retraining in this evaluation.'})
if __name__=='__main__':main()
