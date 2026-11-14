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

class PartialTransferTests(unittest.TestCase):
    def test_resume_keeps_verified_prefix_and_discards_incomplete_tail(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d); blocks=[b'abc',b'def']
            pkg={'bytes':6,'archive_sha256':hashlib.sha256(b'abcdef').hexdigest(),
                 'chunks':[{'name':f'parte_{i:04d}','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for i,b in enumerate(blocks)]}
            (dest/'respaldo.tar.gz').write_bytes(b'abcd')
            fetched=[]
            def fetch(part,local):
                fetched.append(part['name']);local.write_bytes(b'def')
            result=m.receive_parts(dest,pkg,fetch)
            self.assertEqual(result.read_bytes(),b'abcdef')
            self.assertEqual(fetched,['parte_0001'])
            self.assertFalse((dest/'parte_0001').exists())
    def test_bad_existing_prefix_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d);p=dest/'respaldo.tar.gz';p.write_bytes(b'xyz')
            pkg={'bytes':3,'chunks':[{'name':'parte_0000','bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()}]}
            with self.assertRaises(ValueError):m.prefix_state(dest,pkg)
            self.assertEqual(p.read_bytes(),b'xyz')
