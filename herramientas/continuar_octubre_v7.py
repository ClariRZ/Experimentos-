"""Cloud Shell controller and detached VM supervisor for inference-only continuation."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import time

PROJECT='proj-uba-261002122233861'
ZONE='northamerica-northeast2-b'
VM='clari-c1-fundados'
BASE='/home/clarirz/HISTORIA_2019_01'
SOURCE=BASE+'/v7/deployments/v7_20261114_120354/resultados/ejecucion'
PYTHON=BASE+'/historia_2019_v1/.venv/bin/python'


def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(8*1024**2),b''):h.update(block)
    return h.hexdigest()


def verify(folder,name):
    p=folder/name;meta=json.loads((folder/(name+'.json')).read_text())
    assert digest(p)==meta['sha256'],'Archive hash mismatch'
    with tarfile.open(p) as t:
        for m in t.getmembers():
            if m.isfile():
                f=t.extractfile(m)
                while f.read(1024**2):pass


def worker(root,deadline):
    lock=open('/tmp/historia_experiment.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    out=root/'resultados/ejecucion';out.parent.mkdir()
    env=os.environ.copy();env['POLARS_MAX_THREADS']='4';env['PYTHONPATH']=BASE+'/v4/.auditdeps'
    process=None
    try:
        with (root/'runner.log').open('w') as log:
            process=subprocess.Popen([PYTHON,str(root/'evaluar_octubre_v7.py'),'--source',SOURCE,
                '--output',str(out),'--dataset',BASE+'/datos/analistasr_competencia_2026.csv.gz',
                '--deadline',str(deadline),'--clean-training-matrices'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            reason=None
            while process.poll() is None:
                if time.time()>deadline:
                    reason='TIME_CAP';os.killpg(process.pid,signal.SIGTERM)
                    try:process.wait(timeout=15)
                    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL)
                    break
                time.sleep(2)
            rc=process.wait()
        out.mkdir(exist_ok=True)
        import shutil
        shutil.copy2(root/'runner.log',out/'runner.log')
        (out/'supervisor.json').write_text(json.dumps({'returncode':rc,'reason':reason,
            'complete':(out/'FINAL.json').exists(),'finished_epoch':time.time()}))
        original=Path(SOURCE).parents[1]/'scripts/worker_vm.py'
        spec=importlib.util.spec_from_file_location('archive_worker',original)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.archive_outputs(out)
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid,signal.SIGTERM)
        grace=480 if (out.parent/'private_recovery.tar.gz.json').exists() else 0
        if grace:time.sleep(grace)
        subprocess.run(['sudo','-n','shutdown','-h','now'],check=True)


def wait_for_ssh(ssh, attempts=8):
    last_error=''
    for attempt in range(1, attempts+1):
        try:
            result=ssh('true',check=False,timeout=45)
            if result.returncode==0:return
            last_error=(result.stderr or result.stdout or 'SSH unavailable')[-2000:]
        except subprocess.TimeoutExpired:
            last_error='SSH connection attempt exceeded 45 seconds'
        print(f'ESPERANDO_CONEXION {attempt}/{attempts}: {last_error}',flush=True)
        if attempt<attempts:time.sleep(5)
    raise RuntimeError('SSH unavailable after bounded retries: '+last_error)


def controller(output):
    output.mkdir(parents=True,exist_ok=False)
    common=['--project='+PROJECT,'--zone='+ZONE,'--quiet']
    def gc(args,check=True,timeout=180):
        return subprocess.run(['gcloud','compute',*args,*common],text=True,capture_output=True,check=check,timeout=timeout)
    def ssh(cmd,**kw):return gc(['ssh','clarirz@'+VM,'--command='+cmd],**kw)
    before=json.loads(gc(['instances','describe',VM,'--format=json']).stdout)
    if before['status']!='TERMINATED':raise RuntimeError('VM must be stopped; no active run will be interrupted')
    root=BASE+'/v7/continuaciones/octubre_'+time.strftime('%Y%m%d_%H%M%S',time.gmtime())
    record={'source':SOURCE,'remote':root,'new_training_allowed':False,'recovered':False}
    def save(): (output/'control.json').write_text(json.dumps(record,indent=2))
    save();started=False;dispatched=False
    try:
        gc(['instances','set-scheduling',VM,'--max-run-duration=3600s','--instance-termination-action=STOP'])
        schedule=json.loads(gc(['instances','describe',VM,'--format=json']).stdout)['scheduling']
        assert int(schedule['maxRunDuration']['seconds'])==3600 and schedule['instanceTerminationAction']=='STOP'
        started=True;gc(['instances','start',VM]);deadline=time.time()+3000
        wait_for_ssh(ssh)
        ssh('sudo -n shutdown -h +55')
        ssh('mkdir -p '+BASE+'/v7/continuaciones && mkdir '+root)
        for name in ['continuar_octubre_v7.py','evaluar_octubre_v7.py']:
            path=Path(__file__).parent/name
            record[name+'_sha256']=digest(path)
            gc(['scp',str(path),'clarirz@'+VM+':'+root+'/'+name])
            actual=ssh('sha256sum '+root+'/'+name).stdout.split()[0]
            if actual!=record[name+'_sha256']:raise ValueError('Uploaded script hash mismatch: '+name)
        import shlex
        cmd=['python3',root+'/continuar_octubre_v7.py','--worker',root,'--deadline',str(deadline)]
        launch='import subprocess; f=open('+repr(root+'/worker.log')+',"w"); p=subprocess.Popen('+repr(cmd)+',stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True); print(p.pid)'
        dispatched=True;record['worker_pid']=ssh(shlex.join(['python3','-c',launch])).stdout.strip();save()
        print('CONTINUACION_ENVIADA',root,flush=True)
        last=None
        while time.time()<deadline+500:
            if gc(['instances','describe',VM,'--format=value(status)']).stdout.strip()!='RUNNING':break
            status=ssh('cat '+root+'/resultados/ejecucion/status.json',check=False)
            if status.returncode==0 and status.stdout!=last:
                last=status.stdout;print(last,flush=True)
            if ssh('test -f '+root+'/resultados/private_recovery.tar.gz.json',check=False).returncode==0:
                for name in ['aggregates.tar.gz','private_recovery.tar.gz']:
                    for suffix in ['', '.json']:
                        gc(['scp','clarirz@'+VM+':'+root+'/resultados/'+name+suffix,str(output/(name+suffix))])
                    verify(output,name)
                record['recovered']=True;save()
                with tarfile.open(output/'aggregates.tar.gz') as t:
                    for name in ['supervisor.json','FINAL.json']:
                        try: print(name,t.extractfile(name).read().decode(),flush=True)
                        except KeyError:pass
                print('RESPALDOS_VERIFICADOS',output,flush=True);break
            time.sleep(15)
    finally:
        if started and (not dispatched or record['recovered']):gc(['instances','stop',VM])
        record['vm_status']=gc(['instances','describe',VM,'--format=value(status)']).stdout.strip();save()
        print('CONTROL',json.dumps(record),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--worker',type=Path);p.add_argument('--deadline',type=float)
    p.add_argument('--output',type=Path);a=p.parse_args()
    if a.worker:worker(a.worker,a.deadline)
    elif a.output:controller(a.output)
    else:p.error('--output is required in Cloud Shell')
