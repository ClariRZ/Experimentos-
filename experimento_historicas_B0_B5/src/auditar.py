import argparse,json
from pathlib import Path
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
from historicas import labels,KEYS
p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--out',required=True);a=p.parse_args()
out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
d=pq.read_table(a.data,filters=[('foto_mes','>=',201901),('foto_mes','<=',201912)]).to_pandas()
assert not d.duplicated(KEYS).any(),'Claves duplicadas'
d['clase_ternaria']=labels(d[KEYS])
# No se publica distribución de etiquetas del test durante diseño.
safe=d[d.foto_mes.isin([201903,201904,201905,201906,201908])]
pd.crosstab(safe.foto_mes,safe.clase_ternaria).to_csv(out/'clases_train_validacion.csv')
rows=[]
for c in d:
 if c=='clase_ternaria':continue
 s=d[c]
 if c in ['tmobile_app','cmobile_app_trx']:
  n=pd.to_numeric(s,errors='coerce');assert not (s.notna()&n.isna()).any(),c;s=n
 rows.append({'variable':c,'tipo_original':str(d[c].dtype),'faltantes_train_valid':int(s.loc[safe.index].isna().sum()),'filas_train_valid':len(safe),'infinitos_train_valid':int(np.isinf(pd.to_numeric(s.loc[safe.index],errors='coerce').to_numpy(dtype=float,na_value=np.nan)).sum())})
pd.DataFrame(rows).to_csv(out/'columnas.csv',index=False)
report={'filas_2019':len(d),'clientes_2019':int(d.numero_de_cliente.nunique()),'duplicados':0,'train_rows':int(d.foto_mes.isin([201903,201904,201905,201906]).sum()),'valid_rows':int((d.foto_mes==201908).sum()),'test_rows':int((d.foto_mes==201910).sum()),'test_labels_inspected':False,'clase_reconstruida_horizonte':201912}
(out/'resumen.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
