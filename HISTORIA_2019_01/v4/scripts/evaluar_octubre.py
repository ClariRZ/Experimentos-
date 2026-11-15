"""Evaluacion cerrada de octubre: solo inferencia, sin ajuste ni busqueda de corte."""
import argparse, gc, hashlib, importlib.util, json, sys, time
from pathlib import Path
import numpy as np
import polars as pl
import lightgbm as lgb
from sklearn.metrics import roc_auc_score

ID='numero_de_cliente'; MONTH='foto_mes'; LABEL='clase_ternaria'
ARMS=['B0','F1','F3','F4a','F4b']; SEEDS=[101,211,307,401,503]

def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def save(p, obj):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix('.tmp'); tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n'); tmp.replace(p)

def run(a):
    started=time.time(); a.output.mkdir(parents=True,exist_ok=False)
    private=a.output/'private'; private.mkdir()
    sys.path.insert(0,str(a.root/'scripts'))
    import fe_core as fe
    spec=importlib.util.spec_from_file_location('audit',a.root/'scripts/01_full_audit.py')
    audit=importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
    cfg=json.loads((a.prior/'config_frozen.json').read_text())
    registry=json.loads((a.prior/'feature_manifest.json').read_text())
    expected=json.loads(a.expected.read_text())
    identity=json.loads((a.prior/'code_identity.json').read_text())
    for name in ['fe_core.py','01_full_audit.py']:
        assert sha(a.root/'scripts'/name)==identity[name], f'Codigo cambiado: {name}'
    assert sha(a.dataset)==cfg['data']['sha256']
    assert cfg['evaluation']['seeds']==SEEDS
    frozen={}
    for arm in ARMS:
        previous=json.loads((a.prior/arm/'result.json').read_text())
        assert previous==expected[arm], f'Resultado agosto distinto: {arm}'
        assert [x['seed'] for x in previous['seeds']]==SEEDS
        frozen[arm]={'proportion':previous['ensemble_gain']['contact_proportion'],
                     'august_ensemble_gain':previous['ensemble_gain'],
                     'columns':registry[arm]['columns'],
                     'models':{str(s):sha(a.prior/'private'/arm/f'seed_{s}.txt') for s in SEEDS},
                     'august_result_sha256':sha(a.prior/arm/'result.json')}
    # Persistir todas las decisiones antes de leer las etiquetas de octubre.
    save(a.output/'protocolo_congelado.json',{
        'authorized_user_request':'hagmaos no? (evaluar octubre con modelos y cortes congelados)',
        'prior':str(a.prior),'dataset_sha256':cfg['data']['sha256'],
        'evaluator_sha256':sha(__file__),'created_epoch':time.time(),
        'training':False,'refit':False,'cut_search_october':False,
        'test_month':201910,'auc_positive':'BAJA+2','gain_hit':1072500,'gain_miss':-27500,
        'cut_policy':'floor(August ensemble proportion per arm * N_october); same per-arm cut for all seeds and ensemble',
        'comparison':'all four variants vs B0, F4b additionally vs F4a; no model reselection',
        'limitations':['Group October results already known before this evaluation.',
                       'Five seeds measure algorithmic variation, not five independent test periods.',
                       'No new sanitization based on October. Nine original masks retained.'],
        'frozen':frozen})
    print('PROTOCOLO_CONGELADO',flush=True)
    scan=pl.scan_csv(a.dataset,infer_schema_length=20000)
    # Ventanas W3 de agosto y octubre necesitan junio a octubre. No hay informacion futura.
    df=scan.filter(pl.col(MONTH).is_between(201906,201910)).drop(LABEL).collect()
    assert set(df[MONTH].unique())==set(range(201906,201911))
    df,_=audit.normalize_mobile_count(df)
    if not df['tmobile_app'].dtype.is_numeric(): df=df.with_columns(pl.col('tmobile_app').cast(pl.Float64,strict=True))
    raw=[c for c in df.columns if c not in [ID,MONTH]]
    df=fe.sanitize_base(df,raw,{int(k):v for k,v in cfg['data']['broken_masks'].items()}).sort([ID,MONTH])
    sources=cfg['data']['history_sources']; active=pl.col(MONTH).is_in([201908,201910])
    meta=df.filter(active).select([ID,MONTH]); meta.write_parquet(private/'meta.parquet')
    hist=fe.add_baseline_lags_deltas(fe.build_exact_lags(df,sources,2),sources)
    def materialize(arm, frame):
        cols=frozen[arm]['columns']
        frame=frame.filter(active).select([ID,MONTH,*cols]).with_columns([
            pl.when(pl.col(c).cast(pl.Float32,strict=True).is_finite())
              .then(pl.col(c).cast(pl.Float32,strict=True)).otherwise(None).alias(c) for c in cols])
        assert frame.select([ID,MONTH]).equals(meta)
        aug=frame.filter(pl.col(MONTH)==201908)
        old=pl.read_parquet(a.prior/'private'/f'{arm}.parquet').filter(pl.col(MONTH)==201908)
        assert aug.equals(old.select(aug.columns)), f'Matriz agosto no reproduce: {arm}'
        frame.write_parquet(private/f'{arm}.parquet')
        print('MATRIZ_VERIFICADA',arm,len(cols),flush=True)
    materialize('B0',hist)
    for arm,f1,f3 in [('F1',True,False),('F3',False,True)]:
        frame=fe.build_window_families(hist,sources,3,include_f1=f1,include_f2=False,include_f3=f3)
        materialize(arm,frame); del frame; gc.collect()
    base=hist.filter(active).select([ID,MONTH,*frozen['B0']['columns']]); del hist; gc.collect()
    ranks=fe.build_monthly_rankings(df.select([ID,MONTH,*sources]),sources)
    rc=[f'{c}__rk0' for c in sources]; ranks=ranks.select([ID,MONTH,*rc]); del df; gc.collect()
    current=base.hstack(ranks.filter(active).select(rc)); materialize('F4a',current)
    ranks=fe.add_baseline_lags_deltas(fe.build_exact_lags(ranks,rc,2),rc)
    ranks=fe.build_window_families(ranks,rc,3,include_f1=True,include_f2=False,include_f3=False)
    names=[c for c in ranks.columns if c not in [ID,MONTH,*rc]]
    materialize('F4b',current.hstack(ranks.filter(active).select(names)))
    del ranks,current,base; gc.collect()
    checks={}; ids=meta.filter(pl.col(MONTH)==201910)[ID].to_numpy()
    assert len(ids)==len(np.unique(ids))
    for arm in ARMS:
        frame=pl.read_parquet(private/f'{arm}.parquet'); cols=frozen[arm]['columns']
        aug=frame.filter(pl.col(MONTH)==201908); octo=frame.filter(pl.col(MONTH)==201910)
        xa=aug.select(cols).to_numpy(order='c'); xo=octo.select(cols).to_numpy(order='c')
        predictions=[]; checks[arm]=[]
        for s in SEEDS:
            model_path=a.prior/'private'/arm/f'seed_{s}.txt'
            assert sha(model_path)==frozen[arm]['models'][str(s)]
            model=lgb.Booster(model_file=str(model_path)); assert model.num_feature()==len(cols)
            old=np.load(a.prior/'private'/arm/f'seed_{s}.npz')
            assert np.array_equal(old['ids'],aug[ID].to_numpy())
            pa=model.predict(xa,num_threads=4)
            assert np.allclose(pa,old['prediction'],rtol=0,atol=1e-12),f'Prediccion agosto distinta {arm}/{s}'
            pred=model.predict(xo,num_threads=4); assert np.isfinite(pred).all()
            np.savez_compressed(private/f'{arm}_{s}_octubre.npz',ids=ids,prediction=pred)
            predictions.append(pred)
            checks[arm].append({'seed':s,'august_max_abs_error':float(np.max(np.abs(pa-old['prediction']))),
                                'prediction_sha256':sha(private/f'{arm}_{s}_octubre.npz')})
        np.savez_compressed(private/f'{arm}_ensemble_octubre.npz',ids=ids,prediction=np.mean(predictions,axis=0))
        del frame,aug,octo,xa,xo,predictions,model; gc.collect()
        print('PREDICCIONES_CONGELADAS',arm,flush=True)
    save(a.output/'verificaciones.json',checks)
    # Solo despues de congelar todas las predicciones, abrir etiquetas para puntuar.
    labels=scan.filter(pl.col(MONTH)==201910).select([ID,LABEL]).collect().sort(ID)
    assert np.array_equal(labels[ID].to_numpy(),ids)
    assert labels[LABEL].null_count()==0 and set(labels[LABEL].unique())<={'BAJA+1','BAJA+2','CONTINUA'}
    y=(labels[LABEL]=='BAJA+2').to_numpy().astype(np.int8); assert len(np.unique(y))==2
    results={}
    for arm in ARMS:
        p=frozen[arm]['proportion']; rows=[]
        def evaluate(scores):
            return {'auc':float(roc_auc_score(y,scores)),**fe.evaluate_gain_curve(ids,scores,y,frozen_prop=p)}
        for s in SEEDS:
            rows.append({'seed':s,**evaluate(np.load(private/f'{arm}_{s}_octubre.npz')['prediction'])})
        ens=evaluate(np.load(private/f'{arm}_ensemble_octubre.npz')['prediction'])
        results[arm]={'seeds':rows,'ensemble':ens,'gain_mean':float(np.mean([x['point_gain'] for x in rows])),
                      'gain_sd':float(np.std([x['point_gain'] for x in rows],ddof=1)),
                      'auc_mean':float(np.mean([x['auc'] for x in rows]))}
    comparisons=[]
    for arm,control in [(x,'B0') for x in ARMS[1:]]+[('F4b','F4a')]:
        dg=np.array([x['point_gain']-z['point_gain'] for x,z in zip(results[arm]['seeds'],results[control]['seeds'])])
        comparisons.append({'arm':arm,'control':control,'paired_gain_deltas':dg.tolist(),
                            'delta_mean':float(dg.mean()),'delta_sd':float(dg.std(ddof=1)),
                            'wins':int((dg>0).sum()),'ensemble_delta':results[arm]['ensemble']['point_gain']-results[control]['ensemble']['point_gain']})
    final={'status':'OCTUBRE_EVALUADO_SIN_REENTRENAR','n_clients':len(ids),'baja2':int(y.sum()),
           'seconds':time.time()-started,'new_fits':0,'results':results,'comparisons':comparisons,
           'no_selection_on_october':True,'note':'Evaluacion con exposicion previa a resultados grupales de octubre; no test virgen.'}
    save(a.output/'FINAL.json',final); print(json.dumps(final),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['root','prior','dataset','output','expected']: p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    try: run(a)
    except Exception as e:
        if a.output.exists(): save(a.output/'ERROR.json',{'error':str(e),'type':type(e).__name__})
        raise
