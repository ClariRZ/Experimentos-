#!/usr/bin/env python3
"""Cloud Shell: respalda v1/v6, verifica miembros y solo entonces limpia matrices v6."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile
import time
from limpiar_matrices_v7 import gc, sha, verify, regular, active_training, remove_one, VM

BASE = Path('/home/clarirz/HISTORIA_2019_01')
TRAIN = 'v6/deployments/v6_20261113_02/resultados/entrenamiento'
OCT = 'v6/evaluaciones/octubre_v6_01/resultado'
ROOTS = ['historia_2019_v1', 'resultados_historia_01', 'piloto_historia_01',
         'revision_historia_01', 'revision_historia_02', 'full_historia_01.log', 'v6',
         'datos/analistasr_competencia_2026.csv.gz']
SKIP_DIRS = {'.venv', 'venv', '__pycache__', '.cache'}


def dump(p, obj):
    Path(p).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


@contextlib.contextmanager
def locks():
    with contextlib.ExitStack() as stack:
        for name in ['historia_experiment.lock', 'historia_v6.lock']:
            f = stack.enter_context(open('/tmp/' + name, 'a'))
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        active_training()
        yield


def candidates(expected):
    for rel, digest in expected['required'].items():
        verify(BASE / rel, digest)
    result = {}
    for rel, digest in expected['matrices'].items():
        p = BASE / rel
        if p.exists() or p.is_symlink():
            verify(p, digest)
            result[rel] = digest
    for arm in expected['arms']:
        rel = OCT + '/private/' + arm + '_october.npy'
        p = BASE / rel
        if p.exists() or p.is_symlink():
            regular(p)
            with p.open('rb') as f:
                if f.read(6) != b'\x93NUMPY':
                    raise ValueError('Matriz octubre no reconocida: ' + rel)
            result[rel] = sha(p)
    return result


def prepare(folder):
    expected = json.loads((folder / 'evidencia.json').read_text())
    with locks():
        deletable = candidates(expected)
        members, excluded = {}, []
        # All artifacts in selected roots except named, verified matrices and environments.
        for root in ROOTS:
            p = BASE / root
            if not p.exists():
                if root in ['historia_2019_v1', 'resultados_historia_01', 'v6', 'datos/analistasr_competencia_2026.csv.gz']:
                    raise FileNotFoundError(p)
                excluded.append({'path': root, 'reason': 'optional_root_absent'})
                continue
            paths = [p] if p.is_file() else []
            if p.is_dir():
                for directory, dirs, files in os.walk(p, followlinks=False):
                    for d in list(dirs):
                        child = Path(directory) / d
                        if d in SKIP_DIRS:
                            excluded.append({'path': str(child.relative_to(BASE)), 'reason': 'environment_or_cache_not_deleted'})
                            dirs.remove(d)
                        elif child.is_symlink():
                            raise ValueError('Enlace de directorio sin auditar: ' + str(child))
                    paths.extend(Path(directory) / name for name in files)
            for f in paths:
                rel = str(f.relative_to(BASE))
                if rel in deletable:
                    continue
                regular(f)
                members[rel] = {'sha256': sha(f), 'bytes': f.stat().st_size}
        size = sum(v['bytes'] for v in members.values())
        if shutil.disk_usage(folder).free < size * 2.1 + 2 * 1024**3:
            raise OSError('Sin margen para empaquetar; no se borra nada')
        dump(folder / 'inventario.json', {'members': members, 'excluded': excluded, 'deletable': deletable,
                                        'v1_originals_deleted': False, 'scope_roots': ROOTS})
        archive = folder / 'respaldo.tar.gz'
        with tarfile.open(archive, 'w:gz', compresslevel=1) as t:
            for rel in sorted(members):
                active_training()
                t.add(BASE / rel, arcname=rel, recursive=False)
        # Chunk transfer avoids restarting a large archive from zero after SSH failure.
        chunks = []
        with archive.open('rb') as f:
            i = 0
            while True:
                block = f.read(32 * 1024**2)
                if not block:
                    break
                name = f'parte_{i:04d}'
                (folder / name).write_bytes(block)
                chunks.append({'name': name, 'sha256': hashlib.sha256(block).hexdigest(), 'bytes': len(block)})
                i += 1
        dump(folder / 'paquete.json', {'archive_sha256': sha(archive), 'bytes': archive.stat().st_size, 'chunks': chunks,
                                     'inventory_sha256': sha(folder / 'inventario.json')})


def validate_archive(archive, inventory):
    seen = set()
    with tarfile.open(archive, 'r:gz') as t:
        for item in t:
            if not item.isfile() or item.name not in inventory['members'] or item.name in seen:
                raise ValueError('Miembro inesperado: ' + item.name)
            h = hashlib.sha256()
            with t.extractfile(item) as f:
                for block in iter(lambda: f.read(8 * 1024**2), b''):
                    h.update(block)
            ref = inventory['members'][item.name]
            if h.hexdigest() != ref['sha256'] or item.size != ref['bytes']:
                raise ValueError('Miembro no coincide: ' + item.name)
            seen.add(item.name)
    if seen != set(inventory['members']):
        raise ValueError('Faltan miembros en respaldo')


def clean(folder):
    with locks():
        inv = json.loads((folder / 'inventario.json').read_text())
        receipt = json.loads((folder / 'recibo.json').read_text())
        pkg = json.loads((folder / 'paquete.json').read_text())
        if receipt != {'archive_sha256': pkg['archive_sha256'], 'inventory_sha256': sha(folder / 'inventario.json'),
                       'all_members_verified': True}:
            raise ValueError('No existe comprobación de respaldo fuera de VM')
        exp = json.loads((folder / 'evidencia.json').read_text())
        current = candidates(exp)
        if current != inv['deletable']:
            raise ValueError('Cambió el plan de matrices')
        for rel, item in inv['members'].items():
            verify(BASE / rel, item['sha256'])
        before = shutil.disk_usage(BASE).free
        deleted = 0
        for rel, digest in current.items():
            active_training()
            deleted += remove_one(BASE / rel, digest, folder / 'limpieza.jsonl', apply=True)
        summary = {'deleted_files': len(current), 'deleted_bytes': deleted, 'free_before': before,
                   'free_after': shutil.disk_usage(BASE).free, 'v1_deleted_files': 0,
                   'models_predictions_and_dataset_preserved': True}
        dump(folder / 'RESUMEN.json', summary)
        print(json.dumps(summary), flush=True)


def controller():
    here = Path(__file__).resolve().parent
    dest = Path.home() / ('respaldo_v1_v6_' + time.strftime('%Y%m%d_%H%M%S'))
    dest.mkdir(mode=0o700)
    if gc(['instances', 'describe', VM, '--format=value(status)']).stdout.strip() != 'TERMINATED':
        raise RuntimeError('VM activa: no se interviene')
    remote_dir = None
    try:
        gc(['instances', 'set-scheduling', VM, '--max-run-duration=3600s', '--instance-termination-action=STOP'])
        gc(['instances', 'start', VM], timeout=240)
        for attempt in range(12):
            try:
                r = gc(['ssh', 'clarirz@' + VM, '--command=sudo -n shutdown -h +55'], timeout=35, check=False)
                if r.returncode == 0:
                    break
            except subprocess.TimeoutExpired:
                pass
            print('Esperando conexión', attempt + 1, flush=True); time.sleep(5)
        else:
            raise RuntimeError('Sin conexión')
        remote_dir = gc(['ssh', 'clarirz@' + VM, '--command=mktemp -d /home/clarirz/respaldo_v1_v6.XXXXXX']).stdout.strip()
        if not remote_dir.startswith('/home/clarirz/respaldo_v1_v6.') or '\n' in remote_dir:
            raise ValueError('Ruta inesperada')
        dump(dest / 'ubicacion.json', {'remote': remote_dir})
        for name in ['respaldar_limpiar_v1_v6.py', 'limpiar_matrices_v7.py', 'respaldar_limpiar_v1_v6_evidencia.json']:
            target = 'evidencia.json' if name.endswith('_evidencia.json') else name
            gc(['scp', str(here / name), 'clarirz@' + VM + ':' + remote_dir + '/' + target])
        def run(phase):
            cmd = 'python3 ' + shlex.quote(remote_dir + '/respaldar_limpiar_v1_v6.py') + ' --phase ' + phase + ' --folder ' + shlex.quote(remote_dir)
            r = gc(['ssh', 'clarirz@' + VM, '--command=' + cmd], timeout=1200, check=False)
            (dest / (phase + '.log')).write_text(r.stdout + r.stderr)
            if r.returncode: raise RuntimeError('Falló ' + phase + '; originales preservados salvo eliminaciones ya registradas. Ver ' + str(dest))
            print(r.stdout, flush=True)
        print('Inventariando y respaldando v1/v6; todavía no se borra nada.', flush=True)
        run('prepare')
        for name in ['inventario.json', 'paquete.json']:
            gc(['scp', 'clarirz@' + VM + ':' + remote_dir + '/' + name, str(dest / name)])
        pkg = json.loads((dest / 'paquete.json').read_text()); verify(dest / 'inventario.json', pkg['inventory_sha256'])
        if shutil.disk_usage(dest).free < 2 * pkg['bytes'] + 512 * 1024**2:
            raise OSError('Cloud Shell sin espacio para respaldo; no se limpia')
        for part in pkg['chunks']:
            for attempt in range(3):
                try:
                    gc(['scp', 'clarirz@' + VM + ':' + remote_dir + '/' + part['name'], str(dest / part['name'])], timeout=300)
                    verify(dest / part['name'], part['sha256']); break
                except (subprocess.SubprocessError, ValueError):
                    if attempt == 2: raise
            print('Parte verificada:', part['name'], flush=True)
        archive = dest / 'respaldo.tar.gz'
        with archive.open('wb') as out:
            for part in pkg['chunks']:
                with (dest / part['name']).open('rb') as f: shutil.copyfileobj(f, out)
        verify(archive, pkg['archive_sha256'])
        validate_archive(archive, json.loads((dest / 'inventario.json').read_text()))
        receipt = {'archive_sha256': pkg['archive_sha256'], 'inventory_sha256': pkg['inventory_sha256'], 'all_members_verified': True}
        dump(dest / 'recibo.json', receipt)
        print('RESPALDO COMPLETO VERIFICADO FUERA DE LA VM', flush=True)
        gc(['scp', str(dest / 'recibo.json'), 'clarirz@' + VM + ':' + remote_dir + '/recibo.json'])
        run('clean')
        for name in ['limpieza.jsonl', 'RESUMEN.json']:
            gc(['scp', 'clarirz@' + VM + ':' + remote_dir + '/' + name, str(dest / name)], check=False)
    finally:
        gc(['instances', 'stop', VM], timeout=240, check=False)
        state = gc(['instances', 'describe', VM, '--format=value(status)'], check=False).stdout.strip()
        dump(dest / 'estado_vm.json', {'status': state})
        print('Estado final VM:', state, '\nRespaldo e informe:', dest, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--phase', choices=['prepare', 'clean']); p.add_argument('--folder', type=Path)
    a = p.parse_args()
    if a.phase == 'prepare': prepare(a.folder)
    elif a.phase == 'clean': clean(a.folder)
    else: controller()
