"""Bounded VM supervision and resumable private backup; import has no side effects."""
import argparse,fcntl,hashlib,json,math,os,re,shlex,shutil,signal,socket,subprocess,sys,tarfile,time
from pathlib import Path
from ejecutar_v8 import save,sha,validate_contract

VM='clari-c1-fundados'
PROJECT='proj-uba-261002122233861'
ZONE='northamerica-northeast2-b'
BASE='/home/clarirz/HISTORIA_2019_01'
CHUNK=32*1024**2

def supervise(command,log,deadline,min_free,max_rss,poll_seconds=2):
    """Wall-time/resource guard in a process independent of the training worker."""
    reason=None;peak=0
    with Path(log).open('ab') as stream:
        process=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            while process.poll() is None:
                try:
                    fields=Path(f'/proc/{process.pid}/status').read_text().splitlines()
                    rss=next(int(x.split()[1])*1024 for x in fields if x.startswith('VmRSS:'));peak=max(peak,rss)
                except (OSError,StopIteration):rss=0
                if time.time()>=deadline:reason='TIME_CAP'
                elif shutil.disk_usage(Path(log).parent).free<min_free:reason='DISK_CAP'
                elif rss>max_rss:reason='RAM_CAP'
                if reason:break
                time.sleep(poll_seconds)
        finally:
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=15)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
    return {'returncode':process.returncode,'reason':reason,'peak_rss_bytes':peak,'finished_epoch':time.time()}

def verify_archive(path,expected):
    if sha(path)!=expected['sha256']:raise ValueError('Archive checksum mismatch')
    found={}
    with tarfile.open(path,'r|gz') as tar:
        for member in tar:
            if not member.isfile() or member.name not in expected['members'] or member.name in found:raise ValueError('Unexpected archive member')
            h=hashlib.sha256()
            with tar.extractfile(member) as f:
                while block:=f.read(8*1024**2):h.update(block)
            found[member.name]={'bytes':member.size,'sha256':h.hexdigest()}
    if found!=expected['members']:raise ValueError('Restoration verification failed')

