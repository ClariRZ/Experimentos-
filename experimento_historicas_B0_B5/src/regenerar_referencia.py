"""Regenera predicciones privadas desde modelos congelados y matrices con hashes originales."""
import argparse,hashlib,json,shutil,gc
from pathlib import Path
import pandas as pd
import lightgbm as lgb
from entrenar import load_matrix,sha

p=argparse.ArgumentParser();p.add_argument('--reference',required=True);p.add_argument('--prep',required=True);p.add_argument('--out',required=True);a=p.parse_args()
ref=Path(a.reference).resolve();prep=Path(a.prep).resolve();out=Path(a.out).resolve()
assert not out.exists(),'Usar una carpeta nueva para preservar referencias'
frozen=json.loads((ref/'FROZEN.json').read_text())
assert sha(ref.parent/'config.json')==frozen['config_sha256']
assert sha(prep/'manifest.json')==frozen['manifest_sha256']
for line in (ref.parent/'auditoria/preparado_local.sha256').read_text().splitlines():
 digest,name=line.split();assert sha(prep/name)==digest,'Matriz diferente: '+name
for e,digest in frozen['models'].items():
 assert sha(ref/e/'model.txt')==digest
 assert sha(ref/e/'complete.json')==frozen['decisions'][e]
shutil.copytree(ref,out)
manifest=json.loads((prep/'manifest.json').read_text());rows=pd.read_parquet(prep/'filas.parquet')
for e in frozen['models']:
 X,_,_=load_matrix(prep,manifest,e);model=lgb.Booster(model_file=str(ref/e/'model.txt'))
 for month,name in [(201908,'validation_predictions.parquet'),(201910,'test_predictions.parquet')]:
  mask=(rows.foto_mes==month).to_numpy();pred=model.predict(X[mask],num_threads=8)
  pd.DataFrame({'numero_de_cliente':rows.loc[mask,'numero_de_cliente'].to_numpy(),'prob':pred}).to_parquet(out/e/name,index=False)
 del X,model;gc.collect()
print('REFERENCIA_REGENERADA: seis modelos, matrices y decisiones verificadas')
