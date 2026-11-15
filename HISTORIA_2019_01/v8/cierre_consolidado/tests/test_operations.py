import json,sys,tempfile,time,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from operacion_v8 import package,assemble,supervise
class OperationTests(unittest.TestCase):
 def test_backup_restore_and_resume(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);run=root/'run';(run/'private').mkdir(parents=True);(run/'private/model.txt').write_text('private model');(run/'status.json').write_text('{}')
   manifest=package(run,root/'backup',chunk_size=32)
   self.assertEqual(set(manifest['archives']['public.tar.gz']['members']),{'status.json'})
   self.assertEqual(set(manifest['archives']['private.tar.gz']['members']),{'private/model.txt'})
   for n in manifest['archives']:(root/'backup'/n).unlink()
   assemble(root/'backup',manifest);assemble(root/'backup',manifest)
   self.assertTrue(json.loads((root/'backup/RESTORED.json').read_text())['verified'])
   self.assertTrue((run/'private/model.txt').exists())
 def test_corrupt_chunk_blocks(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);run=root/'run';run.mkdir();(run/'x.json').write_text('{}');m=package(run,root/'backup',chunk_size=32)
   n='public.tar.gz';(root/'backup'/n).unlink();(root/'backup'/m['archives'][n]['chunks'][0]['name']).write_bytes(b'bad')
   with self.assertRaises(ValueError):assemble(root/'backup',m)
   self.assertFalse((root/'backup/RESTORED.json').exists())
 def test_independent_timeout(self):
  with tempfile.TemporaryDirectory() as d:
   r=supervise([sys.executable,'-c','import time;time.sleep(60)'],Path(d)/'log',time.time()+.15,0,2**50,poll_seconds=.02)
   self.assertEqual(r['reason'],'TIME_CAP');self.assertNotEqual(r['returncode'],0)
 def test_failed_process(self):
  with tempfile.TemporaryDirectory() as d:
   r=supervise([sys.executable,'-c','raise SystemExit(7)'],Path(d)/'log',time.time()+10,0,2**50,poll_seconds=.02)
   self.assertEqual(r['returncode'],7)
if __name__=='__main__':unittest.main()
