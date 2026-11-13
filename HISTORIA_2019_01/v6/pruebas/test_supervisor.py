import sys,time,json
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from supervisar import supervise

def test_timeout_stops_worker_and_keeps_record(tmp_path):
 out=tmp_path/'timeout'
 r=supervise([sys.executable,'-c','import time;time.sleep(60)'],time.time()+.2,out,min_disk=0)
 assert r['reason']=='TIME_CAP' and r['returncode']!=0
 assert (out/'supervisor.json').exists()
 assert (tmp_path/'timeout_agregados.tar.gz').exists()

def test_success_and_failure_preserve_returncode(tmp_path):
 for code in [0,3]:
  r=supervise([sys.executable,'-c',f'raise SystemExit({code})'],time.time()+10,tmp_path/str(code),min_disk=0)
  assert r['returncode']==code and r['reason'] is None

def test_existing_run_cannot_be_overwritten(tmp_path):
 with pytest.raises(FileExistsError):supervise(['unused'],time.time()+10,tmp_path)
