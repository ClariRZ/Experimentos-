"""Sincroniza hitos agregados de la VM y crea commits; requiere equipo local encendido."""
import subprocess,time,pathlib,tarfile,hashlib,json,os,fcntl
REPO=pathlib.Path('/home/clara-m-rodr-guez/Documents/Codex/2026-11-07/nec/work/Segunda_competencia')
WORK=pathlib.Path('/home/clara-m-rodr-guez/Documents/Codex/2026-11-10/referenced-chatgpt-conversation-this-is-an/work')
DEST=REPO/'HISTORIA_2019_01/v3'
FLAGS=['-F','/dev/null','-i','/home/clara-m-rodr-guez/Documents/Codex/2026-11-07/nec/work/vm_key','-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=34.130.97.27','-o','UserKnownHostsFile=/home/clara-m-rodr-guez/Documents/Codex/2026-11-07/nec/work/vm_known_hosts']
STATE=WORK/'sincronizacion_v3_estado.json'
def state(**d):
 d['updated']=time.time();q=STATE.with_suffix('.tmp');q.write_text(json.dumps(d,indent=2)+'\n');q.replace(STATE);print(d,flush=True)
def git(*args):return subprocess.run(['git','-C',str(REPO),*args],capture_output=True,text=True,timeout=90,env={**os.environ,'GIT_TERMINAL_PROMPT':'0'},check=True)
def audit(x):
 if isinstance(x,dict):
  for k,v in x.items():
   if k.lower() in ['ids','prediction','predictions','password','private_key','refresh_token','access_token']:raise ValueError('Campo individual/sensible no permitido')
   audit(v)
 elif isinstance(x,list):
  if len(x)>10000:raise ValueError('Array inesperado')
  for v in x:audit(v)
def run():
 lock=(WORK/'sincronizacion_v3.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 deadline=time.time()+6*3600+600;last=None;state(status='ESPERANDO_HITO',pid=os.getpid())
 while time.time()<deadline:
  tmp=WORK/'v3_hito_descarga.tar.gz'
  try:
   result=subprocess.run(['scp',*FLAGS,'clara-m-rodr-guez@34.130.27.97:/tmp/historia_v3_agregados.tar.gz',str(tmp)],capture_output=True,timeout=45)
   if result.returncode:time.sleep(60);continue
   digest=hashlib.sha256(tmp.read_bytes()).hexdigest()
   if digest==last:time.sleep(60);continue
   records={}
   with tarfile.open(tmp) as t:
    for m in t:
     p=pathlib.PurePosixPath(m.name)
     if not m.isfile() or p.is_absolute() or '..' in p.parts or p.parts[0] not in ['resultados','auditoria','manifiestos','configuraciones'] or p.suffix!='.json' or m.size>10_000_000:raise ValueError('Archivo no permitido')
     raw=t.extractfile(m).read();d=json.loads(raw);audit(d);records[m.name]=(raw,d)
   # Never change the approved config via synchronization.
   config=records['configuraciones/protocolo.json'][0]
   if config!=(DEST/'configuraciones/protocolo.json').read_bytes():raise ValueError('Configuracion VM diferente de aprobada')
   hito=records['resultados/hitos.json'][1]['last'];changed=[]
   for name,(raw,data) in records.items():
    if name.startswith('configuraciones/'):continue
    dest=DEST/name
    if dest.exists() and dest.read_bytes()==raw:continue
    dest.parent.mkdir(parents=True,exist_ok=True);q=dest.with_suffix('.tmp');q.write_bytes(raw);q.replace(dest);changed.append(str(dest.relative_to(REPO)))
   commit=None
   if changed:
    # Refuse to consume unrelated files already staged by another process.
    if git('diff','--cached','--name-only').stdout.strip():raise ValueError('Hay cambios ajenos en staging; no crear commit')
    git('add','--',*changed);git('diff','--cached','--check');git('commit','-m',f'Registrar hito v3: {hito}');commit=git('rev-parse','HEAD').stdout.strip()
   pushed=False;push_error=None
   if (WORK/'autorizar_push_v3.txt').exists():
    try:git('push','origin','HEAD:main');pushed=True
    except Exception as e:push_error=type(e).__name__
   last=digest;state(status='HITO_GUARDADO',hito=hito,commit=commit,push=pushed,push_error=push_error,archive_sha256=digest)
   if hito in ['cierre','error','pausa_presupuesto']:return
  except Exception as e:
   state(status='ERROR_SINCRONIZACION',error=str(e)[:300]);return
  time.sleep(60)
 state(status='LIMITE_SINCRONIZACION')
if __name__=='__main__':run()
