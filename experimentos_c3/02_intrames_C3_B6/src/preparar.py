import argparse,json,sys,hashlib,gc
from pathlib import Path
import numpy as np,pandas as pd,pyarrow.parquet as pq
from ratios_intrames import calculate,SOURCES,NAMES
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from fe_core import Panel
from generar_fe import iter_features,sha256_file
from fe_semantica import load_catalog
p=argparse.ArgumentParser();p.add_argument('--c1',required=True);p.add_argument('--c2',required=True);p.add_argument('--parent-prep',required=True);p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);out.mkdir(exist_ok=True,parents=True)
plan=json.loads((ROOT/'config/c3_original.json').read_text()); cfg=json.loads((ROOT/'config/fe_c3.json').read_text()); bc=json.loads((ROOT/'config/b5_original.json').read_text())
assert sha256_file(a.c1)==plan['data_sha256']; assert sha256_file(a.c2)==bc['data_sha256']
if not (out/'C3_READY.json').exists():
 panel=Panel(pd.read_parquet(a.c1),cfg)
 use=np.isin(panel.month,[202103,202104,202106]); names=plan['schema']; loc={f:j for j,f in enumerate(names)}
 X=np.lib.format.open_memmap(out/'c3.npy',mode='w+',dtype='float64',shape=(int(use.sum()),len(names)),fortran_order=True)
 for j,f in enumerate(names[:152]): X[:,j]=panel.get(f)[use]
 seen=set();coverage=[]
 for name,values,meta in iter_features(panel,load_catalog(),cfg):
  if name not in loc:continue
  X[:,loc[name]]=values[use].astype('float32').astype('float64');seen.add(name)
  if len(seen)%100==0:print('C3_FEATURES',len(seen),flush=True)
 assert seen==set(names[152:])
 raw=panel.df.loc[use].reset_index(drop=True);rat=calculate(raw)
 dup=[]
 for j,concept in enumerate(['transferencias_emitidas','atm','pagomiscuentas'],start=4):
  f='fe__rel__ticket__'+concept
  np.testing.assert_allclose(rat[:,j].astype('float64'),X[:,loc[f]],equal_nan=True,rtol=0,atol=0);dup.append(f)
 # No otros ratios idénticos al control en estas filas (auditoría exacta de valores).
 for j in range(4):
  for f in names[152:]:
   if np.array_equal(rat[:,j].astype('float64'),X[:,loc[f]],equal_nan=True):raise ValueError('Nuevo ratio duplicado: '+f)
 np.save(out/'c3_intrames.npy',rat[:,:4]);X.flush();del X
 raw[['numero_de_cliente','foto_mes','clase_ternaria']].to_parquet(out/'c3_filas.parquet',index=False)
 for j,n in enumerate(NAMES):
  for m in [202103,202104,202106]:
   v=rat[raw.foto_mes.eq(m).to_numpy(),j];coverage.append({'serie':'C3','variable':n,'mes':m,'filas':len(v),'faltantes':int(np.isnan(v).sum())})
 pd.DataFrame(coverage).to_csv(out/'c3_cobertura.csv',index=False)
 (out/'C3_READY.json').write_text(json.dumps({'schema':names,'added':NAMES[:4],'duplicates_excluded':dup,'rows':len(raw),'data_sha256':plan['data_sha256']},indent=2))
 del panel,raw,rat;gc.collect()
if not (out/'B6_READY.json').exists():
 keys=['numero_de_cliente','foto_mes'];rows=pd.read_parquet(Path(a.parent_prep)/'filas.parquet')
 data=pq.read_table(a.c2,columns=keys+SOURCES,filters=[('foto_mes','in',rows.foto_mes.unique().tolist())]).to_pandas()
 df=rows.merge(data,on=keys,how='left',validate='one_to_one',indicator=True);assert df['_merge'].eq('both').all();assert df[keys].equals(rows[keys])
 ratio=calculate(df);np.save(out/'b6_intrames.npy',ratio)
 cov=[]
 for j,n in enumerate(NAMES):
  for m in sorted(rows.foto_mes.unique()):
   v=ratio[rows.foto_mes.eq(m).to_numpy(),j];cov.append({'serie':'B6','variable':n,'mes':int(m),'filas':len(v),'faltantes':int(np.isnan(v).sum())})
 pd.DataFrame(cov).to_csv(out/'b6_cobertura.csv',index=False)
 (out/'B6_READY.json').write_text(json.dumps({'added':NAMES,'rows':len(rows),'data_sha256':bc['data_sha256']},indent=2))
print('PREPARACION_COMPLETA',flush=True)
