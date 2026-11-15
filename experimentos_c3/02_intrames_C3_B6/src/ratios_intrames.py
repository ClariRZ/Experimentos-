"""Siete ratios intrames: contrato explícito, sin etiquetas ni historia."""
import numpy as np
import pandas as pd
CARD=[('ticket_consumo','mconsumototal','cconsumos'),('uso_limite','msaldototal','mlimitecompra'),('pago_sobre_minimo','mpagado','mpagominimo'),('consumo_sobre_limite','mconsumototal','mlimitecompra')]
TICKETS=[('transferencias_emitidas','mtransferencias_emitidas','ctransferencias_emitidas'),('atm','matm','catm_trx'),('pagomiscuentas','mpagomiscuentas','cpagomiscuentas')]
NAMES=['intrames_tc_'+a for a,_,_ in CARD]+['intrames_ticket_'+a for a,_,_ in TICKETS]
SOURCES=sorted({c for _,n,d in CARD for s in (n,d) for c in ('Master_'+s,'Visa_'+s)}|{c for _,n,d in TICKETS for c in (n,d)})
def safe(n,d):
 n=np.asarray(n,float);d=np.asarray(d,float); z=np.full(len(n),np.nan)
 ok=np.isfinite(n)&np.isfinite(d)&(d>0)
 np.divide(n,d,out=z,where=ok);z[~np.isfinite(z)]=np.nan
 return z

def calculate(df):
 def get(c):
  a=pd.to_numeric(df[c],errors='raise').to_numpy(dtype=float,na_value=np.nan,copy=True);a[~np.isfinite(a)]=np.nan;return a
 def total(s):
  a=get('Master_'+s);b=get('Visa_'+s)
  return np.where(np.isnan(a)&np.isnan(b),np.nan,np.nan_to_num(a,nan=0)+np.nan_to_num(b,nan=0))
 return np.column_stack([safe(total(n),total(d)) for _,n,d in CARD]+[safe(get(n),get(d)) for _,n,d in TICKETS]).astype('float32')

def test():
 np.testing.assert_allclose(safe([0,1,-2,1,1,np.inf],[1,0,2,-1,np.nan,1]),[0,np.nan,-1,np.nan,np.nan,np.nan],equal_nan=True)
 d=pd.DataFrame({c:[np.nan,1,0] for c in SOURCES});r=calculate(d)
 assert r.shape==(3,7) and np.isnan(r[0]).all() and np.isnan(r[2]).all()
 np.testing.assert_allclose(r[1],1)
 # Sólo una marca observada: conservarla; nunca convertir ambos faltantes en 0.
 for c in d.columns:
  if c.startswith('Master_'): d[c]=np.nan
 np.testing.assert_allclose(calculate(d)[1],1)
 print('TEST_RATIOS_OK')
if __name__=='__main__':test()
