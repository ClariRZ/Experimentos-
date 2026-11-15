"""QA de la salida: archivos, esquema y 20 lags/deltas frente a un merge independiente."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from cargar_bloques import cargar_bloques

HISTORY = ['ctrx_quarter','mcaja_ahorro','mcuentas_saldo','mpasivos_margen','mpayroll',
           'cpayroll_trx','mtarjeta_visa_consumo','ctarjeta_visa_transacciones',
           'ctarjeta_debito_transacciones','cextraccion_autoservicio']

def validate(input_path,output_path,month):
    root=Path(output_path);manifest=json.loads((root/'manifest.json').read_text())
    assert manifest['status']=='completed'
    catalog=pd.read_csv(root/'catalogo_features.csv')
    assert catalog.feature.is_unique
    assert len(catalog)==manifest['features_defined']
    expected=catalog[catalog.status.eq('generated')]
    assert len(expected)==manifest['features_materialized']
    for rel,rows in expected.groupby('file'):
        pf=pq.ParquetFile(root/rel)
        assert pf.metadata.num_rows==manifest['output_rows'],rel
        assert set(pf.schema_arrow.names)==set(rows.feature)|{'numero_de_cliente','foto_mes'},rel
    selected=[f'fe__{v}__{op}' for v in HISTORY for op in ['lag1','delta1']]
    actual,_=cargar_bloques(root,features=selected,meses=[month],incluir_raw=False)
    source=pd.read_parquet(input_path,columns=['numero_de_cliente','foto_mes']+HISTORY)
    year,mo=divmod(month,100);previous=year*100+mo-1 if mo>1 else (year-1)*100+12
    current=source[source.foto_mes.eq(month)].drop(columns='foto_mes')
    before=source[source.foto_mes.eq(previous)].drop(columns='foto_mes')
    paired=current.merge(before,on='numero_de_cliente',how='left',validate='one_to_one',suffixes=('','__previous'))
    paired=paired.set_index('numero_de_cliente').reindex(actual.numero_de_cliente)
    for v in HISTORY:
        prev=paired[v+'__previous'].to_numpy(float)
        np.testing.assert_allclose(actual[f'fe__{v}__lag1'],prev,rtol=0,atol=0,equal_nan=True)
        np.testing.assert_allclose(actual[f'fe__{v}__delta1'],paired[v].to_numpy(float)-prev,rtol=0,atol=0,equal_nan=True)
    return {'status':'passed','month':month,'rows_checked':len(actual),'features_checked_against_raw':20,
            'parts_checked':int(expected.file.nunique()),'absolute_tolerance':0,'relative_tolerance':0,
            'note':'Comparación independiente por merge entre fotos; sin entrenamiento de modelos.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--month',type=int,default=202106)
    a=p.parse_args();print(json.dumps(validate(a.input,a.output,a.month),ensure_ascii=False,indent=2))
