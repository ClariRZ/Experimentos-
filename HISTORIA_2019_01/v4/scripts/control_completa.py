"""Ejecutar desde Cloud Shell del propietario. Siempre intenta apagar la VM."""
import subprocess,time,json,shlex
from pathlib import Path
ROOT='/home/clarirz/HISTORIA_2019_01/v4';NAME='completa_20261111_03'
BASE=['--project=proj-uba-261002122233861','--zone=northamerica-northeast2-b']
VM='clari-c1-fundados';OWNER='clarirz@'+VM
home=Path.home();start=time.time();deadline=start+57600;record={'started':start,'deadline':deadline,'run':NAME}
def call(args,timeout=120,check=True):
 print('STEP',args[:4],flush=True);return subprocess.run(args,timeout=timeout,check=check)
def ssh(cmd,timeout=120,check=True):return call(['gcloud','compute','ssh',OWNER,*BASE,'--quiet','--command',cmd],timeout,check)
try:
 call(['gcloud','compute','instances','start',VM,*BASE,'--format=value(status)','--quiet'],180)
 for attempt in range(12):
  try:
   if ssh('true',60,False).returncode==0:break
  except subprocess.TimeoutExpired:print('Esperando SSH',attempt,flush=True)
  time.sleep(5)
 else:raise RuntimeError('SSH owner unavailable')
 call(['gcloud','compute','scp',str(home/'v4_completa_codigo.tar.gz'),OWNER+':/tmp/v4_completa_codigo.tar.gz',*BASE,'--quiet'])
 ssh('tar -xzf /tmp/v4_completa_codigo.tar.gz -C '+ROOT+' && python3 '+ROOT+'/scripts/preparar_completa.py')
 py='/home/clarirz/HISTORIA_2019_01/historia_2019_v1/.venv/bin/python'
 out=ROOT+'/resultados/'+NAME
 cmd=f'cd {ROOT} && POLARS_MAX_THREADS=4 PYTHONPATH={ROOT}/.auditdeps {py} -m pytest pruebas -q && nohup env POLARS_MAX_THREADS=4 {py} scripts/supervisar_completa.py --deadline {deadline-120} --output {out} {py} scripts/ejecutar_completa.py --config configuraciones/ejecucion_completa.json --dataset /home/clarirz/HISTORIA_2019_01/datos/analistasr_competencia_2026.csv.gz --output {out} --deadline {deadline-120} < /dev/null > {out}_supervisor.log 2>&1 & wait'
 r=ssh(cmd,max(1,deadline-time.time()-90),False);record['remote_returncode']=r.returncode
except Exception as e:record['error']=repr(e);print('ERROR',repr(e),flush=True)
finally:
 try:
  call(['gcloud','compute','scp',OWNER+':'+ROOT+'/resultados/'+NAME+'_agregados.tar.gz',str(home/(NAME+'_agregados.tar.gz')),*BASE,'--quiet'],60)
  record['aggregate_downloaded_to_cloudshell']=True
 except Exception as e:record['download_error']=repr(e)
 try:
  call(['gcloud','compute','instances','stop',VM,*BASE,'--format=value(status)','--quiet'],180)
  p=subprocess.run(['gcloud','compute','instances','describe',VM,*BASE,'--format=value(status)'],text=True,capture_output=True,timeout=45,check=True);record['vm_final_status']=p.stdout.strip()
 except Exception as e:record['shutdown_error']=repr(e)
 record['finished']=time.time();(home/(NAME+'_control.json')).write_text(json.dumps(record,indent=2));print('FINAL',record,flush=True)
