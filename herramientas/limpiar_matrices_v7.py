#!/usr/bin/env python3
"""Limpieza acotada v7. Controlador en Cloud Shell; no entrena ni borra privados únicos."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import time

PROJECT = 'proj-uba-261002122233861'
ZONE = 'northamerica-northeast2-b'
VM = 'clari-c1-fundados'
BASE = Path('/home/clarirz/HISTORIA_2019_01')
SOURCE = BASE / 'v7/deployments/v7_20261114_120354/resultados/ejecucion'
OCTOBER = BASE / 'v7/continuaciones/octubre_20261114_182415/resultados/ejecucion'
ARMS = ('B0', 'RK', 'P3', 'MIN3', 'RAN3', 'R3', 'R4', 'T4', 'H_T', 'H_S')
BACKUPS = {
    'agosto': ('v7_rescate_120354.2OVL7t/private_recovery.tar.gz', 'c7e6093d6d1228e93e666cdd269af6a432157217d68fad4108ed3d04db668d4f'),
    'octubre': ('v7_octubre_20261114_182413/private_recovery.tar.gz', 'bc98d361ecc938c5ef93025abe556f63b24f4655bbcfb872c92bbefd5a7e0cad'),
}


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


def regular(p):
    p = Path(p)
    if any(x.is_symlink() for x in [p, *p.parents]):
        raise ValueError('Enlace rechazado: ' + str(p))
    if not stat.S_ISREG(p.lstat().st_mode):
        raise ValueError('No es archivo regular: ' + str(p))
    return p


def verify(p, digest):
    if sha(regular(p)) != digest:
        raise ValueError('Hash incorrecto: ' + str(p))


def journal(path, row):
    with Path(path).open('a') as f:
        f.write(json.dumps(row, ensure_ascii=False) + '\n')
        f.flush()
        os.fsync(f.fileno())


def remove_one(p, expected, log, apply=False):
    p = regular(p)
    before = p.stat()
    verify(p, expected)
    journal(log, {'action': 'planned', 'path': str(p), 'bytes': before.st_size, 'sha256': expected})
    if apply:
        after = regular(p).stat()
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError('Archivo cambió durante la comprobación')
        p.unlink()
        journal(log, {'action': 'deleted', 'path': str(p), 'bytes': before.st_size, 'sha256': expected})
    return before.st_size


def active_training():
    found = []
    for p in Path('/proc').glob('[0-9]*'):
        try:
            if int(p.name) == os.getpid():
                continue
            exe = Path(os.readlink(p / 'exe')).name.lower()
            cmd = (p / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace').lower()
            if any(x in exe for x in ('python', 'rscript', 'lightgbm')) and any(x in cmd for x in ('worker_vm', 'ejecutar_', 'entren', 'optuna', 'train', 'evaluar_octubre')):
                found.append(int(p.name))
        except (OSError, ValueError):
            pass
    if found:
        raise RuntimeError('Procesos de trabajo activos; limpieza bloqueada: ' + str(found))


def remote(evidence_path, apply):
    ev = json.loads(Path(evidence_path).read_text())
    out = Path(evidence_path).parent
    with open('/tmp/historia_experiment.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        active_training()
        for rel, digest in ev['source'].items():
            verify(SOURCE / rel, digest)
        for rel, digest in ev['october'].items():
            verify(OCTOBER / rel, digest)
        for name, digest in ev['code'].items():
            verify(SOURCE.parents[1] / 'scripts' / name, digest)
        cfg = json.loads((SOURCE / 'config_frozen.json').read_text())
        verify(BASE / 'datos/analistasr_competencia_2026.csv.gz', cfg['data']['sha256'])
        policy = json.loads((SOURCE / 'policy_frozen.json').read_text())
        for arm, seeds in policy['models'].items():
            for artifacts in seeds.values():
                for name, digest in artifacts.items():
                    verify(SOURCE / 'private' / arm / name, digest)
        for rel, digest in json.loads((OCTOBER / 'private_manifest.json').read_text()).items():
            verify(OCTOBER / 'private' / rel, digest)
        final = json.loads((OCTOBER / 'FINAL.json').read_text())
        if final['status'] != 'COMPLETE_EXPLORATORY' or final['new_fits'] != 0:
            raise ValueError('Cierre de octubre inválido')
        registry = json.loads((SOURCE / 'feature_manifest.json').read_text())
        candidates = []
        for arm in ARMS:
            p = SOURCE / 'private' / (arm + '.parquet')
            if p.exists() or p.is_symlink():
                verify(p, registry[arm]['matrix_sha256'])
                candidates.append((p, registry[arm]['matrix_sha256']))
            # Partial original October matrices: no unique models/predictions here.
            # Successful continuation regenerated features and verified August exactly.
            p = SOURCE / 'private/october' / (arm + '.parquet')
            if p.exists() or p.is_symlink():
                regular(p)
                with p.open('rb') as f:
                    if f.read(4) != b'PAR1':
                        raise ValueError('No parece una matriz parquet: ' + str(p))
                candidates.append((p, sha(p)))
        # No recursive deletion, no .tmp, no old runs, no model/prediction/archive deletion.
        before = shutil.disk_usage(BASE).free
        planned = sum(p.stat().st_size for p, _ in candidates)
        for p, digest in candidates:
            active_training()
            remove_one(p, digest, out / 'limpieza.jsonl', apply)
        inventory = []
        errors = []
        def onerror(e):
            errors.append(str(e))
        for directory, dirs, files in os.walk(BASE, followlinks=False, onerror=onerror):
            dirs[:] = [d for d in dirs if not (Path(directory) / d).is_symlink()]
            for name in files:
                p = Path(directory) / name
                try:
                    s = p.lstat()
                    inventory.append({'path': str(p.relative_to(BASE)), 'bytes': s.st_size,
                                      'symlink': p.is_symlink(), 'allocated_bytes': s.st_blocks * 512})
                except OSError as e:
                    errors.append(str(e))
        (out / 'inventario_historia.json').write_text(json.dumps({'files': inventory, 'errors': errors}))
        summary = {'applied': apply, 'candidate_count': len(candidates), 'candidate_bytes': planned,
                   'free_before': before, 'free_after': shutil.disk_usage(BASE).free,
                   'scope': 'Only known derived matrices in v7_20261114_120354; v1-v6 unchanged',
                   'completed': True}
        (out / 'RESUMEN.json').write_text(json.dumps(summary, indent=2))
        print(json.dumps(summary))


def gc(args, timeout=120, check=True):
    return subprocess.run(['gcloud', 'compute', *args, '--project=' + PROJECT, '--zone=' + ZONE, '--quiet'],
                          text=True, capture_output=True, timeout=timeout, check=check)


def controller(apply):
    here = Path(__file__).resolve().parent
    evidence = here / 'limpiar_matrices_v7_evidencia.json'
    out = Path.home() / ('v7_limpieza_' + time.strftime('%Y%m%d_%H%M%S'))
    out.mkdir(mode=0o700)
    backups = {}
    for name, (rel, digest) in BACKUPS.items():
        p = Path.home() / rel
        verify(p, digest)
        with tarfile.open(p, 'r:gz') as t:
            members = t.getmembers()
            for m in members:
                if m.isfile():
                    with t.extractfile(m) as f:
                        for _ in iter(lambda: f.read(8 * 1024**2), b''):
                            pass
        backups[name] = {'path': str(p), 'sha256': digest, 'members': len(members)}
    (out / 'respaldos_verificados.json').write_text(json.dumps(backups, indent=2))
    state = gc(['instances', 'describe', VM, '--format=value(status)']).stdout.strip()
    if state != 'TERMINATED':
        raise RuntimeError('VM activa: no se detiene ni se interviene automáticamente')
    started = False
    try:
        # Independent cost bound; training controllers must set their own bound later.
        gc(['instances', 'set-scheduling', VM, '--max-run-duration=1800s', '--instance-termination-action=STOP'])
        started = True
        gc(['instances', 'start', VM], timeout=240)
        for attempt in range(12):
            try:
                result = gc(['ssh', 'clarirz@' + VM, '--command=sudo -n shutdown -h +20'], timeout=35, check=False)
                if result.returncode == 0:
                    break
            except subprocess.TimeoutExpired:
                pass
            print('Esperando conexión', attempt + 1, flush=True)
            time.sleep(5)
        else:
            raise RuntimeError('Sin conexión; no se borró nada')
        remote_dir = gc(['ssh', 'clarirz@' + VM, '--command=mktemp -d /home/clarirz/v7_limpieza.XXXXXX']).stdout.strip()
        if not remote_dir.startswith('/home/clarirz/v7_limpieza.') or '\n' in remote_dir:
            raise ValueError('Directorio remoto inesperado')
        (out / 'ubicacion_remota.json').write_text(json.dumps({'remote': remote_dir}))
        gc(['scp', str(Path(__file__).resolve()), str(evidence), 'clarirz@' + VM + ':' + remote_dir + '/'])
        command = 'python3 ' + shlex.quote(remote_dir + '/' + Path(__file__).name) + ' --remote ' + shlex.quote(remote_dir + '/' + evidence.name)
        if apply:
            command += ' --apply'
        try:
            result = gc(['ssh', 'clarirz@' + VM, '--command=' + command], timeout=900, check=False)
            (out / 'ejecucion.log').write_text(result.stdout + result.stderr)
        finally:
            # Journals survive on VM even when transfer fails. No retraining required.
            gc(['scp', '--recurse', 'clarirz@' + VM + ':' + remote_dir, str(out)], timeout=120, check=False)
        if result.returncode:
            raise RuntimeError('Limpieza interrumpida; consultar ' + str(out))
        print(result.stdout)
    finally:
        if started:
            stopped = gc(['instances', 'stop', VM], timeout=240, check=False)
            state = gc(['instances', 'describe', VM, '--format=value(status)'], check=False).stdout.strip()
            (out / 'estado_vm.json').write_text(json.dumps({'status': state, 'stop_returncode': stopped.returncode}))
            print('Estado final VM:', state)
    print('INFORME GUARDADO:', out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Eliminar solamente candidatos verificados')
    parser.add_argument('--remote', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.remote:
        remote(args.remote, args.apply)
    else:
        controller(args.apply)
