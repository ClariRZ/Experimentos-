"""Preflight v3: no entrena y no carga filas posteriores a agosto."""
from pathlib import Path
import sys,json,hashlib,time
import numpy as np
import polars as pl
ROOT=Path(__file__).resolve().parents[1]
V2=ROOT.parent/'v2'
sys.path.insert(0,str(V2/'vendor'))
from historia_features import _ensure_panel,add_lags_deltas,ID,MONTH,LABEL
TRAIN=[201903,201904,201905,201906]
COUNTS=['cpayroll_trx','ctrx_quarter','ctarjeta_visa_transacciones','ctarjeta_master_transacciones','ctarjeta_debito_transacciones','chomebanking_transacciones','ccuenta_debitos_automaticos','ctarjeta_visa_debitos_automaticos','ctarjeta_master_debitos_automaticos']
SERVICES=COUNTS[-3:]
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 q=p.with_suffix('.tmp');q.write_text(json.dumps(d,indent=2,ensure_ascii=False,allow_nan=False)+'\n');q.replace(p)
def signed_rank(df,c):
 x=pl.col(c)
 pos=pl.when(x>0).then(x);neg=pl.when(x<0).then(x.abs())
 return pl.when(x.is_null()).then(None).when(x==0).then(0).when(x>0).then(pos.rank('average').over(MONTH)/pos.count().over(MONTH)).otherwise(-neg.rank('average').over(MONTH)/neg.count().over(MONTH)).cast(pl.Float32).alias(c+'__rank')
def activity(df,c):
 x,a,b=[pl.col(z) for z in [c,c+'__lag1',c+'__lag2']]
 ok=(x>=0)&(a>=0);ok3=ok&(b>=0)
 return [pl.when(ok).then(((a>0)&(x==0)).cast(pl.Float32)).otherwise(None).alias(c+'__apago1'),pl.when(ok).then(((a==0)&(x>0)).cast(pl.Float32)).otherwise(None).alias(c+'__prendio1'),pl.when(ok3).then(pl.when(x<a).then(pl.when(a<b).then(2).otherwise(1)).otherwise(0)).otherwise(None).cast(pl.Float32).alias(c+'__caidas3')]
def avail(df):
 for k in [1,2]:
  hist=df.select(ID,(pl.col('_month_index')+k).alias('_month_index'),pl.lit(1,dtype=pl.Float32).alias(f'registro_lag{k}_disponible'))
  df=df.join(hist,on=[ID,'_month_index'],how='left',validate='1:1',maintain_order='left').with_columns(pl.col(f'registro_lag{k}_disponible').fill_null(0))
 return df

def tests():
 d=pl.DataFrame({ID:[1,2,3,4,5,6,7],MONTH:[201901]*7,'x':[None,-2.,-2.,-4.,0.,3.,6.]})
 assert d.with_columns(signed_rank(d,'x'))['x__rank'].to_list()==[None,-.5,-.5,-1.,0.,.5,1.]
 d=_ensure_panel(pl.DataFrame({ID:[1,1,1,2],MONTH:[201812,201901,201903,201901],'x':[3.,2.,0.,1.]}))
 h=add_lags_deltas(d,['x']);assert h['x__lag1'].to_list()==[None,3.,None,None];assert h['x__lag2'].to_list()==[None,None,2.,None]
 h=h.with_columns(activity(h,'x'));assert h['x__caidas3'].to_list()==[None]*4
 h=avail(h);assert h['registro_lag1_disponible'].to_list()==[0.,1.,0.,0.]
 print('Pruebas sintéticas de preflight OK',flush=True)

