import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('cleanup', Path(__file__).with_name('limpiar_matrices_v7.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_wrong_hash_never_deletes(self):
        p = self.root / 'matrix'; p.write_bytes(b'original')
        with self.assertRaises(ValueError):
            m.remove_one(p, '0' * 64, self.root / 'log', True)
        self.assertEqual(p.read_bytes(), b'original')

    def test_dry_run_keeps_file(self):
        p = self.root / 'matrix'; p.write_bytes(b'original')
        m.remove_one(p, m.sha(p), self.root / 'log')
        self.assertTrue(p.exists())

    def test_symlink_rejected(self):
        p = self.root / 'original'; p.write_bytes(b'original')
        link = self.root / 'link'; link.symlink_to(p)
        with self.assertRaises(ValueError):
            m.remove_one(link, m.sha(p), self.root / 'log', True)
        self.assertTrue(p.exists())

    def test_parent_symlink_rejected(self):
        d = self.root / 'real'; d.mkdir(); (d / 'matrix').write_bytes(b'a')
        link = self.root / 'linked'; link.symlink_to(d)
        with self.assertRaises(ValueError):
            m.regular(link / 'matrix')

    def test_delete_is_journaled(self):
        p = self.root / 'matrix'; p.write_bytes(b'original')
        m.remove_one(p, m.sha(p), self.root / 'log', True)
        self.assertFalse(p.exists())
        rows = [json.loads(x) for x in (self.root / 'log').read_text().splitlines()]
        self.assertEqual([r['action'] for r in rows], ['planned', 'deleted'])
        self.assertEqual(rows[0]['sha256'], hashlib.sha256(b'original').hexdigest())

    def fixture(self):
        base = self.root / 'HISTORIA'; source = base / 'v7/source'; octo = base / 'v7/october'
        source.mkdir(parents=True); octo.mkdir(); (base / 'datos').mkdir()
        dataset = base / 'datos/analistasr_competencia_2026.csv.gz'; dataset.write_bytes(b'data')
        def save(p, obj): p.write_text(json.dumps(obj))
        (source / 'private/B0').mkdir(parents=True)
        model = source / 'private/B0/seed.txt'; model.write_bytes(b'model')
        matrix = source / 'private/B0.parquet'; matrix.write_bytes(b'PAR1matrix')
        (source / 'private/october').mkdir()
        partial = source / 'private/october/B0.parquet'; partial.write_bytes(b'PAR1derived')
        unknown = source / 'private/october/unknown.parquet'; unknown.write_bytes(b'preserve')
        save(source / 'config_frozen.json', {'data': {'sha256': m.sha(dataset)}})
        save(source / 'policy_frozen.json', {'models': {'B0': {'1': {'seed.txt': m.sha(model)}}}})
        save(source / 'feature_manifest.json', {'B0': {'matrix_sha256': m.sha(matrix)}})
        save(octo / 'private_manifest.json', {})
        save(octo / 'FINAL.json', {'status': 'COMPLETE_EXPLORATORY', 'new_fits': 0})
        ev = {'source': {p.name: m.sha(p) for p in source.glob('*.json')},
              'october': {p.name: m.sha(p) for p in octo.glob('*.json')}, 'code': {}}
        ep = self.root / 'evidence.json'; save(ep, ev)
        return base, source, octo, ep, model, matrix, partial, unknown

    def test_remote_scope_preserves_models_and_unknown_files(self):
        base, source, octo, ep, model, matrix, partial, unknown = self.fixture()
        with patch.multiple(m, BASE=base, SOURCE=source, OCTOBER=octo, ARMS=('B0',)), patch.object(m, 'active_training'), contextlib.redirect_stdout(io.StringIO()):
            m.remote(ep, True)
        self.assertFalse(matrix.exists()); self.assertFalse(partial.exists())
        self.assertEqual(model.read_bytes(), b'model'); self.assertTrue(unknown.exists())
        self.assertTrue((self.root / 'inventario_historia.json').exists())

    def test_corrupt_model_blocks_all_cleanup(self):
        base, source, octo, ep, model, matrix, partial, unknown = self.fixture()
        model.write_bytes(b'corrupt')
        with patch.multiple(m, BASE=base, SOURCE=source, OCTOBER=octo, ARMS=('B0',)), patch.object(m, 'active_training'):
            with self.assertRaises(ValueError): m.remote(ep, True)
        self.assertTrue(matrix.exists()); self.assertTrue(partial.exists())

    def test_active_training_blocks_all_cleanup(self):
        base, source, octo, ep, model, matrix, partial, unknown = self.fixture()
        with patch.multiple(m, BASE=base, SOURCE=source, OCTOBER=octo, ARMS=('B0',)), patch.object(m, 'active_training', side_effect=RuntimeError('active')):
            with self.assertRaises(RuntimeError): m.remote(ep, True)
        self.assertTrue(matrix.exists()); self.assertTrue(partial.exists())


if __name__ == '__main__': unittest.main()
