import io
import json
import hashlib
import tempfile
import tarfile
from pathlib import Path
import unittest
from unittest.mock import patch
import respaldar_limpiar_v1_v6 as m

class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def archive(self, entries):
        p=self.root/'test.tar.gz'
        with tarfile.open(p,'w:gz') as t:
            for name,content in entries:
                item=tarfile.TarInfo(name);item.size=len(content);t.addfile(item,io.BytesIO(content))
        return p
    def inventory(self):
        return {'members':{'model.txt':{'bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()}}}
    def test_valid_archive(self):
        m.validate_archive(self.archive([('model.txt',b'abc')]),self.inventory())
    def test_corrupt_content(self):
        with self.assertRaises(ValueError):m.validate_archive(self.archive([('model.txt',b'xyz')]),self.inventory())
    def test_missing_member(self):
        with self.assertRaises(ValueError):m.validate_archive(self.archive([]),self.inventory())
    def test_extra_member(self):
        with self.assertRaises(ValueError):m.validate_archive(self.archive([('model.txt',b'abc'),('extra',b'x')]),self.inventory())
    def test_duplicate_member(self):
        with self.assertRaises(ValueError):m.validate_archive(self.archive([('model.txt',b'abc'),('model.txt',b'abc')]),self.inventory())
    def test_required_hash_blocks_candidates(self):
        p=self.root/'model';p.write_bytes(b'abc')
        with patch.object(m,'BASE',self.root):
            with self.assertRaises(ValueError):m.candidates({'required':{'model':'wrong'},'matrices':{},'arms':[]})
        self.assertTrue(p.exists())
    def test_only_named_matrices_are_candidates(self):
        (self.root/'model').write_bytes(b'abc');(self.root/'matrix').write_bytes(b'derived');(self.root/'other').write_bytes(b'preserve')
        expected={'required':{'model':m.sha(self.root/'model')},'matrices':{'matrix':m.sha(self.root/'matrix')},'arms':[]}
        with patch.object(m,'BASE',self.root):self.assertEqual(set(m.candidates(expected)),{'matrix'})

if __name__=='__main__':unittest.main()
