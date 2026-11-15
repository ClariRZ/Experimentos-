"""Recover an existing stopped v8 run. Never invokes training or evaluation."""
import argparse,json,re,shlex,tarfile,time
from pathlib import Path
from control_v8 import Cloud,wait_ssh,recover
from ejecutar_v8 import save
from operacion_v8 import VM,BASE

def restore(folder,cloud=None):
    folder=Path(folder);record=json.loads((folder/'control.json').read_text());cloud=cloud or Cloud()
    remote=record['remote']
    if not re.fullmatch(re.escape(BASE)+r'/v8/deployments/v8_\d{8}_\d{6}_[a-f0-9]{6}',remote):raise ValueError('Unexpected recovery path')
    if cloud.describe()['status']!='TERMINATED':raise RuntimeError('VM is not stopped; refusing to interrupt another task')
    report={'remote':remote,'new_training_allowed':False,'started_epoch':time.time(),'recovered':False}
    started=False
    try:
        cloud.run(['instances','set-scheduling',VM,'--max-run-duration=3600s','--instance-termination-action=STOP'])
        schedule=cloud.describe()['scheduling']
        if int(schedule['maxRunDuration']['seconds'])!=3600 or schedule['instanceTerminationAction']!='STOP':raise ValueError('Recovery stop limit not verified')
        started=True
        cloud.run(['instances','start',VM]);wait_ssh(cloud)
        probe="""import json
from pathlib import Path
p=Path(REMOTE)
r={'checkpoints_completed':len(list((p/'run/private/checkpoints').glob('*/record.json'))),'files':{}}
for name in ['run/status.json','run/FINAL.json','run/supervisor.json','worker_final.json']:
 f=p/name
 if f.exists():r['files'][name]=json.loads(f.read_text())
for f in (p/'run').glob('failure_*.json'):r['files'][str(f.relative_to(p))]=json.loads(f.read_text())
r['backup_manifest_exists']=(p/'backup/manifest.json').is_file()
print(json.dumps(r))
""".replace('REMOTE',repr(remote))
        observed=json.loads(cloud.ssh(shlex.join(['python3','-c',probe])).stdout)
        report['observed']=observed;save(folder/'recovery_inspection.json',report)
        print('ESTADO_EXPERIMENTO',json.dumps(observed,ensure_ascii=False),flush=True)
        if not observed['backup_manifest_exists']:raise RuntimeError('No complete backup manifest. Inspection saved; original results retained. No training restarted.')
        recover(cloud,record,folder);report['recovered']=True
        with tarfile.open(folder/'recovery/public.tar.gz','r:gz') as archive:
            for name in ['FINAL.json','status.json','supervisor.json']:
                try:f=archive.extractfile(name)
                except KeyError:continue
                print('RESPALDO_VERIFICADO',name,f.read().decode(),flush=True)
        print('RESPALDO_LOCAL',str(folder/'recovery'),flush=True)
    finally:
        if started:cloud.run(['instances','stop',VM],check=False)
        report['vm_status']=cloud.describe()['status'];save(folder/'recovery_inspection.json',report)
        record['vm_status']=report['vm_status'];save(folder/'control.json',record)
        print('ESTADO_FINAL_VM',report['vm_status'],flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--control-dir',type=Path,required=True);a=p.parse_args();restore(a.control_dir)
if __name__=='__main__':main()
