"""Read-only frozen v7 importance and three-scenario diagnosis. Never fits."""
import argparse,gc,hashlib,io,json,sys,tarfile,time,resource
from pathlib import Path
import numpy as np
import lightgbm as lgb
import polars as pl
VARS=['mrentabilidad','mrentabilidad_annual','mpasivos_margen','mactivos_margen','mcomisiones','mcomisiones_otras','ccomisiones_otras','chomebanking_transacciones','mcajeros_propios_descuentos','ccajeros_propios_descuentos','ctarjeta_visa_descuentos','mtarjeta_visa_descuentos','ctarjeta_master_descuentos','mtarjeta_master_descuentos']
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def read(t,n,expected=None):
 b=t.extractfile(n).read()
 if expected is not None and hashlib.sha256(b).hexdigest()!=expected:raise ValueError('Hash mismatch '+n)
 return b
def loadnp(t,n,expected=None):
 with np.load(io.BytesIO(read(t,n,expected)),allow_pickle=False) as f:return {k:f[k] for k in f.files}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--august-archive',type=Path,required=True);ap.add_argument('--october-archive',type=Path,required=True);ap.add_argument('--dataset',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 a.output.mkdir(parents=True,exist_ok=False)
 base=a.repo/'HISTORIA_2019_01/v7';aug=base/'resultados/agosto';oct=base/'resultados/octubre'
 cfg=json.loads((aug/'config_frozen.json').read_text());reg=json.loads((aug/'feature_manifest.json').read_text());policy=json.loads((aug/'policy_frozen.json').read_text());om=json.loads((oct/'private_manifest.json').read_text())
 identity=json.loads((aug/'code_identity.json').read_text())
 for name in ['ejecutar_v7.py','fe_core.py','preflight.py']:
  if sha(base/'scripts'/name)!=identity[name]:raise ValueError('Original code identity mismatch '+name)
 sys.path.insert(0,str(base/'scripts'));import ejecutar_v7 as m
 ta=tarfile.open(a.august_archive);to=tarfile.open(a.october_archive)
 for name,h in om.items():read(to,'private/'+name,h)
 importance=[];nmodels=0
 for arm in reg:
  columns=reg[arm]['columns']
  for seed,hashes in policy['models'][arm].items():
   modelname='seed_'+seed+'.txt'
   for name,h in hashes.items():read(ta,f'private/{arm}/{name}',h)
   model=lgb.Booster(model_str=read(ta,f'private/{arm}/{modelname}',hashes[modelname]).decode())
   if model.num_feature()!=len(columns):raise ValueError('Column count mismatch')
   gain=model.feature_importance('gain');split=model.feature_importance('split')
   groups={'contemporary':[i for i,c in enumerate(columns) if c in VARS], 'derived':[i for i,c in enumerate(columns) if any(c.startswith(v+'__') for v in VARS)]}
   importance.append({'arm':arm,'seed':int(seed),'total_gain':float(gain.sum()),'total_split':int(split.sum()),'groups':{g:{'n_columns':len(ix),'gain':float(gain[ix].sum()),'split':int(split[ix].sum()),'columns':[columns[i] for i in ix]} for g,ix in groups.items()}});nmodels+=1
 save(a.output/'importancias.json',importance)
 save(a.output/'fuentes_octubre.json',{'source_commit':'770abaa9cad412647211c255360cb6dfe364e697','source_files':['pipeline/funciones.py:ESPERADO_ROTOS_REGLA','pipeline/parametros.py:ROTOS_A_MANO,ROTOS_EXTRA'],'official_confirmation':False,'variables':[{'name':v,'eligible':v in cfg['data']['history_sources']} for v in VARS]})
 status={'models_read_verified':nmodels,'october_members_verified':len(om),'archive_sha256':{'august':sha(a.august_archive),'october':sha(a.october_archive)},'fits':0,'inference':'PENDING_DATASET','peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
 save(a.output/'estado.json',status)
 if a.dataset is None:return
 if sha(a.dataset)!=cfg['data']['sha256']:raise ValueError('Dataset hash mismatch: no inference performed')
 # All intact predictions must pass before any perturbation is interpreted.
 results=[];beg=time.monotonic()
 for scenario in ['intact','contemporary','coherent']:
  data=m.read_data(a.dataset,[201907,201908,201909,201910],labels=False)
  if scenario=='coherent':data=data.with_columns([pl.when(pl.col(m.MONTH)==201910).then(None).otherwise(pl.col(v)).alias(v) for v in VARS])
  hist,raw=m.history(data,cfg,[201910]);del data
  for arm in reg:
   frame=hist
   if arm in ['H_T','H_S']:
    frame,_=m.extras(frame,'R4',cfg['data']['history_sources']);frame,_=m.extras(frame,'T4' if arm=='H_T' else 'SYM',cfg['data']['history_sources'])
   elif arm!='B0':frame,_=m.extras(frame,arm,cfg['data']['history_sources'])
   cols=reg[arm]['columns'];frame=m.numeric(frame.select([m.ID,m.MONTH,*cols]),cols)
   if scenario=='contemporary':frame=frame.with_columns([pl.lit(None,dtype=pl.Float32).alias(v) for v in VARS if v in cols])
   ids=frame[m.ID].to_numpy();X=frame.select(cols).to_numpy();preds=[]
   for seed,hashes in policy['models'][arm].items():
    name='seed_'+seed+'.txt';model=lgb.Booster(model_str=read(ta,f'private/{arm}/{name}',hashes[name]).decode());pred=model.predict(X,num_threads=4)
    saved=loadnp(to,f'private/{arm}/seed_{seed}.npz',om[f'{arm}/seed_{seed}.npz'])
    if not np.array_equal(ids,saved['ids']):raise ValueError('ID order mismatch')
    if scenario=='intact' and not np.array_equal(pred,saved['prediction']):
     save(a.output/'intact_failure.json',{'arm':arm,'seed':seed,'max_error':float(np.max(np.abs(pred-saved['prediction'])))})
     raise ValueError('Intact predictions differ; perturbations blocked')
    preds.append(pred)
   ensemble=np.mean(preds,axis=0)
   if scenario=='intact':
    ep=loadnp(to,f'private/{arm}/ensemble.npz',om[f'{arm}/ensemble.npz'])
    if not np.array_equal(ensemble,ep['prediction']):raise ValueError('Ensemble differs')
   # Labels only needed after successful intact scoring; exact IDs mandatory.
   labels=loadnp(to,'private/labels.npz',om['labels.npz'])
   if not np.array_equal(ids,labels['ids']):raise ValueError('Label ID mismatch')
   label_key='y' if 'y' in labels else 'labels'
   if label_key not in labels:raise ValueError('Inspect label archive schema before inference')
   y=labels[label_key]; positive=(y=='BAJA+2') if y.dtype.kind in 'US' else (y==1)
   def gain(pred):return int(1100000*positive[np.lexsort((ids,-pred))[:3583]].sum()-27500*3583)
   results.append({'scenario':scenario,'arm':arm,'gain':gain(ensemble),'seed_gains':[gain(p) for p in preds]})
   del frame,X,preds;gc.collect()
  del hist;gc.collect()
  save(a.output/'partial_scenarios.json',results)
 for row in results:row['delta_vs_B0']=row['gain']-next(r['gain'] for r in results if r['scenario']==row['scenario'] and r['arm']=='B0')
 save(a.output/'scenarios.json',results)
 status.update(inference='COMPLETE',seconds=time.monotonic()-beg,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);save(a.output/'estado.json',status)
if __name__=='__main__':main()
