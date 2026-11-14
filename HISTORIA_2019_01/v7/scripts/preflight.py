"""Read-only provenance and environment checks; no fitting or outcome access."""
import json
import platform
import sys
from importlib.metadata import distributions,version
from pathlib import Path
import numpy as np
import polars as pl
from fe_core import month_to_idx


def capture_environment(cfg):
    packages={n:version(n) for n in ['numpy','polars','lightgbm','optuna','scikit-learn']}
    expected=cfg.get('runtime',{})
    if expected.get('packages') and packages!=expected['packages']:
        raise ValueError('Runtime packages differ from validated contract')
    if expected.get('python_major_minor') and list(sys.version_info[:2])!=expected['python_major_minor']:
        raise ValueError('Python version differs from validated contract')
    # Distribution metadata can include two installations on sys.path. Preserve all records.
    installed=sorted([{'name':d.metadata.get('Name',''),'version':d.version,'location':str(d.locate_file(''))} for d in distributions()],key=lambda d:(d['name'],d['version'],d['location']))
    return {'python':sys.version,'platform':platform.platform(),'packages':packages,
            'distributions':installed,'executable':sys.executable,'sys_path':sys.path,'frozen_before_fit':True}


def coverage_provenance(df,cfg,target_months):
    if 'clase_ternaria' in df.columns:raise ValueError('Labels prohibited in quality report')
    names=cfg['data']['history_sources'];masks=cfg['data']['broken_masks']
    expressions=[]
    # Exclusive reason priority: sanitation, original null, nonfinite, observed.
    for c in names:
        months=[int(m) for m,cols in masks.items() if c in cols]
        x=pl.col(c).cast(pl.Float64)
        expressions.append(pl.when(pl.col('foto_mes').is_in(months)).then(3)
            .when(x.is_null()).then(2).when(~x.is_finite()).then(4).otherwise(0).cast(pl.UInt8).alias(c))
    lookup=df.select('numero_de_cliente','foto_mes',*expressions).with_columns(month_to_idx().alias('_idx'))
    keys=lookup.filter(pl.col('foto_mes').is_in(target_months)).select('numero_de_cliente','foto_mes','_idx').sort(['numero_de_cliente','foto_mes'])
    frames=[]
    for k in range(4):
        right=lookup.select('numero_de_cliente',(pl.col('_idx')+k).alias('_idx'),*names)
        frames.append(keys.join(right,on=['numero_de_cliente','_idx'],how='left').select(names).fill_null(1).to_numpy())
    reasons=np.stack(frames,axis=2);months=keys['foto_mes'].to_numpy();out={}
    labels={0:'observed',1:'absent_client_month',2:'original_missing',3:'sanitation',4:'nonfinite'}
    for m in target_months:
        a=reasons[months==m];variables={}
        for j,c in enumerate(names):
            x=a[:,j,:];slots={str(k):{label:int((x[:,k]==code).sum()) for code,label in labels.items()} for k in range(4)}
            windows={}
            for w in [3,4]:
                z=x[:,:w];windows[str(w)]={'complete':int((z==0).all(axis=1).sum()),'incomplete':int((z!=0).any(axis=1).sum()),
                    'causes_overlapping':{label:int((z==code).any(axis=1).sum()) for code,label in labels.items() if code}}
            variables[c]={'slots_current_then_lags':slots,'strict_windows':windows}
        out[str(m)]={'rows':int(len(a)),'sources':variables}
    return {'reason_priority':'sanitation > original missing > nonfinite > observed; absent lookup is separate',
            'window_causes_overlap':True,'months':out}


if __name__=='__main__':
    cfg=json.loads(Path(sys.argv[1]).read_text())
    result=capture_environment(cfg)
    Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n')
