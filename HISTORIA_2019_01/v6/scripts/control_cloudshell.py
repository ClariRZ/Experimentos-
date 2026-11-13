"""Launch exact committed code, recover aggregates, publish milestones and stop VM."""
import argparse,hashlib,io,json,re,shlex,subprocess,tarfile,time
from pathlib import Path
PROJECT='proj-uba-261002122233861';ZONE='northamerica-northeast2-b';VM='clari-c1-fundados'
BASE='/home/clarirz/HISTORIA_2019_01';PYTHON=BASE+'/historia_2019_v1/.venv/bin/python'

def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--commit',required=True);p.add_argument('--run',required=True);p.add_argument('--deadline',type=float);p.add_argument('--use-running-vm',action='store_true');a=p.parse_args()
 if not re.fullmatch(r'[0-9a-f]{40}',a.commit) or not re.fullmatch(r'v6_[0-9_]+',a.run):raise ValueError('Invalid run identity')
 repo=a.repo.resolve();source=repo/'HISTORIA_2019_01/v6'
 def command(args,timeout=120,check=True):
  r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
  if r.returncode and check:raise RuntimeError(r.stderr[-2000:])
  return r
 if command(['git','-C',str(repo),'rev-parse','HEAD']).stdout.strip()!=a.commit:raise ValueError('Commit mismatch')
 home=Path.home()/a.run;home.mkdir(exist_ok=False)
 root=BASE+'/v6/deployments/'+a.run
 record={'run':a.run,'commit':a.commit,'vm':VM,'project':PROJECT,'zone':ZONE,'remote_root':root,'max_seconds':21600,'october_used':False}
 def save(): (home/'control.json').write_text(json.dumps(record,indent=2))
 def gc(args,**kw):return command(['gcloud','compute',*args,'--project='+PROJECT,'--zone='+ZONE,'--quiet'],**kw)
 def describe():return json.loads(gc(['instances','describe',VM,'--format=json']).stdout)
 def ssh(cmd,**kw):return gc(['ssh','clarirz@'+VM,'--command='+cmd],**kw)
 manifest=json.loads((source/'MANIFIESTO_SHA256.json').read_text());bundle=home/'codigo.tar.gz'
 with tarfile.open(bundle,'w:gz') as t:
  for n,h in manifest.items():
   if not n.startswith(('scripts/','configuraciones/','pruebas/')):continue
   b=(source/n).read_bytes()
   if hashlib.sha256(b).hexdigest()!=h:raise ValueError('Hash mismatch '+n)
   info=tarfile.TarInfo(n);info.size=len(b);t.addfile(info,io.BytesIO(b))
 record['bundle_sha256']=hashlib.sha256(bundle.read_bytes()).hexdigest()
 before=describe()
 if a.deadline is not None and a.deadline<=time.time()+600:raise ValueError('Insufficient remaining approved time')
 cap=21600 if a.deadline is None else min(21600,int(a.deadline-time.time())+600)
 if a.use_running_vm:
  if before['status']!='RUNNING' or a.deadline is None:raise ValueError('Recovery requires running VM and original deadline')
  from datetime import datetime
  scheduling=before['scheduling'];cap=int(scheduling.get('maxRunDuration',{}).get('seconds',0))
  absolute_stop=datetime.fromisoformat(before['lastStartTimestamp']).timestamp()+cap
  if not 0<cap<=21600 or absolute_stop>a.deadline+620:raise ValueError('Existing stop cap would extend approved budget')
 else:
  if before['status']!='TERMINATED':raise RuntimeError('VM is not stopped; refusing concurrent run')
  gc(['instances','set-scheduling',VM,'--max-run-duration='+str(cap)+'s','--instance-termination-action=STOP'])
  scheduling=describe()['scheduling']
 record['max_seconds']=cap
 if int(scheduling.get('maxRunDuration',{}).get('seconds',0))!=cap or scheduling.get('instanceTerminationAction')!='STOP':raise RuntimeError('Provider stop cap unverified')
 record['verified_scheduling']={k:scheduling[k] for k in ['maxRunDuration','instanceTerminationAction']}
 started=False;launched=False
 def publish(label):
  dest=repo/'HISTORIA_2019_01/v6/auditoria'/a.run;dest.mkdir(parents=True,exist_ok=True)
  (dest/'control_publico.json').write_text(json.dumps(record,indent=2))
  command(['git','-C',str(repo),'add','HISTORIA_2019_01/v6'])
  if command(['git','-C',str(repo),'diff','--cached','--quiet'],check=False).returncode:
   command(['git','-C',str(repo),'commit','-m',label])
   command(['git','-C',str(repo),'push','origin','main'])
 try:
  record['started_epoch']=time.time();record['deadline']=a.deadline if a.deadline is not None else time.time()+21000;save()
  started=True
  if not a.use_running_vm:gc(['instances','start',VM],timeout=180)
  for attempt in range(15):
   try:
    if ssh('true',timeout=30,check=False).returncode==0:break
   except subprocess.TimeoutExpired:pass
   time.sleep(5)
  else:raise RuntimeError('SSH unavailable')
  # Reject any already-running experiment before creating this deployment.
  ssh("sudo -n true && ! pgrep -f '[e]jecutar_etapa1.py'",timeout=30)
  gc(['scp',str(bundle),'clarirz@'+VM+':/tmp/'+a.run+'.tar.gz'])
  ssh(f'mkdir -p {BASE}/v6/deployments && mkdir {root} && tar -xzf /tmp/{a.run}.tar.gz -C {root}')
  cmd=[PYTHON,'scripts/worker_vm.py','--deadline',str(record['deadline']),'--dataset',BASE+'/datos/analistasr_competencia_2026.csv.gz']
  launch_code="import subprocess;from pathlib import Path;root=Path("+repr(root)+");log=(root/'worker.log').open('w');p=subprocess.Popen("+repr(['env','POLARS_MAX_THREADS=4','PYTHONPATH='+BASE+'/v4/.auditdeps',*cmd])+",cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True);print(p.pid)"
  # Mark dispatch before SSH: an ambiguous timeout must never stop a possible worker.
  launched=True;record['worker_dispatch_attempted']=True;save()
  r=ssh('python3 -c '+shlex.quote(launch_code),timeout=120)
  record['worker_launched']=True;record['worker_pid']=r.stdout.strip();save();publish('Registra lanzamiento v6 y límite GCE verificado')
  print('V6_LAUNCHED',json.dumps(record),flush=True)
  previous=None
  while time.time()<record['deadline']+60:
   if describe()['status']!='RUNNING':break
   r=ssh(f'cat {root}/resultados/entrenamiento/status.json',check=False)
   try:status=json.loads(r.stdout)
   except ValueError:time.sleep(30);continue
   record['last_status']=status;save()
   milestone=status.get('arm'),status.get('status')
   if milestone!=previous:
    print('V6_STATUS',json.dumps(status),flush=True);previous=milestone
   # Terminal supervisor archive is complete and excludes private data.
   done=ssh(f'test -f {root}/resultados/entrenamiento_agregados.tar.gz',check=False).returncode==0
   if done:
    gc(['scp','clarirz@'+VM+':'+root+'/resultados/entrenamiento_agregados.tar.gz',str(home)])
    archive=home/'entrenamiento_agregados.tar.gz';record['archive_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
    dest=repo/'HISTORIA_2019_01/v6/resultados'/a.run
    with tarfile.open(archive) as t:
     for m in t.getmembers():
      parts=Path(m.name).parts
      if not m.isfile() or '..' in parts or 'private' in parts or not m.name.endswith(('.json','.log')):continue
      q=dest.joinpath(*parts[1:]);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(t.extractfile(m).read())
    record['recovered']=True;save();publish('Respalda resultados agregados de v6');break
   time.sleep(30)
 except Exception as e:record['error']=repr(e);print('CONTROL_ERROR',repr(e),flush=True)
 finally:
  # If a detached worker was launched, never kill it due to a transient controller error.
  # Worker shutdown + GCE maximum remain active independent of this controller.
  if started and (not launched or record.get('recovered')):
   try:gc(['instances','stop',VM],timeout=180)
   except Exception as e:record['stop_error']=repr(e)
  try:record['vm_status']=describe()['status']
  except Exception as e:record['status_error']=repr(e)
  record['controller_finished_epoch']=time.time();save()
  try:publish('Actualiza control y estado de v6')
  except Exception as e:print('PUBLISH_FAILED',repr(e),flush=True)
if __name__=='__main__':main()
