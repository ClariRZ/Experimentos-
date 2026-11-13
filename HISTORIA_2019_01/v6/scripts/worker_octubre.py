import subprocess,sys,tarfile,time,json,os,fcntl
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'resultado';lock=open('/tmp/historia_v6.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
subprocess.run(['sudo','-n','true'],check=True)
try:
 with (root/'evaluacion.log').open('w') as log:
  r=subprocess.run([sys.executable,str(root/'scripts/evaluar_octubre.py'),'--source','/home/clarirz/HISTORIA_2019_01/v6/deployments/v6_20261113_02/resultados/entrenamiento','--dataset','/home/clarirz/HISTORIA_2019_01/datos/analistasr_competencia_2026.csv.gz','--policy',str(root/'configuraciones/octubre_v6_01.json'),'--output',str(out)],stdout=log,stderr=subprocess.STDOUT,timeout=2100)
 status={'returncode':r.returncode,'finished':time.time()}
except Exception as e:status={'error':repr(e),'finished':time.time()}
finally:
 out.mkdir(exist_ok=True);(out/'supervisor.json').write_text(json.dumps(status,indent=2))
 with tarfile.open(root/'agregados.tmp','w:gz') as t:
  for p in out.rglob('*.json'):
   if 'private' not in p.relative_to(out).parts:t.add(p,arcname=str(p.relative_to(out)))
  t.add(root/'evaluacion.log',arcname='evaluacion.log')
 (root/'agregados.tmp').replace(root/'agregados.tar.gz')
 time.sleep(180);subprocess.run(['sudo','-n','shutdown','-h','now'])
