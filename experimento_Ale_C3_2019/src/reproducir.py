"""Reproducir en directorio NUEVO; las métricas publicadas nunca son checkpoints."""
import argparse,subprocess,shutil,sys,os
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True,help='Corrida privada B0–B5 completa, con preparado y resultados B2');p.add_argument('--out',type=Path,required=True);p.add_argument('--python',type=Path);p.add_argument('--data',type=Path);a=p.parse_args()
source=Path(__file__).resolve().parents[1];parent=a.parent.resolve();dest=a.out.resolve();python=a.python.absolute() if a.python else parent/'.venv/bin/python';data=a.data.resolve() if a.data else parent/'data/competencia_02_crudo.parquet'
if dest.exists():raise SystemExit('El directorio --out debe ser nuevo; no reutilizar resultados publicados como checkpoints.')
for f in [python,data,parent/'preparado/manifest.json',parent/'resultados/B2/model.txt',parent/'resultados/B2/validation_predictions.parquet',parent/'resultados/B2/test_predictions.parquet']:
 if not f.exists():raise SystemExit('Falta insumo privado requerido: '+str(f))
dest.mkdir(parents=True)
for name in ['src','vendor']:shutil.copytree(source/name,dest/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for name in ['config_propuesta.json','variables_propuestas.csv','PROTOCOLO.md','IMPLEMENTACION.txt','REPRODUCIR.txt','bibliografia.txt']:shutil.copy2(source/name,dest/name)
with (dest/'requirements_vm.txt').open('w') as f:subprocess.run([str(python),'-m','pip','freeze'],stdout=f,check=True)
def run(name,*args):subprocess.run([str(python),str(dest/'src'/name),*map(str,args)],cwd=dest,check=True)
run('test_reglas.py');run('preparar.py','--parent',parent,'--data',data)
run('ejecutar.py','--parent',parent,'--mode','train');run('ejecutar.py','--parent',parent,'--mode','evaluate')
run('verificar.py','--root',dest,'--parent',parent);run('informe.py','--root',dest)
print('Reproducción completa y verificada:',dest/'informe.html')
