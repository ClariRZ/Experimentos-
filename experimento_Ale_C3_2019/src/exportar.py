"""Paquete agregado por lista permitida. Nunca exporta filas, IDs ni scores."""
import argparse,tarfile,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();r=a.root
assert json.loads((r/'verificacion_final.json').read_text())['status']=='verified'
files=[]
for f in (r/'resultados').rglob('*'):
 if f.is_file() and (f.suffix=='.json' or f.name in ['importance.csv','trials.csv','resumen.csv','por_semilla.csv','contrastes.csv','seleccion.csv']):files.append(f)
for name in ['preparado/READY.json','preparado/cobertura.csv','requirements_vm.txt','verificacion_final.json','modelos_sha256.json','COMPLETADO.txt','entorno.json']:
 f=r/name
 if f.exists():files.append(f)
with tarfile.open(r/'agregados_finales.tar.gz','w:gz') as t:
 for f in sorted(files):t.add(f,arcname=str(f.relative_to(r)),recursive=False)
print('Aggregate files:',len(files))
