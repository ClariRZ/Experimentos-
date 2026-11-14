#!/usr/bin/env python3
"""Inventario privado y de solo lectura. Ejecutar en Cloud Shell con Python 3."""
import argparse
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

PROJECT = 'proj-uba-261002122233861'
ZONE = 'northamerica-northeast2-b'
VM = 'clari-c1-fundados'


def activity():
    found = []
    for p in Path('/proc').glob('[0-9]*'):
        try:
            if int(p.name) == os.getpid():
                continue
            cmd = (p / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
            executable = Path(os.readlink(p / 'exe')).name.lower()
            if any(x in executable for x in ('python', 'rscript', 'lightgbm')):
                if any(x in cmd.lower() for x in ('ejecutar', 'worker_vm', 'train', 'optuna', 'historia', 'entren', 'modelo')):
                    found.append({'pid': int(p.name), 'executable': executable})
        except (OSError, ValueError):
            pass
    return found


def category(path):
    s = path.lower()
    name = Path(s).name
    if any(x in s for x in ('/.ssh/', '/.config/gcloud/', 'credential', 'secret', 'token')):
        return 'privado_credenciales'
    if any(x in s for x in ('/.venv/', '/venv/', '/site-packages/', '/dist-packages/')):
        return 'entorno_no_borrar_sin_congelar_versiones'
    if '/.git/' in s:
        return 'historial_git_conservar'
    if any(x in s for x in ('/.cache/', '/__pycache__/', '/var/cache/')):
        return 'cache_candidata_no_autorizada'
    if name.endswith(('.tmp', '.partial')):
        return 'temporal_requiere_verificar_uso'
    if any(x in name for x in ('pred', 'score', 'submission')):
        return 'predicciones_respaldar'
    if 'modelo' in s or 'model' in s or name.endswith(('.pkl', '.joblib', '.bin')):
        return 'modelos_respaldar'
    if '/matrices/' in s or '/preparado/' in s or name.endswith('.npy'):
        return 'matrices_requieren_respaldo_o_reconstruccion_probada'
    if name.endswith(('.zip', '.tar', '.gz', '.bz2', '.xz', '.zst')):
        return 'archivo_comprimido_contenido_no_verificado'
    if name.endswith(('.json', '.yaml', '.yml', '.log', '.md', '.txt', '.tsv')):
        return 'configuracion_resultados_registros_respaldar'
    if name.endswith(('.py', '.r', '.sh', '.ipynb', '.sql')):
        return 'codigo_respaldar'
    if name.endswith(('.csv', '.parquet', '.npz', '.xlsx', '.rds', '.fst')):
        return 'datos_o_predicciones_respaldar_hasta_identificar'
    return 'otros_revisar'


def remote_audit():
    os.nice(15)
    started = time.time()
    initial_activity = activity()
    root_device = os.stat('/').st_dev
    stack = ['/']
    files, errors, skipped = [], [], []
    hardlinks = set()
    totals = collections.Counter()
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as entries:
                for e in entries:
                    try:
                        st = e.stat(follow_symlinks=False)
                        if e.is_symlink():
                            continue
                        if st.st_dev != root_device:
                            skipped.append(e.path)
                            continue
                        if e.is_dir(follow_symlinks=False):
                            stack.append(e.path)
                        elif e.is_file(follow_symlinks=False):
                            key = (st.st_dev, st.st_ino)
                            allocated = st.st_blocks * 512 if key not in hardlinks else 0
                            hardlinks.add(key)
                            item = dict(path=e.path, bytes=st.st_size, allocated_bytes=allocated,
                                        mtime_ns=st.st_mtime_ns, inode=st.st_ino,
                                        category=category(e.path), uid=st.st_uid)
                            files.append(item)
                            parts = Path(e.path).parts
                            for depth in range(2, min(5, len(parts))):
                                totals[str(Path(*parts[:depth]))] += allocated
                    except OSError as exc:
                        errors.append({'path': e.path, 'error': str(exc)})
        except OSError as exc:
            errors.append({'path': directory, 'error': str(exc)})
    # Hash only equal-size large-file candidates. A matching name/size is not proof.
    sizes = collections.defaultdict(list)
    for item in files:
        if item['bytes'] >= 32 * 1024**2 and item['category'] != 'privado_credenciales':
            sizes[item['bytes']].append(item)
    groups = collections.defaultdict(list)
    hash_status = 'completed_for_equal_size_files_at_least_32_MiB'
    if initial_activity or activity():
        hash_status = 'deferred_training_detected'
    else:
        try:
            for candidates in sizes.values():
                if len(candidates) < 2:
                    continue
                for item in candidates:
                    if activity():
                        raise InterruptedError('training_detected')
                    p = Path(item['path'])
                    h = hashlib.sha256()
                    last_check = time.monotonic()
                    with p.open('rb') as f:
                        for block in iter(lambda: f.read(8 * 1024**2), b''):
                            h.update(block)
                            if time.monotonic() - last_check >= 5:
                                if activity():
                                    raise InterruptedError('training_detected')
                                last_check = time.monotonic()
                    st = p.stat()
                    if (st.st_size, st.st_mtime_ns, st.st_ino) != (item['bytes'], item['mtime_ns'], item['inode']):
                        item['hash_status'] = 'changed_during_audit'
                        continue
                    item['sha256'] = h.hexdigest()
                    groups[(item['bytes'], h.hexdigest())].append(item['path'])
        except InterruptedError:
            hash_status = 'interrupted_training_detected'
        except OSError as exc:
            hash_status = 'incomplete_io_error'
            errors.append({'phase': 'hashing', 'error': str(exc)})
    usage = os.statvfs('/')
    result = dict(schema=1, started_epoch=started, finished_epoch=time.time(),
                  scope='Regular files on root filesystem; symlinks and other filesystems excluded',
                  files=files, errors=errors, excluded_mounts=sorted(set(skipped)),
                  folders_allocated_bytes=dict(totals.most_common()),
                  disk_free_bytes=usage.f_bavail * usage.f_frsize,
                  training_at_start=initial_activity, training_at_end=activity(),
                  hash_status=hash_status,
                  duplicates=[{'bytes_each': size, 'sha256': sha, 'paths': paths}
                              for (size, sha), paths in groups.items() if len(paths) > 1],
                  external_backups_verified=False, deleted_files=0,
                  backup_warning='Same-VM duplicates are NOT external backups. Category is heuristic, not deletion authorization.')
    print(json.dumps(result))


def report(data):
    gib = lambda n: f'{n / 2**30:.2f} GiB'
    summary = collections.Counter()
    for f in data['files']:
        summary[f['category']] += f['allocated_bytes']
    lines = ['# Auditoría integral privada de la VM', '',
             f"Archivos inventariados: {len(data['files'])}. Espacio libre: {gib(data['disk_free_bytes'])}.",
             f"Errores de lectura: {len(data['errors'])}. Verificación de duplicados: {data['hash_status']}.",
             'No se borraron archivos. No se certificó ningún respaldo externo.', '',
             '## Qué debe quedar respaldado',
             'Datos originales; código y commit ejecutado; configuración, semillas y versiones; '
             'modelos; predicciones con identificadores; resultados por semilla; registros y manifiestos. '
             'Git no garantiza que los archivos grandes estén incluidos. Los entornos se conservan '
             'hasta registrar y validar sus dependencias.', '',
             '## Ocupación por categoría (clasificación orientativa)', '']
    lines += [f'- {k}: {gib(v)}' for k, v in summary.most_common()]
    lines += ['', '## Directorios más grandes', '']
    lines += [f'- `{k}`: {gib(v)}' for k, v in list(data['folders_allocated_bytes'].items())[:35]]
    lines += ['', '## Duplicados verificados por contenido',
              'Son candidatos para revisar uso y permisos; no se eliminan automáticamente.']
    for group in data['duplicates']:
        lines.append(f"- {gib(group['bytes_each'])} por archivo; SHA256 {group['sha256']}")
        lines.extend('  - `' + p + '`' for p in group['paths'])
    if not data['duplicates']:
        lines.append('No se certificaron duplicados en esta ejecución.')
    lines += ['', '## Qué no hace falta respaldar necesariamente',
              'Cachés descargables, bytecode y matrices temporales pueden ser prescindibles, '
              'pero solo tras verificar que no están en uso y que no contienen la única copia. '
              'Una matriz derivada requiere respaldo o reconstrucción comprobada antes de borrarse.', '',
              '## Límites y pendientes explícitos',
              '- El inventario es en vivo, no una instantánea consistente de una corrida activa.',
              '- Las categorías dependen de nombres y extensiones; no prueban el contenido.',
              '- No se leyó el contenido de credenciales ni se publicaron archivos privados.',
              '- No se verificaron copias en GitHub, buckets ni otras máquinas.',
              '- El cálculo de hashes se pospone o interrumpe si detecta entrenamiento.',
              '- Los archivos menores de 32 MiB no se comparan por hash.',
              '- El detalle completo, errores y volúmenes excluidos están en inventario_privado.json.', '']
    return '\n'.join(lines)


def cloud_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    a = parser.parse_args()
    out = Path(a.output).expanduser()
    out.mkdir(parents=True, exist_ok=False)
    base = ['gcloud', 'compute']
    common = ['--project=' + PROJECT, '--zone=' + ZONE, '--quiet']
    def call(args, **kw):
        return subprocess.run(base + args + common, check=True, text=True, **kw)
    details = json.loads(call(['instances', 'describe', VM, '--format=json'], capture_output=True).stdout)
    (out / 'vm_antes.json').write_text(json.dumps(details, indent=2))
    started_here = details['status'] == 'TERMINATED'
    if details['status'] not in ('TERMINATED', 'RUNNING'):
        raise RuntimeError('VM en transición: no se interviene.')
    source = Path(__file__).read_text()
    data = None
    try:
        if started_here:
            call(['instances', 'start', VM])
        for attempt in range(8):
            probe = subprocess.run(base + ['ssh', 'clarirz@' + VM] + common + ['--command=true'], capture_output=True, text=True)
            if probe.returncode == 0:
                break
            time.sleep(10)
        else:
            raise RuntimeError('SSH no disponible.')
        print('Auditoría de solo lectura en curso. Los hashes se omiten si hay entrenamiento.', flush=True)
        result = call(['ssh', 'clarirz@' + VM, '--command=sudo -n python3 - remote'], input=source, capture_output=True)
        (out / 'salida_remota.txt').write_text(result.stdout)
        (out / 'diagnostico_ssh.txt').write_text(result.stderr)
        data = json.loads(result.stdout)
        (out / 'inventario_privado.json').write_text(json.dumps(data))
        (out / 'INFORME.md').write_text(report(data))
        (out / 'INFORME.md.sha256').write_text(hashlib.sha256((out / 'INFORME.md').read_bytes()).hexdigest())
        print(report(data), flush=True)
        print('AUDITORIA_GUARDADA', out, flush=True)
    finally:
        if started_here:
            try:
                probe_source = source.split("if __name__ == '__main__':")[0] + '\nprint(json.dumps(activity()))\n'
                active = json.loads(call(['ssh', 'clarirz@' + VM, '--command=sudo -n python3 -'], input=probe_source, capture_output=True).stdout)
                if active:
                    print('VM conservada encendida: apareció un proceso de entrenamiento.', flush=True)
                else:
                    call(['instances', 'stop', VM])
            except Exception as exc:
                print('No se pudo confirmar apagado; revisar VM:', str(exc), flush=True)
        else:
            print('La VM ya estaba activa: no se modifica su estado ni su apagado programado.', flush=True)


if __name__ == '__main__':
    if sys.argv[1:] == ['remote']:
        remote_audit()
    else:
        cloud_main()
