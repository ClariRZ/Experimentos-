from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import worker_vm

class WorkerTests(unittest.TestCase):
    def test_invalid_deadline_requests_shutdown_after_owning_lock(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'scripts').mkdir()
            with patch.object(worker_vm,'__file__',str(root/'scripts/worker_vm.py')), patch.object(sys,'argv',['worker','--dataset','unused','--config','unused','--deadline','0']), patch.object(worker_vm.fcntl,'flock'), patch.object(worker_vm.subprocess,'run') as run:
                with self.assertRaisesRegex(ValueError,'Invalid cap'):worker_vm.main()
                self.assertIn((['sudo','-n','shutdown','-h','now'],),[c.args for c in run.call_args_list])
                self.assertTrue((root/'resultados/worker_error.json').exists())
    def test_lock_conflict_does_not_shutdown_another_worker(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'scripts').mkdir()
            with patch.object(worker_vm,'__file__',str(root/'scripts/worker_vm.py')), patch.object(sys,'argv',['worker','--dataset','unused','--config','unused','--deadline',str(time.time()+600)]), patch.object(worker_vm.fcntl,'flock',side_effect=BlockingIOError('busy')), patch.object(worker_vm.subprocess,'run') as run:
                with self.assertRaises(BlockingIOError):worker_vm.main()
                run.assert_not_called()
