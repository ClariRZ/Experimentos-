"""Cloud Shell launch, bounded VM lifetime and private recovery. Standard library only."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import time
from control_auditoria import PROJECT, ZONE, VM, BASE, PY


def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def validate_launch_gate(cfg):
    if not cfg.get('training_authorized') or not cfg.get('real_audit_approved') or not cfg.get('sanitation_review',{}).get('resolved'):
        raise ValueError('V7 BLOCKED: method/sanitation review unresolved; no Cloud calls permitted')


def validate_audit(path,cfg):
    if digest(path)!=cfg['real_audit_sha256']:raise ValueError('Audit hash mismatch')
    a=json.loads(Path(path).read_text())
    if a['dataset_sha256']!=cfg['data']['sha256'] or a['october_labels_accessed'] or a['training_executed']:
        raise ValueError('Audit provenance mismatch')
    rows={(x['month'],x['variable']):x for x in a['variable_month_statistics']}
    if len(a['raw_columns'])!=152 or len(rows)!=1520:raise ValueError('Incomplete audit')
    for name in cfg['data']['broken_masks'].get('201907',[]):
        x=rows[201907,name];prev=rows[201906,name]
        if not (x['zeros']+x['nulls']==x['rows'] and x['nonfinite']==0 and
                x['distinct_finite']==1 and x['minimum']==x['maximum']==0 and prev['distinct_finite']>1):
            raise ValueError('July hypothesis not supported by full audit: '+name)
    for expected in cfg.get('sanitation_review',{}).get('july_expected_statistics',[]):
        actual=rows[(expected['month'],expected['variable'])]
        if any(actual.get(k)!=v for k,v in expected.items()):
            raise ValueError('Reviewed July statistics mismatch')
    for name in cfg['data']['broken_masks'].get('201910',[]):
        if rows[201910,name]['zeros']!=rows[201910,name]['rows'] or rows[201909,name]['distinct_finite']<=1:
            raise ValueError('October mask not supported: '+name)
    return a


def verify_archive(path):
    meta=json.loads(Path(str(path)+'.json').read_text())
    if digest(path)!=meta['sha256']:raise ValueError('Recovery archive hash mismatch')
    with tarfile.open(path) as t:
        for m in t.getmembers():
            if not m.isfile() or Path(m.name).is_absolute() or '..' in Path(m.name).parts:
                raise ValueError('Unsafe archive member')
            with t.extractfile(m) as f:
                while f.read(1024*1024):pass


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--audit-root',type=Path,default=Path.home());a=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    cfg=json.loads((root/'configuraciones/contrato_v7.json').read_text())
    validate_launch_gate(cfg)
    manifest=json.loads((root/'MANIFIESTO_CODIGO.json').read_text())
    for name,expected in manifest.items():
        if digest(root/name)!=expected:raise ValueError('Code/config modified: '+name)
    audits=[x for x in a.audit_root.glob('v7_auditoria_resultado_*/calidad.json') if digest(x)==cfg['real_audit_sha256']]
    if not audits:raise FileNotFoundError('Exact recovered calidad.json not found; VM remains off')
    validate_audit(audits[0],cfg)
    a.output.mkdir(parents=True,exist_ok=False)
    run='v7_'+time.strftime('%Y%m%d_%H%M%S',time.gmtime())
    remote=BASE+'/v7/deployments/'+run
    record={'run':run,'remote':remote,'training_confirmed':False,'recovered':False,'hard_cap_seconds':21600}
    def save(): (a.output/'control.json').write_text(json.dumps(record,indent=2)+'\n')
    def command(args,timeout=120,check=True):
        r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
        if check and r.returncode:raise RuntimeError(r.stderr[-2500:])
        return r
    def gc(args,**kw):return command(['gcloud','compute',*args,'--project='+PROJECT,'--zone='+ZONE,'--quiet'],**kw)
    def describe():return json.loads(gc(['instances','describe',VM,'--format=json']).stdout)
    def ssh(cmd,**kw):return gc(['ssh','clarirz@'+VM,'--command='+cmd],**kw)
    before=describe()
    if before['status']!='TERMINATED':raise RuntimeError('VM must be stopped; refusing to interrupt another process')
    if not before['machineType'].endswith('/e2-highmem-8'):raise RuntimeError('Unexpected machine type')
    bundle=a.output/'code.tar.gz'
    with tarfile.open(bundle,'w:gz') as t:
        for name in sorted(manifest):t.add(root/name,arcname=name)
        t.add(root/'MANIFIESTO_CODIGO.json',arcname='MANIFIESTO_CODIGO.json')
        for f in (root/'prompts').glob('*'):
            if f.is_file():t.add(f,arcname='prompts/'+f.name)
        t.add(audits[0],arcname='configuraciones/calidad_real.json')
    record['bundle_sha256']=digest(bundle);record['audit_sha256']=digest(audits[0]);save()
    gc(['instances','set-scheduling',VM,'--max-run-duration=21600s','--instance-termination-action=STOP'])
    schedule=describe()['scheduling']
    if int(schedule.get('maxRunDuration',{}).get('seconds',0))!=21600 or schedule.get('instanceTerminationAction')!='STOP':
        raise RuntimeError('Six-hour GCE STOP not verified')
    record['scheduling']=schedule
    dispatch_attempted=False;start_attempted=False
    try:
        start_attempted=True;record['start_request_epoch']=time.time();save()
        gc(['instances','start',VM],timeout=180)
        info=describe()
        start=datetime.fromisoformat(info['lastStartTimestamp'].replace('Z','+00:00')).timestamp()
        deadline=start+21000;record['deadline_epoch']=deadline;save()
        for _ in range(18):
            try:
                if ssh('true',timeout=20,check=False).returncode==0:break
            except subprocess.TimeoutExpired:pass
            time.sleep(5)
        else:raise RuntimeError('SSH unavailable')
        minutes=max(1,int((start+21540-time.time())//60))
        ssh('sudo -n true && sudo -n shutdown -h +'+str(minutes))
        # Check actual process command lines without matching this probe itself.
        probe="import os,pathlib; hits=[p.read_text().replace(chr(0),' ') for p in pathlib.Path('/proc').glob('[0-9]*/cmdline') if p.parent.name!=str(os.getpid()) and p.exists()]; hits=[s for s in hits if any(x in s for x in ['ejecutar_'+'v7.py','worker_'+'vm.py'])]; assert not hits,hits"
        ssh(shlex.join([PY,'-c',probe]))
        gc(['scp',str(bundle),'clarirz@'+VM+':/tmp/'+run+'.tar.gz'])
        ssh('mkdir -p '+shlex.quote(remote.rsplit('/',1)[0])+' && mkdir '+shlex.quote(remote)+' && tar -xzf /tmp/'+run+'.tar.gz -C '+shlex.quote(remote))
        preflight="import shutil,importlib; assert shutil.disk_usage('.').free>10*2**30; [importlib.import_module(x) for x in ['numpy','polars','lightgbm','optuna','sklearn']]"
        env=['env','POLARS_MAX_THREADS=4','PYTHONPATH='+BASE+'/v4/.auditdeps',PY]
        ssh(shlex.join(env+['-c',preflight]))
        ssh(shlex.join(env+[remote+'/scripts/preflight.py',remote+'/configuraciones/contrato_v7.json',remote+'/environment_before_launch.json']))
        gc(['scp','clarirz@'+VM+':'+remote+'/environment_before_launch.json',str(a.output/'environment_before_launch.json')])
        args=[PY,remote+'/scripts/worker_vm.py','--dataset',BASE+'/datos/analistasr_competencia_2026.csv.gz',
              '--config',remote+'/configuraciones/contrato_v7.json','--deadline',str(deadline)]
        launch='import subprocess; f=open('+repr(remote+'/worker.log')+',"a"); p=subprocess.Popen('+repr(args)+',stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True); print(p.pid)'
        dispatch_attempted=True;record['dispatch_attempted']=True;save()
        record['worker_pid']=ssh(shlex.join(env+['-c',launch])).stdout.strip();save()
        print('V7_DISPATCHED',json.dumps(record),flush=True)
        print('El supervisor continúa si se corta Cloud Shell. El límite GCE es de seis horas.',flush=True)
        last=None
        while time.time()<start+21600:
            if describe()['status']!='RUNNING':break
            status=ssh('cat '+shlex.quote(remote+'/resultados/ejecucion/status.json'),check=False,timeout=30)
            if status.returncode==0 and status.stdout!=last:
                last=status.stdout;record['training_confirmed']=json.loads(last).get('fits_started',0)>0;save();print('V7_STATUS',last.strip(),flush=True)
            ready=ssh('test -f '+shlex.quote(remote+'/resultados/private_recovery.tar.gz.json'),check=False,timeout=30)
            if ready.returncode==0:
                for name in ['aggregates.tar.gz','private_recovery.tar.gz']:
                    for suffix in ['', '.json']:
                        gc(['scp','clarirz@'+VM+':'+remote+'/resultados/'+name+suffix,str(a.output/(name+suffix))],timeout=90)
                    verify_archive(a.output/name)
                record['recovered']=True;record['private_backup_location']=str(a.output/'private_recovery.tar.gz');save()
                print('V7_RECOVERED',str(a.output),flush=True)
                break
            time.sleep(20)
    except BaseException as e:
        record['controller_error']=str(e);save()
        print('V7_CONTROLLER_ERROR',str(e),flush=True)
        # After dispatch, a transport failure is not permission to interrupt the worker.
        raise
    finally:
        if start_attempted and (not dispatch_attempted or record['recovered']):
            try:gc(['instances','stop',VM],timeout=180)
            except Exception as e:record['stop_error']=str(e)
        try:record['vm_status']=describe()['status']
        except Exception as e:record['status_error']=str(e)
        save();print('V7_CONTROL',json.dumps(record),flush=True)

if __name__=='__main__':main()
