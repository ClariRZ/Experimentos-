"""Históricas causales por mes calendario; sin leer etiquetas futuras como features."""
import numpy as np
import pandas as pd

KEYS = ['numero_de_cliente', 'foto_mes']

def period(month):
    return month // 100 * 12 + month % 100

def labels(keys):
    """Clase con censura al final del horizonte recibido; ausencias mensuales exactas."""
    p = period(keys.foto_mes.to_numpy())
    idx = pd.MultiIndex.from_arrays([keys.numero_de_cliente, p])
    if not idx.is_unique:
        raise ValueError('Claves duplicadas')
    nxt = pd.MultiIndex.from_arrays([keys.numero_de_cliente, p+1]).isin(idx)
    nxt2 = pd.MultiIndex.from_arrays([keys.numero_de_cliente, p+2]).isin(idx)
    last = int(p.max())
    y = np.full(len(p), None, dtype=object)
    y[p <= last-2] = 'CONTINUA'
    y[(p < last) & ~nxt] = 'BAJA+1'
    y[(p <= last-2) & nxt & ~nxt2] = 'BAJA+2'
    return y

def exact_lags(frame, cols):
    idx = pd.MultiIndex.from_arrays([frame.numero_de_cliente, period(frame.foto_mes)])
    if not idx.is_unique:
        raise ValueError('Claves duplicadas')
    values = frame[cols].copy()
    values.index = idx
    result = []
    for k in [1, 2]:
        target = pd.MultiIndex.from_arrays([frame.numero_de_cliente, period(frame.foto_mes)-k])
        lag = values.reindex(target)
        lag.index = frame.index
        result.append(lag)
    return result

def summaries(current, lag1, lag2):
    a = np.stack([lag2, lag1, current]).astype('float64')
    ok = np.isfinite(a)
    t = np.arange(3).reshape((3,)+(1,)*(a.ndim-1))
    n = ok.sum(axis=0)
    sy = np.where(ok,a,0).sum(axis=0)
    sx = (ok*t).sum(axis=0)
    sxx = (ok*t*t).sum(axis=0)
    sxy = np.where(ok,a*t,0).sum(axis=0)
    mean = np.full(current.shape,np.nan)
    slope = np.full(current.shape,np.nan)
    np.divide(sy,n,out=mean,where=n>=2)
    den=n*sxx-sx*sx
    np.divide(n*sxy-sx*sy,den,out=slope,where=(n>=2)&(den>0))
    return mean.astype('float32'),slope.astype('float32')

def ratio(a,b):
    out=np.full(a.shape,np.nan,dtype='float64')
    np.divide(a,b,out=out,where=np.isfinite(a)&np.isfinite(b)&(b!=0))
    out[~np.isfinite(out) | (np.abs(out)>np.finfo('float32').max)]=np.nan
    return out.astype('float32')

def gain(y):
    return np.where(np.asarray(y)=='BAJA+2',1072500,-27500).astype('int64')
