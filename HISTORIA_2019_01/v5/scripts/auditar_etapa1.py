"""Construye matrices v5 sin ajustar modelos ni consultar octubre."""
import argparse,hashlib,json,os,platform,shutil,sys,time,resource
from pathlib import Path
from importlib.metadata import version
import polars as pl
from ejecutar_etapa1 import prepare,sha,save,TRAIN

def main():
 p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--deadline',type=float,required=True);a=p.parse_args()
 cfg=json.loads(a.config.read_text());start=time.time()
 if a.deadline<=start:raise ValueError('Deadline vencido')
 if a.output.exists():raise FileExistsError(a.output)
 a.output.mkdir(parents=True);art=a.output/'private';art.mkdir()
 def check():
  if time.time()>=a.deadline:raise TimeoutError('Limite auditoria')
  if shutil.disk_usage(a.output).free<10*2**30:raise RuntimeError('Disco insuficiente')
 check()
 digest=sha(a.dataset)
 if digest!=cfg['data']['sha256']:raise ValueError('Dataset no coincide')
 env={'python':sys.version,'platform':platform.platform(),'packages':{n:version(n) for n in ['numpy','polars','lightgbm','optuna','scikit-learn']},'cpu_count':os.cpu_count(),'memory':Path('/proc/meminfo').read_text(),'disk_free_bytes':shutil.disk_usage(a.output).free}
 save(a.output/'entorno.json',env);save(a.output/'config_frozen.json',cfg)
 save(a.output/'code_identity.json',{p.name:sha(p) for p in Path(__file__).parent.glob('*.py')})
 df=pl.scan_csv(a.dataset,infer_schema_length=20000).filter(pl.col('foto_mes').is_between(201901,201908)).collect();check()
 reg=prepare(df,cfg,art,a.output,check)
 meta=pl.read_parquet(art/'meta.parquet');tr=meta.filter(pl.col('foto_mes').is_in(TRAIN));va=meta.filter(pl.col('foto_mes')==201908)
 save(a.output/'FINAL.json',{'status':'AUDITORIA_COMPLETA_SIN_ENTRENAR','fits':0,'october_used':False,'dataset_sha256':digest,'n_train':len(tr),'n_valid':len(va),'train_keys_sha256':hashlib.sha256(tr.select(['numero_de_cliente','foto_mes']).to_numpy().tobytes()).hexdigest(),'valid_ids_sha256':hashlib.sha256(va['numero_de_cliente'].to_numpy().tobytes()).hexdigest(),'arms':{k:{'columns':len(v['columns']),'columns_sha256':hashlib.sha256(json.dumps(v['columns'],separators=(',',':')).encode()).hexdigest(),'excluded':len(v['excluded'])} for k,v in reg.items()},'seconds':time.time()-start,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024})
 print((a.output/'FINAL.json').read_text(),flush=True)
if __name__=='__main__':main()
