"""Remove only verified transfer chunks; retain complete archives and run artifacts."""
import argparse
import fcntl
import hashlib
import json
import shlex
import shutil
import subprocess
import time
from pathlib import Path

PROJECT = 'proj-uba-261002122233861'
ZONE = 'northamerica-northeast2-b'
VM = 'clari-c1-fundados'
RUN = Path('/home/clarirz/HISTORIA_2019_01/v8/deployments/v8_20261115_021908_c48e9d')
MANIFEST_HASH = '37c754790bd19270c4385f406a5378cc8cc7a6ed1d9d115c165ce4f37d8c45a1'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()

def plain(path):
    if path.resolve() != path.absolute() or not path.is_file():
        raise ValueError('Missing file or symlink: ' + str(path))

def plan(backup, manifest_hash):
    plain(backup / 'manifest.json')
    if sha(backup / 'manifest.json') != manifest_hash:
        raise ValueError('Unexpected manifest; nothing deleted')
    m = json.loads((backup / 'manifest.json').read_text())
    if set(m['archives']) != {'public.tar.gz', 'private.tar.gz'}:
        raise ValueError('Unexpected archives')
    candidates = []
    for name, spec in m['archives'].items():
        archive = backup / name
        plain(archive)
        if archive.stat().st_size != spec['bytes'] or sha(archive) != spec['sha256']:
            raise ValueError('Full archive not intact: ' + name)
        for chunk in spec['chunks']:
            name = chunk['name']
            if Path(name).name != name or not name.startswith(('public.part', 'private.part')):
                raise ValueError('Unexpected chunk name')
            p = backup / name
            if not p.exists() and not p.is_symlink():
                continue  # Already cleaned: idempotent.
            plain(p)
            if p.stat().st_size != chunk['bytes'] or sha(p) != chunk['sha256']:
                raise ValueError('Chunk mismatch; nothing deleted: ' + name)
            candidates.append((p, chunk))
    if len({p for p, _ in candidates}) != len(candidates):
        raise ValueError('Duplicate candidates')
    return candidates

def clean(backup, manifest_hash, apply, report):
    candidates = plan(backup, manifest_hash)
    result = {'applied': apply, 'candidate_count': len(candidates),
              'candidate_bytes': sum(c['bytes'] for _, c in candidates),
              'preserved': ['full archives', 'all models', 'all predictions', 'all run files'],
              'free_before': shutil.disk_usage(backup).free, 'deleted': [], 'complete': False}
    report.write_text(json.dumps(result, indent=2) + '\n')
    if apply:
        for p, c in candidates:
            plain(p)
            if sha(p) != c['sha256']:
                raise ValueError('Chunk changed during cleanup')
            p.unlink()
            result['deleted'].append(p.name)
            report.write_text(json.dumps(result, indent=2) + '\n')
    result.update(complete=True, free_after=shutil.disk_usage(backup).free)
    report.write_text(json.dumps(result, indent=2) + '\n')
    return result

def remote(apply):
    locks = []
    for path in [Path('/tmp/historia_experiment.lock'), RUN / 'run/run.lock']:
        if path.is_symlink():
            raise ValueError('Unexpected lock symlink')
        f = path.open('a')
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(f)
    final = json.loads((RUN / 'run/FINAL.json').read_text())
    if final.get('fits_completed') != 144 or not final.get('economic_evaluation_complete'):
        raise ValueError('Run not complete')
    report = RUN / ('limpieza_partes_' + str(time.time_ns()) + '.json')
    print(json.dumps(clean(RUN / 'backup', MANIFEST_HASH, apply, report)), flush=True)

def gc(args, timeout=180):
    return subprocess.run(['gcloud', 'compute', *args, '--project='+PROJECT,
                           '--zone='+ZONE, '--quiet'], check=True, text=True,
                          capture_output=True, timeout=timeout)

def controller(apply):
    # Verify the external backup in Cloud Shell BEFORE starting the VM.
    recovery = Path.home() / 'v8_lanzamiento_20261115_021905/recovery'
    plain(recovery / 'manifest.json')
    if sha(recovery / 'manifest.json') != MANIFEST_HASH:
        raise ValueError('Cloud Shell manifest mismatch')
    manifest = json.loads((recovery / 'manifest.json').read_text())
    receipt = json.loads((recovery / 'RESTORED.json').read_text())
    if receipt.get('verified') is not True:
        raise ValueError('Recovery not verified')
    for name, spec in manifest['archives'].items():
        p = recovery / name
        plain(p)
        if sha(p) != spec['sha256'] or p.stat().st_size != spec['bytes'] or receipt['archive_hashes'][name] != spec['sha256']:
            raise ValueError('External backup mismatch: ' + name)
    state = gc(['instances', 'describe', VM, '--format=value(status)']).stdout.strip()
    if state != 'TERMINATED':
        raise RuntimeError('VM active; not interrupting it')
    gc(['instances', 'set-scheduling', VM, '--max-run-duration=1200s', '--instance-termination-action=STOP'])
    scheduling = json.loads(gc(['instances', 'describe', VM, '--format=json']).stdout)['scheduling']
    if int(scheduling['maxRunDuration']['seconds']) != 1200 or scheduling['instanceTerminationAction'] != 'STOP':
        raise RuntimeError('Automatic stop not verified')
    try:
        gc(['instances', 'start', VM])
        for attempt in range(12):
            try:
                gc(['ssh', 'clarirz@'+VM, '--command=true'], timeout=30)
                break
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                if attempt == 11:
                    raise
                time.sleep(5)
        script = Path(__file__).read_text()
        command = 'python3 - --remote' + (' --apply' if apply else '') + " <<'V8_CLEANUP_SCRIPT'\n" + script + '\nV8_CLEANUP_SCRIPT'
        result = gc(['ssh', 'clarirz@'+VM, '--command='+command], timeout=600)
        dest = Path.home() / ('v8_limpieza_partes_' + str(time.time_ns()) + '.json')
        dest.write_text(result.stdout)
        print(result.stdout)
        print('INFORME:', dest, flush=True)
    finally:
        gc(['instances', 'stop', VM], timeout=300)
        print('ESTADO_FINAL_VM:', gc(['instances', 'describe', VM, '--format=value(status)']).stdout.strip(), flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--remote', action='store_true')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    (remote if args.remote else controller)(args.apply)
