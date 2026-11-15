import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('cleanup', Path(__file__).resolve().parents[1] / 'limpiar_partes_v8.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class CleanupTests(unittest.TestCase):
    def fixture(self, root):
        manifest = {'archives': {}}
        for label in ['public', 'private']:
            data = (label * 10).encode()
            h = hashlib.sha256(data).hexdigest()
            (root / (label+'.tar.gz')).write_bytes(data)
            (root / (label+'.part00000')).write_bytes(data)
            manifest['archives'][label+'.tar.gz'] = {'bytes': len(data), 'sha256': h,
                'chunks': [{'name': label+'.part00000', 'bytes': len(data), 'sha256': h}]}
        (root/'manifest.json').write_text(json.dumps(manifest))
        (root/'model.txt').write_text('keep this model')
        return m.sha(root/'manifest.json')

    def test_cleanup_preserves_originals_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);h=self.fixture(root)
            r=m.clean(root,h,True,root/'report.json')
            self.assertEqual(r['candidate_count'],2)
            self.assertTrue((root/'model.txt').exists())
            self.assertTrue((root/'private.tar.gz').exists())
            self.assertTrue((root/'public.tar.gz').exists())
            self.assertEqual(m.clean(root,h,True,root/'report2.json')['candidate_count'],0)

    def test_corrupt_archive_blocks_all_deletion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);h=self.fixture(root)
            (root/'private.tar.gz').write_bytes(b'corrupt')
            with self.assertRaises(ValueError):m.clean(root,h,True,root/'report.json')
            self.assertEqual(len(list(root.glob('*.part*'))),2)

    def test_symlink_blocks_deletion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);h=self.fixture(root)
            p=root/'private.part00000';p.unlink();p.symlink_to(root/'private.tar.gz')
            with self.assertRaises(ValueError):m.clean(root,h,True,root/'report.json')
            self.assertTrue((root/'public.part00000').exists())

    def test_dry_run_keeps_chunks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);h=self.fixture(root)
            m.clean(root,h,False,root/'report.json')
            self.assertEqual(len(list(root.glob('*.part*'))),2)

if __name__=='__main__':unittest.main()
