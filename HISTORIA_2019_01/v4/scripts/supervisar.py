"""Watchdog independiente: limita tiempo, RAM y disco; exporta solo agregados."""
import argparse,json,os,signal,subprocess,sys,tarfile,time,shutil
from pathlib import Path

def supervise(cmd, deadline, output, memory_limit=48*2**30, min_disk=10*2**30):
 output.parent.mkdir(parents=True,exist_ok=True)
 log=output.parent/(output.name+'.log');peak=0;reason=None
 with log.open('w') as f:
  p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  while p.poll() is None:
   try:
    vals=Path(f'/proc/{p.pid}/status').read_text().splitlines()
    rss=int(next(x.split()[1] for x in vals if x.startswith('VmRSS:')))*1024
   except (FileNotFoundError,StopIteration):rss=0
   peak=max(peak,rss)
   if time.time()>=deadline:reason='TIME_CAP'
   elif rss>memory_limit:reason='MEMORY_CAP'
   elif shutil.disk_usage(output.parent).free<min_disk:reason='DISK_CAP'
   if reason:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    break
   time.sleep(1)
  rc=p.wait()
 record={'returncode':rc,'reason':reason,'peak_rss_bytes':peak,'finished_epoch':time.time(),'october_used':False}
 output.mkdir(exist_ok=True)
 (output/'supervisor.json').write_text(json.dumps(record,indent=2))
 archive=output.parent/(output.name+'_agregados.tar.gz')
 with tarfile.open(archive,'w:gz') as t:
  for path in output.rglob('*.json'):
   if 'private' not in path.relative_to(output).parts:t.add(path,arcname=str(Path(output.name)/path.relative_to(output)))
  t.add(log,arcname=output.name+'/ejecucion.log')
 return record

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--deadline',type=float,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('cmd',nargs=argparse.REMAINDER);a=p.parse_args()
 print(supervise(a.cmd,a.deadline,a.output),flush=True)
