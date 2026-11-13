import argparse,gc,json,time
from pathlib import Path
import numpy as np
import polars as pl
import lightgbm as lgb
from ejecutar_inicial import save,sha,Run,TRAIN,MONTH,LABEL

def measure(xt,yt,xv,yv,params,check):
 t=time.monotonic();ds=lgb.Dataset(xt,label=yt,params=params,free_raw_data=False);ds.construct()
 valid=lgb.Dataset(xv,label=yv,reference=ds,params=params,free_raw_data=False);valid.construct();construction=time.monotonic()-t
 stamps=[]
 def callback(env):
  check();stamps.append(time.monotonic())
 callback.order=99
 t=time.monotonic();model=lgb.train(params,ds,num_boost_round=200,valid_sets=[valid],callbacks=[callback])
 elapsed=time.monotonic()-t
 return {'construction_seconds':construction,'training_200_seconds':elapsed,'first_100_seconds':stamps[99]-t,'second_100_seconds':stamps[199]-stamps[99],'rounds_completed':model.current_iteration()}

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--deadline',type=float,required=True);p.add_argument('--prior',type=Path,required=True);a=p.parse_args()
 a.output.mkdir(exist_ok=False,parents=True);cfg=json.loads((a.prior/'config_frozen.json').read_text());reg=json.loads((a.prior/'feature_manifest.json').read_text())
 meta=pl.read_parquet(a.prior/'private/meta.parquet');yt=meta.filter(pl.col(MONTH).is_in(TRAIN))[LABEL].is_in(['BAJA+1','BAJA+2']).to_numpy().astype(np.int8);yv=(meta.filter(pl.col(MONTH)==201908)[LABEL]=='BAJA+2').to_numpy().astype(np.int8)
 r=Run.__new__(Run);r.cfg=cfg;r.out=a.output;r.deadline=a.deadline;r.art=a.prior/'private';r.registry=reg;r.yt=yt;r.yv=yv
 reports=[]
 for arm in ['B0','F1','F3','F4a','F4b']:
  save(a.output/'status.json',{'status':'CALIBRANDO','arm':arm,'october_used':False});print('CALIBRANDO',arm,flush=True)
  assert sha(r.art/f'{arm}.parquet')==reg[arm]['matrix_file_sha256']
  t=time.monotonic();xt,xv=r.matrices(arm);load=time.monotonic()-t
  report=measure(xt,yt,xv,yv,r.params(cfg['budget']['pilot_fixed_parameters'],101),r.check)
  report.update(arm=arm,columns=xt.shape[1],load_seconds=load);reports.append(report);save(a.output/'timings.json',reports);print(report,flush=True)
  del xt,xv;gc.collect()
 estimate=sum(15*(z['construction_seconds']+z['training_200_seconds']+13*z['second_100_seconds'])+z['load_seconds'] for z in reports)*1.2
 save(a.output/'FINAL.json',{'status':'CALIBRACION_COMPLETA','fits':5,'october_used':False,'timings':reports,'projection_75_fits_1500_rounds_seconds':estimate,'remaining_seconds':a.deadline-time.time(),'fits_budget':75,'assumption':'Pilot hyperparameters; no early stopping discount; 20% margin; runtime estimate, not guaranteed upper bound','decision':'FITS_ESTIMATE' if estimate<a.deadline-time.time() else 'REQUIRES_REVISED_BUDGET'})
 print('CALIBRACION_COMPLETA',estimate,flush=True)
if __name__=='__main__':main()
