"""Diagnóstico sin cambiar fórmulas: numerador/denominador observados por marca."""
import argparse,sys
from pathlib import Path
import pandas as pd,numpy as np,pyarrow.parquet as pq
from ratios_intrames import CARD,SOURCES,calculate
p=argparse.ArgumentParser();p.add_argument('--c1',required=True);p.add_argument('--c2',required=True);p.add_argument('--output',required=True);a=p.parse_args();records=[]
for series,path,months in [('C3',a.c1,[202103,202104,202106]),('B6',a.c2,[201903,201904,201905,201906,201908,201910])]:
 df=pq.read_table(path,columns=['foto_mes']+SOURCES,filters=[('foto_mes','in',months)]).to_pandas();rat=calculate(df)
 for j,(name,n,d) in enumerate(CARD):
  mismatch=np.zeros(len(df),bool)
  for brand in ['Master','Visa']:
   num=pd.to_numeric(df[brand+'_'+n]).to_numpy(float,na_value=np.nan);den=pd.to_numeric(df[brand+'_'+d]).to_numpy(float,na_value=np.nan)
   mismatch|=(np.isfinite(num)!=np.isfinite(den))
  for month in months:
   mask=df.foto_mes.eq(month).to_numpy();valid=np.isfinite(rat[:,j])&mask
   records.append({'serie':series,'mes':month,'ratio':name,'ratio_observado':int(valid.sum()),'observado_con_soporte_marcas_distinto':int((valid&mismatch).sum())})
Path(a.output).parent.mkdir(parents=True,exist_ok=True);pd.DataFrame(records).to_csv(a.output,index=False)
