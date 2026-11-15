"""Diagnóstico de cobertura de matrices, sin abrir etiquetas de test."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
p=argparse.ArgumentParser();p.add_argument('--prep',required=True);p.add_argument('--out',required=True);a=p.parse_args()
root=Path(a.prep);manifest=json.loads((root/'manifest.json').read_text())
months=pd.read_parquet(root/'filas.parquet',columns=['foto_mes']).foto_mes.to_numpy()
rows=[]
for family in manifest['families']:
    x=np.load(root/(family+'.npy'),mmap_mode='r')
    for label,selected in [('entrenamiento',[201903,201904,201905,201906]),('validacion',[201908])]:
        indices=np.flatnonzero(np.isin(months,selected));valid=0
        for start in range(0,len(indices),10000):
            valid+=int(np.isfinite(x[indices[start:start+10000]]).sum())
        total=len(indices)*x.shape[1]
        rows.append(dict(familia=family,particion=label,columnas=x.shape[1],filas=len(indices),celdas_validas=valid,celdas_totales=total,cobertura_pct=100*valid/total))
pd.DataFrame(rows).to_csv(a.out,index=False)
original=np.load(root/'original.npy',mmap_mode='r');lags=np.load(root/'lags.npy',mmap_mode='r')
q=[manifest['families']['original'].index(c) for c in manifest['quantitative']]
ncols=original.shape[1];diagnostics=[]
for label,selected in [('entrenamiento',[201903,201904,201905,201906]),('validacion',[201908])]:
    indices=np.flatnonzero(np.isin(months,selected));counts=np.zeros(4,dtype=np.int64)
    for start in range(0,len(indices),10000):
        ix=indices[start:start+10000]
        n=np.isfinite(original[np.ix_(ix,q)]).astype('int8')
        n+=np.isfinite(lags[np.ix_(ix,q)])
        n+=np.isfinite(lags[np.ix_(ix,[c+ncols for c in q])])
        counts+=np.bincount(n.ravel(),minlength=4)
    for valid,count in enumerate(counts):
        diagnostics.append(dict(particion=label,observaciones_validas_ventana=valid,ventanas_variable_cliente=int(count),porcentaje=100*count/counts.sum()))
pd.DataFrame(diagnostics).to_csv(Path(a.out).with_name('observaciones_por_ventana.csv'),index=False)
