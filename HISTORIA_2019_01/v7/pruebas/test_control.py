import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from control_entrenamiento import validate_audit,verify_archive,digest,validate_launch_gate,main
from unittest.mock import patch

class ControllerTests(unittest.TestCase):
    def test_unresolved_gate_blocks(self):
        for cfg in [{}, {'training_authorized':True,'real_audit_approved':False,'sanitation_review':{'resolved':True}}, {'training_authorized':True,'real_audit_approved':True,'sanitation_review':{'resolved':False}}]:
            with self.assertRaisesRegex(ValueError,'V7 BLOCKED'):validate_launch_gate(cfg)
        validate_launch_gate({'training_authorized':True,'real_audit_approved':True,'sanitation_review':{'resolved':True}})

    def test_blocked_main_never_calls_cloud(self):
        cfg={'training_authorized':True,'real_audit_approved':False,'sanitation_review':{'resolved':False}}
        with patch.object(sys,'argv',['controller','--output','/tmp/unused_v7_block_test']), patch('control_entrenamiento.Path.read_text',return_value=json.dumps(cfg)), patch('control_entrenamiento.subprocess.run') as cloud:
            with self.assertRaisesRegex(ValueError,'V7 BLOCKED'):main()
            cloud.assert_not_called()

    def fixture(self,path):
        rows=[dict(month=m,variable='x'+str(i),rows=10,zeros=0,nulls=0,nonfinite=0,distinct_finite=5,minimum=1,maximum=5)
              for m in range(201901,201911) for i in range(152)]
        for x in rows:
            if (x['month'],x['variable']) in [(201907,'x0'),(201910,'x1')]:
                x.update(zeros=10,distinct_finite=1,minimum=0,maximum=0)
        a=dict(dataset_sha256='dataset',october_labels_accessed=False,training_executed=False,raw_columns=list(range(152)),variable_month_statistics=rows)
        path.write_text(json.dumps(a))
        return dict(real_audit_sha256=digest(path),data=dict(sha256='dataset',broken_masks={'201907':['x0'],'201910':['x1']}))
    def test_gate_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'audit.json';cfg=self.fixture(p);validate_audit(p,cfg)
            p.write_text(p.read_text()+' ')
            with self.assertRaises(ValueError):validate_audit(p,cfg)
    def test_gate_rejects_unconfirmed_july(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'audit.json';cfg=self.fixture(p);a=json.loads(p.read_text())
            next(x for x in a['variable_month_statistics'] if x['month']==201907 and x['variable']=='x0')['zeros']=9
            p.write_text(json.dumps(a));cfg['real_audit_sha256']=digest(p)
            with self.assertRaises(ValueError):validate_audit(p,cfg)
    def test_reviewed_july_is_preserved_and_verified(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'audit.json';cfg=self.fixture(p)
            a=json.loads(p.read_text())
            x=next(x for x in a['variable_month_statistics'] if x['month']==201907 and x['variable']=='x0')
            x.update(rows=129957,nulls=4973,zeros=86019,distinct_finite=78,minimum=0,maximum=4466)
            p.write_text(json.dumps(a));cfg['real_audit_sha256']=digest(p)
            cfg['data']['broken_masks'].pop('201907')
            cfg['sanitation_review']={'july_expected_statistics':[dict(x)]}
            validate_audit(p,cfg)
            cfg['sanitation_review']['july_expected_statistics'][0]['zeros']+=1
            with self.assertRaises(ValueError):validate_audit(p,cfg)
    def test_recovery_verifies_hash_and_safe_paths(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'archive.tar.gz'
            for name in ['private/model.txt','../unsafe']:
                with tarfile.open(p,'w:gz') as t:
                    info=tarfile.TarInfo(name);info.size=2;t.addfile(info,io.BytesIO(b'ok'))
                Path(str(p)+'.json').write_text(json.dumps({'sha256':digest(p)}))
                if name.startswith('..'):
                    with self.assertRaises(ValueError):verify_archive(p)
                else:verify_archive(p)
if __name__=='__main__':unittest.main()
