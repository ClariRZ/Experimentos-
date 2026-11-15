"""Compara resultados numéricos y predicciones; excluye tiempos, RAM y fechas."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd

p=argparse.ArgumentParser();p.add_argument('--reference',required=True);p.add_argument('--new',required=True);p.add_argument('--out',required=True);a=p.parse_args()
ref=Path(a.reference);new=Path(a.new);checks=[]
def equal(label,left,right,approx=False):
    try:
        if approx:np.testing.assert_allclose(left,right,rtol=0,atol=1e-12,equal_nan=True)
        else:np.testing.assert_array_equal(left,right)
        checks.append({'check':label,'passed':True})
    except (AssertionError,ValueError) as err:checks.append({'check':label,'passed':False,'detail':str(err)[:1000]})
rr=pd.read_csv(ref/'resultados.csv').sort_values('experimento').reset_index(drop=True)
nr=pd.read_csv(new/'resultados.csv').sort_values('experimento').reset_index(drop=True)
for c in rr.columns:
    if c not in ['segundos','pico_ram_mib_proceso']:equal('resultados/'+c,rr[c].to_numpy(),nr[c].to_numpy(),c=='auc_agosto')
for e in rr.experimento:
    for name in ['validation_predictions.parquet','test_predictions.parquet']:
        left=pd.read_parquet(ref/e/name).sort_values('numero_de_cliente');right=pd.read_parquet(new/e/name).sort_values('numero_de_cliente')
        equal(e+'/'+name+'/ids',left.numero_de_cliente.to_numpy(),right.numero_de_cliente.to_numpy())
        equal(e+'/'+name+'/prob',left.prob.to_numpy(),right.prob.to_numpy(),True)
    l=pd.read_csv(ref/e/'trials.csv').sort_values('number');r=pd.read_csv(new/e/'trials.csv').sort_values('number')
    for col in ['number','state','value','user_attrs_best_iteration']+[c for c in l if c.startswith('params_')]:
        equal(e+'/trials/'+col,l[col].to_numpy(),r[col].to_numpy(),col=='value')
models={e:hashlib.sha256((ref/e/'model.txt').read_bytes()).hexdigest()==hashlib.sha256((new/e/'model.txt').read_bytes()).hexdigest() for e in rr.experimento}
passed=all(c['passed'] for c in checks)
Path(a.out).write_text(json.dumps({'numerical_reproduction_passed':passed,'probability_auc_atol':1e-12,'model_files_byte_identical':models,'checks':checks},indent=2))
print('COMPARACION_NUMERICA_OK' if passed else 'DIFERENCIAS_EN_REPRODUCCION',len(checks),'controles')
raise SystemExit(0 if passed else 1)
