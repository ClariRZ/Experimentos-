"""Detached VM worker; archive before shutdown, independent of Cloud Shell lifetime."""
import argparse,fcntl,json,os,subprocess,sys,time
from pathlib import Path
from supervisar import supervise

def main():
 p=argparse.ArgumentParser();p.add_argument('--deadline',type=float,required=True);p.add_argument('--dataset',required=True);a=p.parse_args()
 root=Path(__file__).resolve().parents[1];out=root/'resultados/entrenamiento'
 lock=open('/tmp/historia_v6.lock','w')
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 # Permission to stop must be available before any fitting, not discovered at the end.
 subprocess.run(['sudo','-n','true'],check=True)
 try:
  cmd=[sys.executable,str(root/'scripts/ejecutar_etapa1.py'),'--config',str(root/'configuraciones/contrato_v6.json'),'--dataset',a.dataset,'--output',str(out),'--deadline',str(a.deadline)]
  result=supervise(cmd,a.deadline,out)
 finally:
  # Recovery grace period lets Cloud Shell collect the archive; disk is persistent.
  (root/'resultados/shutdown_pending.json').write_text(json.dumps({'scheduled_at':time.time()+180,'reason':'worker_finished_or_failed'}))
  time.sleep(180)
  subprocess.run(['sudo','-n','shutdown','-h','now'],check=True)
if __name__=='__main__':main()
