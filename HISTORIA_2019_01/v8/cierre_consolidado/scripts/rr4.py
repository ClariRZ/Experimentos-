"""RR4: four exact calendar observations; no fitting or data mutation."""
import numpy as np

def rr4(window):
    a = np.asarray(window, dtype=np.float64)
    if a.ndim != 2 or a.shape[1] != 4:
        raise ValueError('Expected rows x [current, lag1, lag2, lag3]')
    finite = np.isfinite(a)
    nz = finite & (a != 0)
    rec = np.where(nz.any(axis=1), nz.argmax(axis=1), np.nan).astype(float)
    zero = np.cumprod(finite & (a == 0), axis=1).sum(axis=1).astype(float)
    nonzero = np.cumprod(nz, axis=1).sum(axis=1).astype(float)
    zero[~finite[:, 0]] = np.nan
    nonzero[~finite[:, 0]] = np.nan
    return np.column_stack((rec, zero, nonzero))

def calendar_window(ids, months, values):
    ids, months, values = list(ids), list(months), list(values)
    if not len(ids) == len(months) == len(values): raise ValueError('Length mismatch')
    keys=[]
    for i,m in zip(ids,months):
        if i is None or m is None or int(m)%100 not in range(1,13): raise ValueError('Invalid key/month')
        keys.append((i,int(m)//100*12+int(m)%100))
    if len(set(keys))!=len(keys): raise ValueError('Duplicate client-month')
    lookup=dict(zip(keys,values))
    present=np.array([[(i,m-k) in lookup for k in range(4)] for i,m in keys],dtype=bool)
    a=np.array([[lookup.get((i,m-k),np.nan) for k in range(4)] for i,m in keys],dtype=float)
    return a,present

def coverage(raw, present, masked):
    """Cell-level provenance; callers aggregate with explicit column/month keys."""
    raw=np.asarray(raw,dtype=float);present=np.asarray(present,dtype=bool);masked=np.asarray(masked,dtype=bool)
    if raw.ndim!=2 or raw.shape[1]!=4 or present.shape!=raw.shape or masked.shape!=raw.shape: raise ValueError('Shape mismatch')
    x=np.where(present & ~masked,raw,np.nan)
    before=rr4(np.where(present,raw,np.nan));after=rr4(x)
    absent=(~present).any(axis=1)
    original=(present & ~np.isfinite(raw)).any(axis=1)
    masks=(present & np.isfinite(raw) & masked).any(axis=1)
    categories=np.full(after.shape,'unexpected',dtype=object)
    for j in range(3):
        missing=~np.isfinite(after[:,j])
        # Rachas only require current to return finite; recencia may inspect all four.
        absent_j=absent if j==0 else ~present[:,0]
        original_j=original if j==0 else present[:,0]&~np.isfinite(raw[:,0])
        mask_j=masks if j==0 else present[:,0]&np.isfinite(raw[:,0])&masked[:,0]
        categories[np.isfinite(after[:,j]),j]='finite'
        categories[missing & absent_j,j]='absent_client'
        categories[missing & ~absent_j & original_j,j]='original_missing'
        categories[missing & ~absent_j & ~original_j & mask_j,j]='historical_mask'
        if j==0:
            categories[missing & ~absent_j & ~original_j & ~mask_j,j]='complete_window_no_nonzero'
    truncated=np.zeros((len(raw),2),bool)
    for j in range(2):
        for row,run in enumerate(after[:,j+1]):
            if np.isfinite(run) and 0<run<4 and not np.isfinite(x[row,int(run)]): truncated[row,j]=True
    return {'values':after,'category':categories,'absent_any':absent,'original_missing_any':original,
            'mask_any':masks,'no_nonzero_observed':~(np.isfinite(x)&(x!=0)).any(axis=1),
            'truncated_runs':truncated,'mask_only_new_na':np.isfinite(before)&~np.isfinite(after),
            'mask_changed_finite':np.isfinite(before)&np.isfinite(after)&(before!=after)}

def deduplicate_new(base, new):
    """Baseline is immutable; exact equality includes missingness, lexicographic aliases."""
    kept=dict(base); excluded={}
    lengths={len(v) for v in list(base.values())+list(new.values())}
    if len(lengths)>1 or lengths=={0}: raise ValueError('Invalid train lengths')
    for name in sorted(new):
        if name in base: raise ValueError('Name collision')
        a=np.asarray(new[name],dtype=float)
        if np.isnan(a).all(): excluded[name]='all_missing';continue
        if np.all(a==a[0]): excluded[name]='constant';continue
        alias=next((k for k,v in kept.items() if np.array_equal(a,v,equal_nan=True)),None)
        if alias is not None: excluded[name]='duplicate:'+alias
        else: kept[name]=a
    return kept,excluded
