"""Verify public v8 artifacts; no data access, training or network required."""
import hashlib
import json
import tarfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
run = root / 'HISTORIA_2019_01/v8/resultados/v8_20261115_021908_c48e9d'
manifest = json.loads((run / 'respaldo/manifest.json').read_text())
spec = manifest['archives']['public.tar.gz']
archive = run / 'respaldo/public.tar.gz'
assert archive.stat().st_size == spec['bytes']
assert hashlib.sha256(archive.read_bytes()).hexdigest() == spec['sha256']
with tarfile.open(archive) as tar:
    members = tar.getmembers()
    assert len(members) == len(spec['members'])
    assert {m.name for m in members} == set(spec['members'])
    for member in members:
        assert member.isfile()
        raw = tar.extractfile(member).read()
        expected = spec['members'][member.name]
        assert len(raw) == expected['bytes']
        assert hashlib.sha256(raw).hexdigest() == expected['sha256']
        assert (run / 'originales' / member.name).read_bytes() == raw
receipt = json.loads((run / 'respaldo/RESTORED.json').read_text())
assert receipt['verified']
for name, entry in manifest['archives'].items():
    assert receipt['archive_hashes'][name] == entry['sha256']
print(json.dumps({'public_members_verified': len(members),
                  'receipt_hashes_consistent': True,
                  'private_archive_locally_verified': False,
                  'independent_model_reproduction': False}, indent=2))
