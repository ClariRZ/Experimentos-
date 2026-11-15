import argparse,sys
from pathlib import Path
import numpy as np,pandas as pd,pyarrow.parquet as pq
from comun import ROOT,read,write,sha,formulas
p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--data',type=Path,required=True);a=p.parse_args()
out=ROOT/'preparado';out.mkdir(exist_ok=True);cfg=read(ROOT/'config_propuesta.json');manifest=pd.read_csv(ROOT/'variables_propuestas.csv');prep=a.parent/'preparado'
assert sha(a.data)==cfg['data_sha256'];assert sha(ROOT/'vendor/fe_relaciones.py')==cfg['source_sha256'];assert len(manifest)==43 and manifest.variable.is_unique
base=read(prep/'manifest.json');cols=sum([base['families'][x] for x in ['original','lags','deltas']],[]);assert len(cols)==722 and not set(cols)&set(manifest.variable)
rows=pd.read_parquet(prep/'filas.parquet');assert not rows.duplicated(['numero_de_cliente','foto_mes']).any()
sources=sorted(set(manifest.fuente_1)|set(manifest.fuente_2));assert set(sources)<=set(pq.ParquetFile(a.data).schema_arrow.names)
df=pq.read_table(a.data,columns=['numero_de_cliente','foto_mes']+sources,filters=[('foto_mes','in',sorted(rows.foto_mes.unique().tolist()))]).to_pandas()
assert not df.duplicated(['numero_de_cliente','foto_mes']).any();df=df.set_index(['numero_de_cliente','foto_mes']).loc[pd.MultiIndex.from_frame(rows[['numero_de_cliente','foto_mes']])].reset_index()
assert df[['numero_de_cliente','foto_mes']].equals(rows[['numero_de_cliente','foto_mes']]);extra=formulas(df,manifest)
# Independent equality to the original C3 generator, with history prohibited.
sys.path.insert(0,str(ROOT/'vendor'));from fe_relaciones import generate_relations
class Panel:
 columns=df.columns;n=len(df)
 def get(self,v):return df[v].to_numpy(dtype='float64',na_value=np.nan)
 def lag(self,*args):raise AssertionError('History not authorized')
 def rank(self,*args):raise AssertionError('Ranks not authorized')
seen=[]
for name,v,meta in generate_relations(Panel(),{'relations':True,'relations_history':False}):
 if name in set(manifest.variable):
  j=manifest.variable.tolist().index(name);np.testing.assert_array_equal(extra[:,j],np.asarray(v,dtype='float32'));seen.append(name)
assert set(seen)==set(manifest.variable)
coverage=[]
for m in sorted(rows.foto_mes.unique()):
 ix=rows.foto_mes.eq(m).to_numpy()
 for j,c in enumerate(manifest.variable):coverage.append({'mes':int(m),'variable':c,'filas':int(ix.sum()),'faltantes':int(np.isnan(extra[ix,j]).sum())})
pd.DataFrame(coverage).to_csv(out/'cobertura.csv',index=False)
train=rows.foto_mes.isin(cfg['train_months']).to_numpy();assert np.isfinite(extra[train]).any(axis=0).all();assert not np.isinf(extra).any()
np.save(out/'extra.npy',extra)
write(out/'READY.json',{'status':'ready','data_sha256':sha(a.data),'parent_manifest_sha256':sha(prep/'manifest.json'),'extra_sha256':sha(out/'extra.npy'),'manifest_sha256':sha(ROOT/'variables_propuestas.csv'),'rows':len(rows),'baseline_features':len(cols),'extra_features':43,'columns':cols+manifest.variable.tolist(),'formulas_equal_original_c3':True,'no_test_labels_read':True})
print('PREPARADO',extra.shape,flush=True)
