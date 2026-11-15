import copy,json,shutil,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from control_v8 import recover,launch
from operacion_v8 import package,validate_manifest

class FakeCloud:
 def __init__(self,remote):self.remote=remote;self.downloads=[];self.fail=True
 def scp(self,source,dest):
  if str(source).startswith('clarirz@'):
   name=str(source).split('/')[-1]
   if name=='private.part00001' and self.fail:
    self.fail=False;raise ConnectionError('simulated disconnection')
   shutil.copyfile(self.remote/name,dest);self.downloads.append(name)
  else:shutil.copyfile(source,self.remote/'receipt.json')

class ControllerTests(unittest.TestCase):
 def test_interrupted_recovery_reuses_verified_chunks(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);run=root/'run';(run/'private').mkdir(parents=True)
   (run/'private/model.txt').write_text('model data'*100);(run/'status.json').write_text('{}')
   package(run,root/'remote',chunk_size=32);folder=root/'local';folder.mkdir()
   cloud=FakeCloud(root/'remote');record={'remote':'/remote','recovered':False}
   with self.assertRaises(ConnectionError):recover(cloud,record,folder)
   self.assertFalse(record['recovered']);self.assertFalse((root/'remote/receipt.json').exists())
   recover(cloud,record,folder)
   self.assertTrue(record['recovered']);self.assertEqual(cloud.downloads.count('private.part00000'),1)
   self.assertTrue(json.loads((root/'remote/receipt.json').read_text())['verified'])
 def test_reject_path_escape(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);run=root/'run';run.mkdir();m=package(run,root/'backup')
   for kind in ['archive','chunk','member']:
    bad=copy.deepcopy(m)
    if kind=='archive':bad['archives']['../escape']=bad['archives'].pop('public.tar.gz')
    elif kind=='chunk':bad['archives']['public.tar.gz']['chunks'][0]['name']='../escape'
    else:bad['archives']['public.tar.gz']['members']['../escape']={'bytes':0,'sha256':'0'*64}
    with self.assertRaises(ValueError):validate_manifest(bad)
 def test_draft_blocks_before_cloud_calls(self):
  root=Path(__file__).resolve().parents[1]
  class NoCloud:
   def describe(self):raise AssertionError('Cloud must not be contacted')
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):launch(root,root/'contrato_v8_consolidado.json',Path(d)/'launch',NoCloud())
if __name__=='__main__':unittest.main()
