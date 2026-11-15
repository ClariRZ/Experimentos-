"""Explicit approved launch/recovery via gcloud. No training authorization is inferred."""
import argparse,json,os,shlex,shutil,subprocess,sys,time,uuid
from pathlib import Path
from ejecutar_v8 import validate_contract,save,sha
from operacion_v8 import VM,PROJECT,ZONE,BASE,assemble,validate_manifest

class Cloud:
    def run(self,args,check=True,timeout=180):
        return subprocess.run(['gcloud','compute',*args,'--project='+PROJECT,'--zone='+ZONE,'--quiet'],text=True,capture_output=True,check=check,timeout=timeout)
    def describe(self):return json.loads(self.run(['instances','describe',VM,'--format=json']).stdout)
    def ssh(self,command,**kw):return self.run(['ssh','clarirz@'+VM,'--command='+command],**kw)
    def scp(self,source,dest):return self.run(['scp',str(source),str(dest)],timeout=900)

def wait_ssh(cloud):
    for attempt in range(8):
        try:
            if cloud.ssh('true',check=False,timeout=45).returncode==0:return
        except subprocess.TimeoutExpired:pass
        time.sleep(5)
    raise RuntimeError('SSH unavailable; training not dispatched')

def recover(cloud,record,folder):
    folder=Path(folder);remote=record['remote'];dest=folder/'recovery';dest.mkdir(exist_ok=True)
    cloud.scp('clarirz@'+VM+':'+remote+'/backup/manifest.json',dest/'manifest.json')
    manifest=json.loads((dest/'manifest.json').read_text());validate_manifest(manifest)
    needed=sum(s['bytes'] for s in manifest['archives'].values())*2+1024**3
    if shutil.disk_usage(dest).free<needed:raise OSError('Destination lacks backup space; original retained')
    for spec in manifest['archives'].values():
        for chunk in spec['chunks']:
            # Manifest is untrusted input; names cannot escape the destination.
            name=chunk['name']
            if Path(name).name!=name or '/' in name or '..' in name:raise ValueError('Invalid chunk path')
            target=dest/name
            if target.exists() and target.stat().st_size==chunk['bytes'] and sha(target)==chunk['sha256']:continue
            partial=dest/(name+'.partial');cloud.scp('clarirz@'+VM+':'+remote+'/backup/'+name,partial)
            if partial.stat().st_size!=chunk['bytes'] or sha(partial)!=chunk['sha256']:raise ValueError('Transfer checksum mismatch')
            partial.replace(target)
    assemble(dest,manifest)
    cloud.scp(dest/'RESTORED.json','clarirz@'+VM+':'+remote+'/RECOVERED.json')
    record['recovered']=True;save(folder/'control.json',record)

