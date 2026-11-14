"""Detached supervisor with time/resource guards, recovery archives and OS shutdown."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tarfile
import time


def terminate(p):
    if p.poll() is not None:return
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=15)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()


def archive_outputs(out):
    for private in [False,True]:
        target=out.parent/('private_recovery.tar.gz' if private else 'aggregates.tar.gz')
        with tarfile.open(target,'w:gz') as t:
            for p in sorted(out.rglob('*')):
                if not p.is_file():continue
                relative=p.relative_to(out)
                is_private='private' in relative.parts
                if private and is_private and p.suffix in ['.txt','.npz']:
                    t.add(p,arcname=str(relative))
                elif not private and not is_private and p.suffix in ['.json','.log']:
                    t.add(p,arcname=str(relative))
        with target.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        # Test gzip/tar readability without extracting client-level contents.
        with tarfile.open(target) as t:
            names=[]
            for m in t.getmembers():
                if m.isfile():
                    fp=t.extractfile(m)
                    while fp.read(1024*1024):pass
                    names.append(m.name)
        (target.parent/(target.name+'.json')).write_text(json.dumps({'sha256':digest,'members':names,'readback_passed':True},indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dataset',required=True)
    parser.add_argument('--config',required=True);parser.add_argument('--deadline',type=float,required=True)
    a=parser.parse_args();root=Path(__file__).resolve().parents[1]
    out=root/'resultados/ejecucion';out.parent.mkdir(exist_ok=True)
    lock=open('/tmp/historia_experiment.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if out.exists():raise FileExistsError('Fresh run required')
    subprocess.run(['sudo','-n','true'],check=True)
    if not time.time()<a.deadline<=time.time()+21600:raise ValueError('Invalid cap')
    p=None;reason=None;peak=0
    try:
        cmd=[sys.executable,str(root/'scripts/ejecutar_v7.py'),'--config',a.config,'--dataset',a.dataset,
             '--output',str(out),'--deadline',str(a.deadline)]
        with (out.parent/'runner.log').open('w') as log:
            p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            while p.poll() is None:
                try:
                    lines=Path(f'/proc/{p.pid}/status').read_text().splitlines()
                    rss=int(next(x.split()[1] for x in lines if x.startswith('VmRSS:')))*1024
                except (FileNotFoundError,StopIteration):rss=0
                peak=max(peak,rss)
                if time.time()>=a.deadline:reason='TIME_CAP'
                elif rss>48*2**30:reason='MEMORY_CAP'
                elif shutil.disk_usage(root).free<10*2**30:reason='DISK_CAP'
                if reason:terminate(p);break
                time.sleep(2)
            rc=p.wait()
        out.mkdir(exist_ok=True)
        shutil.copy2(out.parent/'runner.log',out/'runner.log')
        (out/'supervisor.json').write_text(json.dumps({'returncode':rc,'reason':reason,'peak_rss_bytes':peak,
            'finished_epoch':time.time(),'complete':(out/'FINAL.json').exists()},indent=2)+'\n')
        archive_outputs(out)
    except Exception as e:
        if p is not None:terminate(p)
        (out.parent/'worker_error.json').write_text(json.dumps({'error':str(e)}))
        raise
    finally:
        # Applies on success, timeout and failure; not dependent on Cloud Shell.
        (out.parent/'shutdown_pending.json').write_text(json.dumps({'shutdown_epoch':time.time()+480}))
        time.sleep(480)
        subprocess.run(['sudo','-n','shutdown','-h','now'],check=True)

if __name__=='__main__':main()