def main(persist=True):
 tests();cfg=json.loads((V2/'configuraciones/protocolo.json').read_text());recipe=json.loads((V2/'resultados/B4/recipe.json').read_text());cols=recipe['columns']
 assert sha(cfg['data'])==cfg['expected_data_sha256']
 source=pl.scan_csv(cfg['data'],infer_schema=False,null_values=['','NA','NaN','nan','NULL','null'])
 d=source.with_columns(pl.col(MONTH).cast(pl.Int64),pl.col(ID).cast(pl.Int64)).filter(pl.col(MONTH).is_between(201901,201908)).collect()
 d=_ensure_panel(d);raw=[c for c in d.columns if c not in [ID,MONTH,LABEL,'_month_index']];assert len(raw)==152
 for c,months in cfg['broken_variables'].items():d=d.with_columns(pl.when(pl.col(MONTH).is_in(months)).then(None).otherwise(pl.col(c)).alias(c))
 for c in raw:
  x=d[c].cast(pl.Float64,strict=False);assert not (d[c].is_not_null()&x.is_null()).any(),c
  x=x.cast(pl.Float32);d=d.with_columns(x.set(~x.is_finite().fill_null(False),None).alias(c))
 for m in TRAIN+[201908]:
  y=d.filter(pl.col(MONTH)==m)[LABEL];assert y.len()>0 and y.is_in(['BAJA+1','BAJA+2','CONTINUA']).all() and not y.null_count()
 d=add_lags_deltas(d,raw);assert set(cols)<=set(d.columns)
 shortlist=json.loads((V2/'resultados/shortlist.json').read_text())['selected']
 monetary=[c for c in shortlist if c.startswith('m') or c.startswith(('Visa_m','Master_m'))]
 d=d.with_columns([signed_rank(d,c) for c in monetary]);d=add_lags_deltas(d,[c+'__rank' for c in monetary])
 d=d.with_columns([e for c in COUNTS if c in raw for e in activity(d,c)]);d=avail(d)
 coverage={}
 def measure(c):
  if c not in coverage:
   coverage[c]={}
   for m in TRAIN+[201908]:
    x=d.filter(pl.col(MONTH)==m)[c];valid=x.is_finite().fill_null(False)
    coverage[c][str(m)]={'defined':int(valid.sum()),'total':len(x),'coverage':float(valid.mean()),'nonzero':int(((x!=0)&valid).sum()),'undefined':int((~valid).sum()),'min':x.min(),'max':x.max()}
  return all(coverage[c][str(m)]['coverage']>=.9 for m in TRAIN)
 sources=[];excluded_sources={}
 for c in monetary:
  names=[c+'__rank']+[c+'__rank__'+op+str(k) for k in [1,2] for op in ['lag','delta']]
  good=[measure(n) for n in names]
  if all(good):sources.append(c)
  else:excluded_sources[c]=[n for n,g in zip(names,good) if not g]
 arms={'A':[c+'__rank' for c in sources],'C':[c+'__'+op for c in COUNTS if c in raw for op in ['apago1','prendio1','caidas3']],'D':['registro_lag1_disponible','registro_lag2_disponible']}
 arms['B']=arms['A']+[c+'__rank__'+op+str(k) for c in sources for k in [1,2] for op in ['lag','delta']]
 services=[c+'__apago1' for c in SERVICES if c in raw and measure(c+'__apago1')]
 if len(services)>=2:
  d=d.with_columns(pl.when(pl.all_horizontal([pl.col(c).is_not_null() for c in services])).then(pl.sum_horizontal(services)).otherwise(None).alias('servicios_apagados'))
  arms['C'].append('servicios_apagados')
 train=d.filter(pl.col(MONTH).is_in(TRAIN));hashes={};removed={};keep={}
 def digest(c):
  a=train[c].to_numpy().astype(np.float32,copy=True);a[np.isnan(a)]=np.nan;a[a==0]=0
  return hashlib.sha256(a.tobytes()).hexdigest()
 for c in cols:hashes.setdefault(digest(c),c)
 # A before B assures nested designs; common columns are reused.
 for arm in ['A','B','C','D']:
  keep[arm]=[]
  for c in arms[arm]:
   if c in removed:continue
   if not measure(c):removed[c]='Cobertura <90% en al menos un mes train';continue
   x=train[c]
   if x.n_unique()<=1:removed[c]='Constante en train';continue
   h=digest(c)
   if h in hashes and hashes[h]!=c:removed[c]='Identica en train a '+hashes[h];continue
   hashes[h]=c;keep[arm].append(c)
 audit={'status':'AUDITORIA_SIN_ENTRENAMIENTO','dataset_sha256':cfg['expected_data_sha256'],'months_loaded':sorted(d[MONTH].unique().to_list()),'octubre_abierto':False,'control_proposed':'B4 adaptado v2; no confirmado con 20 semillas','control_columns':len(cols),'hyperparams':recipe['hyperparams'],'control_recipe_sha256':sha(V2/'resultados/B4/recipe.json'),'monetary_candidates':monetary,'rank_sources':sources,'excluded_rank_sources':excluded_sources,'activity_sources_missing':[c for c in COUNTS if c not in raw],'services_for_sum':services,'arm_new_columns':keep,'excluded_columns':removed,'coverage':coverage,'partitions':{str(m):d.filter(pl.col(MONTH)==m).height for m in TRAIN+[201908]},'warnings':['BOF pendiente: 588 no equivale automaticamente a 760','Shortlist ya uso junio; agosto fue utilizado por Optuna y comparaciones v2','Motivos de NA: dato fuente faltante/roto, mes ausente o conteo negativo; cobertura agrega todos estos motivos'],'code_sha256':sha(__file__)}
 if persist: save(ROOT/'auditoria/preflight.json',audit)
 print(json.dumps({k:audit[k] for k in ['status','control_columns','rank_sources','excluded_rank_sources','excluded_columns','partitions']},ensure_ascii=False),flush=True)
 print('COLUMNAS_NUEVAS', {k:len(v) for k,v in keep.items()},flush=True)
 return d,audit
if __name__=='__main__':main()
