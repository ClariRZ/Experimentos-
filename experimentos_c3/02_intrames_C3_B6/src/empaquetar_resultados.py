"""Respaldo privado completo y paquete agregado; ejecutar sólo al terminar."""
import argparse,hashlib,json,tarfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--parent-prep',type=Path,required=True);a=p.parse_args();root=a.root.resolve()
assert (root/'COMPLETADO.txt').exists()
assert json.loads((root/'verificacion_final.json').read_text())['gains_recomputed_from_all_scores']
files=[]
for dirname in ['src','vendor','config','resultados','referencia_s3']:
 for f in (root/dirname).rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc':files.append((f,str(f.relative_to(root))))
for name in ['requirements_vm.txt','PROTOCOLO.txt','REPRODUCIR.txt','PROCEDENCIA.json','run_vm.sh','corrida.log','COMPLETADO.txt','auditoria_runtime.json','verificacion_final.json','modelos_sha256.json','cambios_seleccion.csv','composicion_11000.csv']:
 f=root/name
 if f.exists():files.append((f,name))
for pattern in ['*READY.json','*cobertura.csv','c3_filas.parquet']:
 for f in (root/'preparado').glob(pattern):files.append((f,str(f.relative_to(root))))
for name in ['meta_desarrollo.parquet','meta_test_sellado.parquet','filas.parquet']:
 f=a.parent_prep/name;files.append((f,'metadata_2019/'+name))
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as stream:
  for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
manifest={n:{'sha256':sha(f),'bytes':f.stat().st_size} for f,n in files}
m=root/'manifest_respaldo_privado.json';m.write_text(json.dumps({'warning':'Contiene IDs, etiquetas y predicciones. Mantener privado; no agregar a Git.','files':manifest},indent=2));files.append((m,m.name))
archive=root/'respaldo_privado_c3_b6.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=3) as tar:
 for f,n in sorted(files,key=lambda x:x[1]):tar.add(f,arcname=n,recursive=False)
(root/'respaldo_privado.sha256').write_text(sha(archive)+'  '+archive.name+'\n')
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive),'files':len(files)}))