def launch(repo,config,folder,cloud=None):
    cloud=cloud or Cloud();repo=repo.resolve();config=config.resolve();relative=config.relative_to(repo)
    c=json.loads(config.read_text());validate_contract(c)
    if subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip():raise ValueError('Repository must be clean')
    # Config must be included at HEAD, not merely an ignored local approval file.
    tracked=subprocess.check_output(['git','-C',str(repo),'show','HEAD:'+str(relative)])
    if tracked!=config.read_bytes():raise ValueError('Approved contract not committed')
    before=cloud.describe()
    if before['status']!='TERMINATED':raise RuntimeError('VM active; refusing to interfere')
    folder.mkdir(parents=True,exist_ok=False);(folder/'.gitignore').write_text('*\n')
    commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    archive=folder/'code.tar.gz'
    with archive.open('wb') as f:
        subprocess.run(['git','-C',str(repo),'archive','--format=tar.gz','HEAD','HISTORIA_2019_01/v8/cierre_consolidado','HISTORIA_2019_01/v7/scripts','HISTORIA_2019_01/v7/resultados/agosto/config_frozen.json'],stdout=f,check=True)
    remote=BASE+'/v8/deployments/v8_'+time.strftime('%Y%m%d_%H%M%S',time.gmtime())+'_'+uuid.uuid4().hex[:6]
    record={'commit':commit,'remote':remote,'bundle_sha256':sha(archive),'config_sha256':sha(config),'recovered':False,'dispatched':False,'vm_started':False}
    save(folder/'control.json',record)
    try:
        seconds=c['budget']['requested_max_seconds']
        cloud.run(['instances','set-scheduling',VM,'--max-run-duration='+str(seconds)+'s','--instance-termination-action=STOP'])
        scheduling=cloud.describe()['scheduling']
        if int(scheduling['maxRunDuration']['seconds'])!=seconds or scheduling['instanceTerminationAction']!='STOP':raise ValueError('Independent GCE stop not verified')
        record['scheduling']=scheduling;record['hard_deadline']=time.time()+seconds;record['vm_started']=True;save(folder/'control.json',record)
        cloud.run(['instances','start',VM]);wait_ssh(cloud)
        # Bound even a pre-dispatch setup failure; GCE remains an independent cap.
        cloud.ssh('sudo -n shutdown -h +'+str(max(1,int((record['hard_deadline']-time.time())//60))))
        cloud.ssh('mkdir -p '+shlex.quote(remote+'/repo'))
        cloud.scp(archive,'clarirz@'+VM+':'+remote+'/code.tar.gz')
        if cloud.ssh('sha256sum '+shlex.quote(remote+'/code.tar.gz')).stdout.split()[0]!=record['bundle_sha256']:raise ValueError('Uploaded code differs')
        cloud.ssh('tar -xzf '+shlex.quote(remote+'/code.tar.gz')+' -C '+shlex.quote(remote+'/repo'))
        py=BASE+'/historia_2019_v1/.venv/bin/python';script=remote+'/repo/HISTORIA_2019_01/v8/cierre_consolidado/scripts/operacion_v8.py'
        command=[py,script,'--worker','--repo',remote+'/repo','--config',remote+'/repo/'+str(relative),'--dataset',BASE+'/datos/analistasr_competencia_2026.csv.gz','--run',remote+'/run','--hard-deadline',str(record['hard_deadline'])]
        dispatch="import os,subprocess; e=os.environ.copy(); e['POLARS_MAX_THREADS']='4'; e['PYTHONPATH']="+repr(BASE+'/v4/.auditdeps')+"; f=open("+repr(remote+'/worker.log')+",'ab'); p=subprocess.Popen("+repr(command)+",stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,env=e,start_new_session=True); print(p.pid)"
        # A timed-out response may still have launched the process. Do not dispatch twice.
        record['dispatched']=True;save(folder/'control.json',record)
        record['worker_pid']=cloud.ssh(shlex.join([py,'-c',dispatch]),timeout=60).stdout.strip();save(folder/'control.json',record)
        print('DISPATCHED',remote,flush=True)
        monitor(cloud,record,folder)
    finally:
        if record['vm_started'] and (not record['dispatched'] or record['recovered']):cloud.run(['instances','stop',VM],check=False)
        record['vm_status']=cloud.describe()['status'];save(folder/'control.json',record)

def monitor(cloud,record,folder):
    last=None
    while time.time()<record['hard_deadline']:
        if cloud.describe()['status']!='RUNNING':break
        r=cloud.ssh('test -f '+shlex.quote(record['remote']+'/backup/manifest.json'),check=False,timeout=45)
        if r.returncode==0:
            recover(cloud,record,folder);return
        status=cloud.ssh('cat '+shlex.quote(record['remote']+'/run/status.json'),check=False,timeout=45)
        if status.returncode==0 and status.stdout!=last:last=status.stdout;print(last,flush=True)
        time.sleep(30)
    raise RuntimeError('Recovery not confirmed; retained source and partial copies. Do not relaunch training.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path);p.add_argument('--config',type=Path);p.add_argument('--output',type=Path);p.add_argument('--recover',type=Path);a=p.parse_args()
    if a.recover:
        folder=a.recover;record=json.loads((folder/'control.json').read_text());cloud=Cloud()
        if cloud.describe()['status']!='RUNNING':raise RuntimeError('VM stopped; no automatic restart or new training')
        monitor(cloud,record,folder)
        if record['recovered']:cloud.run(['instances','stop',VM])
        record['vm_status']=cloud.describe()['status'];save(folder/'control.json',record)
    elif all([a.repo,a.config,a.output]):launch(a.repo,a.config,a.output)
    else:p.error('Provide --repo --config --output, or --recover EXISTING_CONTROL_FOLDER')
if __name__=='__main__':main()
