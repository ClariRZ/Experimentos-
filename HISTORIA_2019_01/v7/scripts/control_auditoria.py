"""Cloud Shell controller: bounded read-only audit and unconditional VM stop.

Run from a pinned checkout. Never trains and never deletes VM disks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import time

PROJECT='proj-uba-261002122233861'
ZONE='northamerica-northeast2-b'
VM='clari-c1-fundados'
BASE='/home/clarirz/HISTORIA_2019_01'
PY=BASE+'/historia_2019_v1/.venv/bin/python'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    a.output.mkdir(parents=True,exist_ok=False)
    run='v7_audit_'+time.strftime('%Y%m%d_%H%M%S',time.gmtime())
    remote=BASE+'/v7/auditorias/'+run
    record={'run':run,'training_executed':False,'hard_stop_seconds':2700,'remote':remote}
    def save():
        (a.output/'control.json').write_text(json.dumps(record,indent=2)+'\n')
    def command(args,timeout=120,check=True):
        r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
        if check and r.returncode:
            raise RuntimeError(r.stderr[-2500:])
        return r
    def gc(args,**kw):
        return command(['gcloud','compute',*args,'--project='+PROJECT,'--zone='+ZONE,'--quiet'],**kw)
    def describe():
        return json.loads(gc(['instances','describe',VM,'--format=json']).stdout)
    def ssh(cmd,**kw):
        return gc(['ssh','clarirz@'+VM,'--command='+cmd],**kw)
    before=describe()
    if before['status']!='TERMINATED':
        raise RuntimeError('Refusing to interfere with a running VM')
    record['machine_type']=before['machineType']
    gc(['instances','set-scheduling',VM,'--max-run-duration=2700s','--instance-termination-action=STOP'])
    sched=describe()['scheduling']
    if int(sched.get('maxRunDuration',{}).get('seconds',0))!=2700 or sched.get('instanceTerminationAction')!='STOP':
        raise RuntimeError('GCE STOP cap not verified')
    record['scheduling']=sched
    bundle=a.output/'audit_code.tar.gz'
    with tarfile.open(bundle,'w:gz') as t:
        for rel in ['scripts/auditar_datos.py','configuraciones/contrato_v7_propuesto.json']:
            t.add(root/rel,arcname=rel)
    record['bundle_sha256']=hashlib.sha256(bundle.read_bytes()).hexdigest()
    record['started_at']=time.time();save()
    try:
        gc(['instances','start',VM],timeout=180)
        for attempt in range(12):
            try:
                if ssh('true',timeout=30,check=False).returncode==0:break
            except subprocess.TimeoutExpired:pass
            time.sleep(5)
        else:raise RuntimeError('SSH unavailable')
        # Defense in depth: OS shutdown also remains if Cloud Shell disconnects.
        ssh('sudo -n shutdown -h +40',timeout=30)
        gc(['scp',str(bundle),'clarirz@'+VM+':/tmp/'+run+'.tar.gz'])
        ssh('mkdir -p '+shlex.quote(remote)+' && tar -xzf /tmp/'+run+'.tar.gz -C '+shlex.quote(remote))
        cmd=['env','POLARS_MAX_THREADS=4','PYTHONPATH='+BASE+'/v4/.auditdeps',PY,
             remote+'/scripts/auditar_datos.py','--config',remote+'/configuraciones/contrato_v7_propuesto.json',
             '--dataset',BASE+'/datos/analistasr_competencia_2026.csv.gz','--output',remote+'/resultado']
        r=ssh(shlex.join(cmd),timeout=1800,check=False)
        record['returncode']=r.returncode
        (a.output/'audit.log').write_text(r.stdout+'\n'+r.stderr)
        if r.returncode:raise RuntimeError('Remote audit failed; inspect audit.log')
        gc(['scp','clarirz@'+VM+':'+remote+'/resultado/calidad.json',str(a.output/'calidad.json')])
        report=json.loads((a.output/'calidad.json').read_text())
        record['report_sha256']=hashlib.sha256((a.output/'calidad.json').read_bytes()).hexdigest()
        summary={'dataset_sha256':report['dataset_sha256'],'monthly_rows':report['monthly_rows'],
                 'suspected_breaks':report['suspected_breaks']}
        (a.output/'resumen.json').write_text(json.dumps(summary,indent=2)+'\n')
        print('AUDIT_SUMMARY',json.dumps(summary),flush=True)
    except Exception as e:
        record['error']=str(e)
        print('AUDIT_ERROR',str(e),flush=True)
    finally:
        try:gc(['instances','stop',VM],timeout=180)
        except Exception as e:record['stop_error']=str(e)
        record['vm_status']=describe()['status']
        record['finished_at']=time.time();save()
        print('AUDIT_CONTROL',json.dumps(record),flush=True)
    if record.get('error') or record['vm_status']!='TERMINATED':raise SystemExit(1)

if __name__=='__main__':main()