def package(run,dest,chunk_size=CHUNK):
    """Create self-verifying private/public archives. Never delete run artifacts."""
    run=Path(run);dest=Path(dest);dest.mkdir(exist_ok=False)
    files=[]
    for p in sorted(run.rglob('*')):
        if p.is_symlink():raise ValueError('Unexpected symlink')
        if p.is_file() and p.name!='run.lock':files.append(p)
    size=sum(p.stat().st_size for p in files)
    if shutil.disk_usage(dest).free < 2*size+1024**3:raise OSError('Insufficient packaging reserve')
    manifest={'archives':{},'created_epoch':time.time()}
    for label,is_private in [('public',False),('private',True)]:
        paths=[p for p in files if (p.relative_to(run).parts[0]=='private')==is_private]
        members={str(p.relative_to(run)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths}
        archive=dest/(label+'.tar.gz')
        with tarfile.open(archive,'w:gz',compresslevel=1) as tar:
            for p in paths:tar.add(p,arcname=str(p.relative_to(run)),recursive=False)
        spec={'bytes':archive.stat().st_size,'sha256':sha(archive),'members':members,'chunks':[]}
        verify_archive(archive,spec)
        with archive.open('rb') as f:
            i=0
            while block:=f.read(chunk_size):
                name=f'{label}.part{i:05d}';(dest/name).write_bytes(block)
                spec['chunks'].append({'name':name,'bytes':len(block),'sha256':hashlib.sha256(block).hexdigest()});i+=1
        manifest['archives'][archive.name]=spec
    save(dest/'manifest.json',manifest);return manifest

def validate_manifest(manifest):
    if set(manifest['archives']) != {'public.tar.gz','private.tar.gz'}:
        raise ValueError('Unexpected archive names')
    for name,spec in manifest['archives'].items():
        label=name.split('.')[0]
        if not spec['chunks'] or sum(c['bytes'] for c in spec['chunks'])!=spec['bytes']:
            raise ValueError('Invalid chunk sizes')
        for i,c in enumerate(spec['chunks']):
            if c['name']!=f'{label}.part{i:05d}' or c['bytes']<=0:
                raise ValueError('Invalid chunk name or size')
        for item in [spec,*spec['chunks'],*spec['members'].values()]:
            if not re.fullmatch('[0-9a-f]{64}',item['sha256']):raise ValueError('Invalid checksum')
        for member in spec['members']:
            path=Path(member)
            if path.is_absolute() or '..' in path.parts:raise ValueError('Invalid member path')

def assemble(folder,manifest):
    """Idempotent local reconstruction; verify every file before marking recovered."""
    folder=Path(folder);validate_manifest(manifest)
    for name,spec in manifest['archives'].items():
        target=folder/name
        if target.exists() and sha(target)==spec['sha256']:verify_archive(target,spec);continue
        with (folder/(name+'.partial')).open('wb') as out:
            for chunk in spec['chunks']:
                p=folder/chunk['name']
                if p.stat().st_size!=chunk['bytes'] or sha(p)!=chunk['sha256']:raise ValueError('Chunk mismatch')
                with p.open('rb') as f:shutil.copyfileobj(f,out,8*1024**2)
            out.flush();os.fsync(out.fileno())
        verify_archive(folder/(name+'.partial'),spec);(folder/(name+'.partial')).replace(target)
    save(folder/'RESTORED.json',{'verified':True,'archive_hashes':{n:s['sha256'] for n,s in manifest['archives'].items()}})

def worker(repo,config,dataset,run,hard_deadline):
    # Refuse shutdown commands on a notebook or a different host.
    if socket.gethostname().split('.')[0]!=VM:raise RuntimeError('Worker is restricted to the authorized VM')
    c=json.loads(config.read_text());validate_contract(c)
    if not time.time()+900<hard_deadline<=time.time()+c['budget']['requested_max_seconds']:raise ValueError('Invalid deadline')
    lock=open('/tmp/historia_experiment.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    run.mkdir(parents=True,exist_ok=False)
    # The controller must also set and verify the independent GCE STOP timer.
    subprocess.run(['sudo','-n','shutdown','-h','+'+str(max(1,math.ceil((hard_deadline-time.time())/60)))],check=True)
    script=Path(__file__).parent;summary={'stages':[],'hard_deadline':hard_deadline,'recovered':False};backup=run.parent/'backup'
    try:
        commands=[['--repo',str(repo),'--config',str(config),'--dataset',str(dataset),'--output',str(run)],['--repo',str(repo),'--run',str(run),'--dataset',str(dataset)]]
        for name,args in zip(['ejecutar_v8.py','evaluar_v8.py'],commands):
            stage=supervise([sys.executable,str(script/name),*args],run/'runner.log',hard_deadline-900,c['budget']['required_free_disk_bytes'],c['budget']['max_rss_bytes'])
            summary['stages'].append({'stage':name,**stage});save(run/'supervisor.json',summary)
            if stage['returncode']!=0:break
        manifest=package(run,backup)
        while time.time()<hard_deadline-60:
            receipt=run.parent/'RECOVERED.json'
            if receipt.exists():
                received=json.loads(receipt.read_text())
                expected={n:s['sha256'] for n,s in manifest['archives'].items()}
                if received.get('archive_hashes')==expected:summary['recovered']=True;break
            time.sleep(5)
    except Exception as error:
        summary['error']={'type':type(error).__name__,'message':str(error)}
        raise
    finally:
        save(run.parent/'worker_final.json',summary)
        subprocess.run(['sudo','-n','shutdown','-h','now'],check=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true');p.add_argument('--repo',type=Path);p.add_argument('--config',type=Path);p.add_argument('--dataset',type=Path);p.add_argument('--run',type=Path);p.add_argument('--hard-deadline',type=float);a=p.parse_args()
    if not a.worker:p.error('This entrypoint is only the VM worker; controller must verify GCE limits first')
    worker(a.repo,a.config,a.dataset,a.run,a.hard_deadline)
if __name__=='__main__':main()
