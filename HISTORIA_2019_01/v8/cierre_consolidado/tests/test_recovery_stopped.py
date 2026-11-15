import json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import recuperar_v8 as r
class Cloud:
 def __init__(self,status='TERMINATED',manifest=False):self.status=status;self.commands=[];self.manifest=manifest
 def describe(self):return {'status':self.status,'scheduling':{'maxRunDuration':{'seconds':'3600'},'instanceTerminationAction':'STOP'}}
 def run(self,args,**kw):
  self.commands.append(args)
  if args[:2]==['instances','start']:self.status='RUNNING'
  if args[:2]==['instances','stop']:self.status='TERMINATED'
  return SimpleNamespace(returncode=0)
 def ssh(self,cmd,**kw):
  self.commands.append(cmd)
  return SimpleNamespace(returncode=0,stdout=json.dumps({'backup_manifest_exists':self.manifest,'checkpoints_completed':144}))
class RecoveryTests(unittest.TestCase):
 def setup_folder(self,d):
  p=Path(d);(p/'control.json').write_text(json.dumps({'remote':r.BASE+'/v8/deployments/v8_20261115_021908_c48e9d','recovered':False}));return p
 def test_missing_backup_stops_and_never_trains(self):
  with tempfile.TemporaryDirectory() as d:
   p=self.setup_folder(d);c=Cloud()
   with self.assertRaises(RuntimeError):r.restore(p,c)
   self.assertEqual(c.status,'TERMINATED')
   self.assertFalse(any('ejecutar_v8.py' in str(x) or 'evaluar_v8.py' in str(x) for x in c.commands))
   self.assertTrue((p/'recovery_inspection.json').exists())
 def test_running_vm_untouched(self):
  with tempfile.TemporaryDirectory() as d:
   c=Cloud('RUNNING')
   with self.assertRaises(RuntimeError):r.restore(self.setup_folder(d),c)
   self.assertEqual(c.commands,[])
 def test_failed_download_still_stops(self):
  with tempfile.TemporaryDirectory() as d:
   c=Cloud(manifest=True)
   with patch.object(r,'recover',side_effect=ConnectionError('test')):
    with self.assertRaises(ConnectionError):r.restore(self.setup_folder(d),c)
   self.assertEqual(c.status,'TERMINATED')
if __name__=='__main__':unittest.main()
