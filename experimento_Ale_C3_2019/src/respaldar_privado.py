"""Respaldo local privado; no sube archivos a servicios externos."""
from pathlib import Path
import argparse,hashlib,json,tarfile
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);a=p.parse_args();r=a.root.resolve()
assert json.loads((r/'verificacion_final.json').read_text())['status']=='verified'
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as s:
  for chunk in iter(lambda:s.read(8*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
files=[]
for sub in ['src','vendor','resultados','incidente_pretrial','incidente_semilla20']:
 for f in (r/sub).rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc':files.append((f,str(f.relative_to(r))))
for f in r.iterdir():
 if f.is_file() and f.suffix in ['.json','.csv','.md','.txt','.sh','.html','.png','.log'] and not f.name.startswith('respaldo_'):files.append((f,f.name))
for name in ['READY.json','cobertura.csv']:files.append((r/'preparado'/name,'preparado/'+name))
for name in ['filas.parquet','meta_desarrollo.parquet','meta_test_sellado.parquet','manifest.json']:files.append((a.parent/'preparado'/name,'metadata_2019/'+name))
manifest={name:{'sha256':sha(f),'bytes':f.stat().st_size} for f,name in files};m=r/'respaldo_manifest.json';m.write_text(json.dumps({'private':True,'files':manifest},indent=2));files.append((m,m.name));target=r/'respaldo_privado_Ale_C3_2019.tar.gz'
with tarfile.open(target,'w:gz',compresslevel=3) as tar:
 for f,name in sorted(files,key=lambda pair:pair[1]):tar.add(f,arcname=name,recursive=False)
record={'archive':target.name,'sha256':sha(target),'bytes':target.stat().st_size,'files':len(files),'private':True,'raw_data_and_matrices_included':False};(r/'respaldo_sha256.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
