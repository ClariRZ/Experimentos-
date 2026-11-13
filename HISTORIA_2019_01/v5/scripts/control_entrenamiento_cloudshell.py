"""Entrenamiento v5 autorizado, con límite GCE de seis horas y apagado al terminar."""
import argparse, hashlib, io, json, re, shlex, subprocess, tarfile, time, urllib.request
from pathlib import Path
PROJECT='proj-uba-261002122233861'
ZONE='northamerica-northeast2-b'
VM='clari-c1-fundados'
BASE='/home/clarirz/HISTORIA_2019_01'
PYTHON=BASE+'/historia_2019_v1/.venv/bin/python'

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-dir',type=Path);p.add_argument('--commit',required=True);p.add_argument('--run',required=True);a=p.parse_args()
 if not re.fullmatch(r'[0-9a-f]{40}',a.commit) or not re.fullmatch(r'entrenamiento_[0-9_]+',a.run):raise ValueError('Identificador inválido')
 home=Path.home()/a.run;home.mkdir(exist_ok=False)
 record={'commit':a.commit,'run':a.run,'training_authorized':True,'max_seconds':21600}
 def save(): (home/'control.json').write_text(json.dumps(record,indent=2))
 def cmd(args,timeout=120,check=True):
  r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
  print(r.stdout[-3000:],r.stderr[-1500:],flush=True)
  if check and r.returncode:raise RuntimeError(f'Comando falló ({r.returncode}): {args[:4]}')
  return r
 def gc(args,**kw):return cmd(['gcloud','compute',*args,'--project='+PROJECT,'--zone='+ZONE,'--quiet'],**kw)
 def describe():return json.loads(gc(['instances','describe',VM,'--format=json']).stdout)
 url=f'https://raw.githubusercontent.com/ClariRZ/Segunda_competencia/{a.commit}/HISTORIA_2019_01/v5/'
 def fetch(name):return (a.source_dir/name).read_bytes() if a.source_dir else urllib.request.urlopen(url+name,timeout=45).read()
 manifest=json.loads(fetch('MANIFIESTO_SHA256.json'))
 names=[n for n in manifest if n.startswith('scripts/') or n=='configuraciones/etapa1_autorizada_20261113.json']
 bundle=home/'codigo.tar.gz'
 with tarfile.open(bundle,'w:gz') as t:
  for n in names:
   b=fetch(n)
   if hashlib.sha256(b).hexdigest()!=manifest[n]:raise ValueError('Hash incorrecto: '+n)
   if n.endswith('etapa1_autorizada_20261113.json') and json.loads(b).get('training_authorized') is not True:raise ValueError('Contrato no permite entrenar')
   info=tarfile.TarInfo(n);info.size=len(b);t.addfile(info,io.BytesIO(b))
 record['bundle_sha256']=hashlib.sha256(bundle.read_bytes()).hexdigest()
 before=describe();record['before']=before;save()
 if before['status']!='TERMINATED':raise RuntimeError('VM no está apagada; no se modifica')
 gc(['instances','set-scheduling',VM,'--max-run-duration=21600s','--instance-termination-action=STOP'])
 scheduling=describe()['scheduling'];record['scheduling']=scheduling;save()
 if int(scheduling.get('maxRunDuration',{}).get('seconds',0))!=21600 or scheduling.get('instanceTerminationAction')!='STOP':raise RuntimeError('No se confirmó apagado automático')
 root=BASE+'/v5/deployments/'+a.run;out=root+'/resultados/entrenamiento'
 started=False;deployed=False
 try:
  started=True;deadline=time.time()+21000;record['deadline']=deadline;save()
  gc(['instances','start',VM],timeout=180)
  for attempt in range(12):
   try:
    r=gc(['ssh','clarirz@'+VM,'--command=true'],timeout=30,check=False)
    if r.returncode==0:break
   except subprocess.TimeoutExpired:pass
   time.sleep(5)
  else:raise RuntimeError('SSH no disponible')
  gc(['scp',str(bundle),'clarirz@'+VM+':/tmp/'+a.run+'.tar.gz'])
  gc(['ssh','clarirz@'+VM,'--command='+f'mkdir -p {BASE}/v5/deployments && mkdir {root} && tar -xzf /tmp/{a.run}.tar.gz -C {root}'])
  deployed=True
  worker=[PYTHON,'scripts/supervisar.py','--deadline',str(deadline),'--output',out,PYTHON,'scripts/ejecutar_etapa1.py','--config','configuraciones/etapa1_autorizada_20261113.json','--dataset',BASE+'/datos/analistasr_competencia_2026.csv.gz','--output',out,'--deadline',str(deadline)]
  remote=f'cd {shlex.quote(root)} && env POLARS_MAX_THREADS=4 PYTHONPATH={BASE}/v4/.auditdeps '+shlex.join(worker)
  r=gc(['ssh','clarirz@'+VM,'--command='+remote],timeout=max(1,int(deadline-time.time())+20),check=False)
  record['worker_returncode']=r.returncode
 except Exception as e:record['error']=repr(e)
 finally:
  if deployed:
   try:gc(['scp','clarirz@'+VM+':'+root+'/resultados/entrenamiento_agregados.tar.gz',str(home)],timeout=90)
   except Exception as e:record['recovery_error']=repr(e)
  if started:
   try:gc(['instances','stop',VM],timeout=180)
   except Exception as e:record['stop_error']=repr(e)
   try:record['final_status']=describe()['status']
   except Exception as e:record['status_error']=repr(e)
  record['finished_epoch']=time.time();save();print('CONTROL_FINAL',json.dumps(record),flush=True)
 if record.get('worker_returncode')!=0 or record.get('final_status')!='TERMINATED' or 'recovery_error' in record:raise SystemExit(1)
if __name__=='__main__':main()
