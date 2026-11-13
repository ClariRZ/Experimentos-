"""Read-only experiment checkpoint; export only aggregate JSON and logs to Git."""
import argparse, hashlib, json, re, shlex, subprocess, tarfile, time
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--run',required=True)
    a=p.parse_args()
    if not re.fullmatch(r'v6_[0-9_]+',a.run): raise ValueError('Invalid run')
    repo=a.repo.resolve()
    root='/home/clarirz/HISTORIA_2019_01/v6/deployments/'+a.run
    archive_name='/tmp/'+a.run+'_snapshot.tar.gz'
    remote="""import tarfile
from pathlib import Path
root=Path(ROOT)
out=root/'resultados/entrenamiento'
assert (out/'audit_gate.json').exists(), 'Audit gate not complete yet'
with tarfile.open(ARCHIVE,'w:gz') as t:
 for p in out.rglob('*.json'):
  if 'private' not in p.relative_to(out).parts:
   t.add(p,arcname=str(p.relative_to(out)))
 t.add(root/'resultados/entrenamiento.log',arcname='ejecucion.log')
""".replace('ROOT',repr(root)).replace('ARCHIVE',repr(archive_name))
    flags=['--project=proj-uba-261002122233861','--zone=northamerica-northeast2-b','--quiet']
    subprocess.run(['gcloud','compute','ssh','clarirz@clari-c1-fundados','--command=python3 -c '+shlex.quote(remote),*flags],check=True,timeout=120)
    local=Path.home()/a.run/Path(archive_name).name
    subprocess.run(['gcloud','compute','scp','clarirz@clari-c1-fundados:'+archive_name,str(local),*flags],check=True,timeout=120)
    dest=repo/'HISTORIA_2019_01/v6/auditoria'/a.run/'snapshot'
    with tarfile.open(local) as t:
        for m in t.getmembers():
            parts=Path(m.name).parts
            if not m.isfile() or m.name.startswith('/') or '..' in parts or 'private' in parts:continue
            if not m.name.endswith(('.json','.log')):continue
            q=dest.joinpath(*parts);q.parent.mkdir(parents=True,exist_ok=True)
            q.write_bytes(t.extractfile(m).read())
    record={'captured_epoch':time.time(),'archive_sha256':hashlib.sha256(local.read_bytes()).hexdigest(),'kind':'live_checkpoint_not_final','source_run':a.run,'note':'Files copied during execution; individual writes are atomic, snapshot is not a simultaneous transaction.'}
    (dest/'CHECKPOINT.json').write_text(json.dumps(record,indent=2))
    rel=str(dest.relative_to(repo))
    subprocess.run(['git','-C',str(repo),'add',rel],check=True)
    subprocess.run(['git','-C',str(repo),'commit','-m','Respalda auditoría real y avance agregado de '+a.run],check=True)
    subprocess.run(['git','-C',str(repo),'push','origin','main'],check=True)
    print('CHECKPOINT_PUBLISHED',json.dumps(record),flush=True)

if __name__=='__main__':main()
