"""Start capped VM, execute inference only, recover aggregates and stop."""
import subprocess,sys,json,time,tarfile,shlex,hashlib
from pathlib import Path
from control_cloudshell import PROJECT,ZONE,VM,BASE,PYTHON
repo=Path(sys.argv[1]).resolve();home=Path.home()/'octubre_v6_01';home.mkdir(exist_ok=False)
source=repo/'HISTORIA_2019_01/v6';remote=BASE+'/v6/evaluaciones/octubre_v6_01'
record={'run':'octubre_v6_01','training_fits':0,'commit':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()}
def cmd(args,timeout=120,check=True):
 r=subprocess.run(args,text=True,capture_output=True,timeout=timeout)
 if check and r.returncode:raise RuntimeError(r.stderr[-2000:])
 return r
def gc(args,**kw):return cmd(['gcloud','compute',*args,'--project='+PROJECT,'--zone='+ZONE,'--quiet'],**kw)
def ssh(c,**kw):return gc(['ssh','clarirz@'+VM,'--command='+c],**kw)
def state():return json.loads(gc(['instances','describe',VM,'--format=json']).stdout)
def publish():
 dest=source/'auditoria/octubre_v6_01';dest.mkdir(parents=True,exist_ok=True);(dest/'control.json').write_text(json.dumps(record,indent=2)+'\n')
 cmd(['git','-C',str(repo),'add','HISTORIA_2019_01/v6'])
 if cmd(['git','-C',str(repo),'diff','--cached','--quiet'],check=False).returncode:
  cmd(['git','-C',str(repo),'commit','-m','Respalda cierre octubre v6 sin reentrenamiento']);cmd(['git','-C',str(repo),'push','origin','main'])
assert state()['status']=='TERMINATED','VM must be stopped'
gc(['instances','set-scheduling',VM,'--max-run-duration=2700s','--instance-termination-action=STOP'])
sc=state()['scheduling'];assert int(sc['maxRunDuration']['seconds'])==2700 and sc['instanceTerminationAction']=='STOP';record['verified_scheduling']=sc
bundle=home/'codigo.tar.gz'
with tarfile.open(bundle,'w:gz') as t:
 for p in (source/'scripts').glob('*.py'):t.add(p,arcname='scripts/'+p.name)
 t.add(source/'configuraciones/octubre_v6_01.json',arcname='configuraciones/octubre_v6_01.json')
record['bundle_sha256']=hashlib.sha256(bundle.read_bytes()).hexdigest();launched=False;started=False
try:
 started=True;gc(['instances','start',VM],timeout=180)
 for attempt in range(15):
  try:
   if ssh('true',timeout=30,check=False).returncode==0:break
  except subprocess.TimeoutExpired:pass
  time.sleep(5)
 else:raise RuntimeError('SSH unavailable')
 ssh("sudo -n true && ! pgrep -f '[e]jecutar_etapa1.py'")
 gc(['scp',str(bundle),'clarirz@'+VM+':/tmp/octubre_v6_01.tar.gz'])
 ssh('mkdir -p '+BASE+'/v6/evaluaciones && mkdir '+remote+' && tar -xzf /tmp/octubre_v6_01.tar.gz -C '+remote)
 code="import subprocess;f=open("+repr(remote+'/worker.log')+",'w');p=subprocess.Popen("+repr(['env','POLARS_MAX_THREADS=4','PYTHONPATH='+BASE+'/v4/.auditdeps',PYTHON,remote+'/scripts/worker_octubre.py'])+",stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True);print(p.pid)"
 launched=True;record['pid']=ssh('python3 -c '+shlex.quote(code)).stdout.strip();record['launched']=True;publish();print('LAUNCHED',record['pid'],flush=True)
 end=time.time()+2250
 while time.time()<end and state()['status']=='RUNNING':
  if ssh('test -f '+remote+'/agregados.tar.gz',check=False).returncode==0:
   gc(['scp','clarirz@'+VM+':'+remote+'/agregados.tar.gz',str(home)])
   archive=home/'agregados.tar.gz';record['archive_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest();dest=source/'resultados/octubre_v6_01'
   with tarfile.open(archive) as t:
    for m in t.getmembers():
     if not m.isfile() or Path(m.name).is_absolute() or '..' in Path(m.name).parts or 'private' in Path(m.name).parts:raise ValueError('Unsafe aggregate')
     q=dest/m.name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(t.extractfile(m).read())
   record['recovered']=True;publish();break
  time.sleep(20)
except Exception as e:record['error']=repr(e);print('ERROR',repr(e),flush=True)
finally:
 if started and (not launched or record.get('recovered')):gc(['instances','stop',VM],timeout=180)
 record['vm_status']=state()['status'];record['finished']=time.time();publish();print(json.dumps(record),flush=True)
