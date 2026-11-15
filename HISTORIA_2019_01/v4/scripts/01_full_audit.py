"""Auditoria sin LightGBM ni Optuna. Las fuentes requieren revision semantica."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import polars as pl
from fe_core import sanitize_base, build_exact_lags, add_baseline_lags_deltas, build_window_families, build_monthly_rankings

ROOT = Path(__file__).resolve().parents[1]
TRAIN = [201903,201904,201905,201906]
SEEDS = [101,211,307,401,503,601,701,809,907,1009,1103,1201,1301,1409,1511,1601,1709,1801,1901,2003]
META = {'numero_de_cliente','foto_mes','clase_ternaria'}

def dump(path, obj):
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)

def validate(df):
    needed=set(range(201901,201909))
    if set(df['foto_mes'].unique()) != needed:
        raise ValueError('Faltan meses de enero a agosto o hay meses no permitidos')
    if df.select(pl.any_horizontal([pl.col(c).is_null() for c in ('numero_de_cliente','foto_mes')]).any()).item():
        raise ValueError('Clave nula')
    if df.select(['numero_de_cliente','foto_mes']).is_duplicated().any():
        raise ValueError('Clave duplicada')
    labels=df.filter(pl.col('foto_mes').is_in(TRAIN+[201908]))['clase_ternaria']
    if labels.null_count() or not set(labels.unique()) <= {'CONTINUA','BAJA+1','BAJA+2'}:
        raise ValueError('Etiquetas invalidas o nulas')

def coverage(df, cols, months):
    report={c:{} for c in cols}
    for m in months:
        part=df.filter(pl.col('foto_mes')==m)
        if not part.height: raise ValueError(f'Mes ausente: {m}')
        values=part.select([(pl.col(c).is_not_null() & pl.col(c).is_finite()).sum().alias(c) for c in cols]).to_dicts()[0] if cols else {}
        for c in cols: report[c][str(m)]=values[c]/part.height
    return report

def redundancies(df, cols):
    # Hash solo agrupa candidatos; igualdad completa confirma cada duplicado.
    groups={}; result={}
    for c in cols:
        s=df[c]
        if s.drop_nulls().n_unique()<=1:
            result[c]='constante'; continue
        sig=int(s.hash(seed=2026).sum())
        for old in groups.get(sig,[]):
            if s.equals(df[old],check_dtypes=False):
                result[c]='duplicada_de:'+old; break
        groups.setdefault(sig,[]).append(c)
    return result

def validate_seeds(cfg, prior):
    if cfg.get('seeds') != SEEDS or len(set(cfg['seeds']))!=20:
        raise ValueError('Semillas no coinciden con las 20 existentes')
    observed=prior.get('seeds', prior.get('semillas'))
    if observed != SEEDS: raise ValueError('Artefacto previo no confirma las semillas')

def select_sources(df, raw, cfg):
    numeric=[c for c in raw if df.schema[c].is_numeric()]
    if cfg['sources_reviewed']:
        sources=cfg['history_sources']
    else:
        train=df.filter(pl.col('foto_mes').is_in(TRAIN))
        sources=[c for c in numeric if train[c].drop_nulls().n_unique()>2]
    if not sources or len(sources)!=len(set(sources)) or set(sources)-set(numeric):
        raise ValueError('Fuentes vacias, repetidas, ausentes o no numericas')
    # Una cantidad puede tomar solo 0/1. La semantica proviene del diccionario;
    # cobertura y constantes se informan luego, sin invalidar la fuente completa.
    return sources

def normalize_mobile_count(df):
    c='cmobile_app_trx'
    if c not in df.columns or df.schema[c].is_numeric():
        return df, []
    # El diccionario define un conteo. Conversion estricta, sin imputar nulos.
    return df.with_columns(pl.col(c).cast(pl.Float64, strict=True)), [c]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dataset',type=Path,required=True)
    p.add_argument('--prior-config',type=Path,required=True,help='Configuracion previa con lista seeds verificable')
    p.add_argument('--config',type=Path,default=ROOT/'configuraciones/auditoria.json')
    p.add_argument('--output',type=Path,required=True,help='Directorio nuevo, nunca sobreescribir auditorias')
    a=p.parse_args()
    cfg=json.loads(a.config.read_text()); prior=json.loads(a.prior_config.read_text())
    validate_seeds(cfg,prior)
    with a.dataset.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
    if digest!=cfg['expected_dataset_sha256']: raise ValueError('Dataset distinto del verificado')
    lf=pl.scan_parquet(a.dataset) if a.dataset.suffix=='.parquet' else pl.scan_csv(a.dataset,infer_schema_length=20000)
    # No se calculan estadisticas ni resultados de octubre; CSV debe leerse para filtrar.
    df=lf.filter(pl.col('foto_mes').is_between(201901,201908)).collect()
    validate(df)
    raw=[c for c in df.columns if c not in META]
    masks={int(k):v for k,v in cfg['broken_masks'].items()}
    if len(masks.get(201904,[]))!=2 or len(masks.get(201905,[]))!=7:
        raise ValueError('Mascaras de saneamiento incompletas')
    absent=set(sum(masks.values(),[]))-set(raw)
    if absent: raise ValueError(f'Faltan variables saneadas: {absent}')
    df, numeric_casts = normalize_mobile_count(df)
    df=sanitize_base(df,raw,masks)
    train=df.filter(pl.col('foto_mes').is_in(TRAIN))
    reviewed=bool(cfg['sources_reviewed'])
    sources=select_sources(df, raw, cfg)
    base=[c for c in raw if train[c].null_count()<train.height]
    hist=build_exact_lags(df.filter(pl.col('foto_mes')<=201906),sources,5)
    hist=add_baseline_lags_deltas(hist,sources)
    baseline=base+[f'{c}__{t}' for c in sources for t in ['lag1','lag2','delta1','delta2']]
    threshold=cfg['coverage_threshold']
    if not 0<=threshold<=1: raise ValueError('Cobertura fuera de rango')
    report={'status':'AUDITADO' if reviewed else 'FUENTES_PROPUESTAS_REQUIEREN_REVISION','dataset_sha256':digest,'prior_config':str(a.prior_config),'seeds':SEEDS,'baseline_columns':baseline,'baseline_count':len(baseline),'sources':sources,'sources_reviewed':reviewed,'threshold':threshold,'training_executed':False,'october_outcomes_used':False,'hardware':{'cpus':os.cpu_count(),'disk_free_bytes':shutil.disk_usage(ROOT).free,'meminfo':Path('/proc/meminfo').read_text()},'families':{}}
    for L in [3,4,6]:
        w=build_window_families(hist,sources,L,include_f2=True)
        cols=[c for c in w.columns if c.endswith(f'_W{L}')]
        for branch,months in [('R2',[201906])]+([('R1',TRAIN)] if L==3 else []):
            names=[c for c in cols if branch!='R1' or '__f2_' not in c]
            cov=coverage(w,names,months)
            report['families'][f'{branch}_W{L}']={'coverage':cov,'redundancies_report_only':redundancies(w.filter(pl.col('foto_mes').is_in(months)),names),'passing':[c for c in names if min(cov[c].values())>=threshold]}
    report['numeric_casts']=numeric_casts
    report['monthly_rows']=df.group_by('foto_mes').len().sort('foto_mes').to_dicts()
    # Comparabilidad por pareja fuente-formula. No expulsar fuente por otro ratio ausente.
    normalized=[]
    for L in [3,4,6]:
        normalized.append({c.rsplit('_W',1)[0] for c in report['families'][f'R2_W{L}']['passing']})
    report['r2_common_source_formula_pairs']=sorted(set.intersection(*normalized))
    rk=build_monthly_rankings(df.filter(pl.col('foto_mes')<=201906),sources)
    rc=[f'{c}__rk0' for c in sources]
    rk=add_baseline_lags_deltas(build_exact_lags(rk,rc,2),rc)
    rk=build_window_families(rk,rc,3,include_f2=False,include_f3=False)
    history=[f'{c}__{t}' for c in rc for t in ['lag1','lag2','delta1','delta2','f1_mean_W3','f1_min_W3','f1_max_W3','f1_range_W3']]
    report['rank_recipe']='rango promedio mensual / cantidad no nula; ceros incluidos'
    report['rank_current_coverage']=coverage(rk,rc,TRAIN)
    report['rank_history_coverage']=coverage(rk,history,TRAIN)
    a.output.mkdir(parents=True,exist_ok=False)
    dump(a.output/'audit_summary.json',report)
    print(report['status'],a.output/'audit_summary.json')

if __name__=='__main__': main()
