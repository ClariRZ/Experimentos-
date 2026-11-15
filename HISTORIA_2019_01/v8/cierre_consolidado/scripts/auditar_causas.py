"""Read-only cell-level missingness attribution for frozen B0/R3/T4 columns."""
import argparse,copy,gc,json,sys
from pathlib import Path
import numpy as np
import polars as pl
from ejecutar_v8 import sha,save

def required_lags(column):
    if '__' not in column:return [0]
    suffix=column.split('__',1)[1]
    if suffix.startswith('lag'):return [int(suffix[3:])]
    if suffix.startswith('delta'):return [0,int(suffix[5:])]
    if suffix.startswith('f3_'):return [0,1,2]
    if suffix.startswith('f2_'):return [0,1,2,3]
    raise ValueError('Unknown formula: '+column)

def attribute(missing,absent,original,mask,zero,overflow):
    result=np.full(len(missing),'finite',dtype=object);remaining=missing.copy()
    for name,condition in [('absent_client_month',absent),('original_missing_or_nonfinite',original),('historical_mask',mask),('zero_reference',zero),('float32_overflow',overflow)]:
        selected=remaining&condition;result[selected]=name;remaining&=~condition
    result[remaining]='unexpected';return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    b=a.repo/'HISTORIA_2019_01/v7';cfg=json.loads((b/'resultados/agosto/config_frozen.json').read_text());reg=json.loads((b/'resultados/agosto/feature_manifest.json').read_text())
    if sha(a.dataset)!=cfg['data']['sha256']:raise ValueError('Dataset hash')
    a.output.mkdir(parents=True,exist_ok=False);sys.path.insert(0,str(b/'scripts'));import ejecutar_v7 as old
    data=old.read_data(a.dataset,list(range(201901,201911)),labels=False);unmasked=copy.deepcopy(cfg);unmasked['data']['broken_masks']={};rows=[]
    for month in [201904,201905,201906,201908,201909,201910]:
        print('CAUSES',month,flush=True);d=data.filter(pl.col(old.MONTH).is_between(month-3,month))
        hist,_=old.history(d,cfg,[month]);raw,_=old.history(d,unmasked,[month]);ids=hist[old.ID].to_numpy();n=len(ids)
        present=np.column_stack([np.isin(ids,d.filter(pl.col(old.MONTH)==month-k)[old.ID].to_numpy()) for k in range(4)])
        for arm in ['B0','R3','T4']:
            f=hist if arm=='B0' else old.extras(hist,arm,cfg['data']['history_sources'])[0]
            orig=raw if arm=='B0' else old.extras(raw,arm,cfg['data']['history_sources'])[0]
            cols=reg[arm]['columns'];values=old.numeric(f.select(cols),cols)
            for col in cols:
                source=col.split('__',1)[0];lags=required_lags(col);inputs=[source if k==0 else f'{source}__lag{k}' for k in lags]
                original_inputs=raw.select(inputs).to_numpy();p=present[:,lags]
                absent=(~p).any(axis=1);original=(p&~np.isfinite(original_inputs)).any(axis=1)
                masked=np.broadcast_to([source in cfg['data']['broken_masks'].get(str(month-k),[]) for k in lags],original_inputs.shape)
                mask=(p&np.isfinite(original_inputs)&masked).any(axis=1)
                missing=~np.isfinite(values[col].to_numpy());zero=np.zeros(n,dtype=bool)
                if '__f3_' in col:
                    seq=hist.select(inputs).to_numpy();complete=np.isfinite(seq).all(axis=1)
                    ref=seq.mean(axis=1) if '_mean_' in col else seq[:,1] if '_prev_' in col else seq[:,2]
                    zero=complete&(ref==0)
                native=f[col].to_numpy();overflow=np.isfinite(native)&missing
                causes=attribute(missing,absent,original,mask,zero,overflow);names,counts=np.unique(causes,return_counts=True)
                row={'month':month,'arm':arm,'column':col,'denominator':'cells','n':n,'exclusive':dict(zip(names.tolist(),counts.tolist())),'overlap_absent':int(absent.sum()),'overlap_original':int(original.sum()),'overlap_mask':int(mask.sum()),'mask_only_new_na':int((missing&np.isfinite(old.numeric(orig.select(col),[col])[col].to_numpy())).sum())}
                rows.append(row)
                if 'unexpected' in row['exclusive']:
                    save(a.output/'unexpected.json',row);raise ValueError('Unexplained missingness')
            del f,orig,values;gc.collect()
        save(a.output/'coverage_causes.json',rows);del hist,raw,d;gc.collect()
    save(a.output/'status.json',{'status':'PASSED','entries':len(rows),'unexpected':0,'fits':0})
if __name__=='__main__':main()
