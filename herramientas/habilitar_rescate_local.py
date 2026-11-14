#!/usr/bin/env python3
"""Habilita una clave pública temporal para recuperar a la computadora; no borra datos."""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shlex
import subprocess
import time
from limpiar_matrices_v7 import gc, VM


def validate_key(value):
    parts = value.strip().split()
    if len(parts) != 3 or parts[0] != 'ssh-ed25519' or parts[2] != 'respaldo-local-v1-v6-20261114':
        raise ValueError('Clave pública o comentario inesperado')
    base64.b64decode(parts[1], validate=True)
    return ' '.join(parts)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--public-key', required=True)
    p.add_argument('--recovery', type=Path, required=True)
    a = p.parse_args()
    key = validate_key(a.public_key)
    root = json.loads((a.recovery / 'ubicacion.json').read_text())['remote']
    if not root.startswith('/home/clarirz/respaldo_v1_v6.') or '\n' in root:
        raise ValueError('Ruta de recuperación inesperada')
    state = gc(['instances','describe',VM,'--format=value(status)']).stdout.strip()
    if state != 'TERMINATED':
        raise RuntimeError('VM activa: no se interviene')
    expiry = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y%m%d%H%M%SZ')
    line = f'restrict,expiry-time="{expiry}" {key}'
    code = '''from pathlib import Path
import json, os, subprocess
root=Path(ROOT)
assert (root/'paquete.json').is_file() and (root/'inventario.json').is_file()
subprocess.run(['sudo','-n','shutdown','-h','+55'],check=True)
s=Path.home()/'.ssh';s.mkdir(mode=0o700,exist_ok=True)
p=s/'authorized_keys'
assert not p.is_symlink()
old=p.read_text() if p.exists() else ''
if KEY not in old:
 with p.open('a') as f:
  f.write(('\\n' if old and not old.endswith('\\n') else '')+LINE+'\\n');f.flush();os.fsync(f.fileno())
 os.chmod(p,0o600)
print(json.dumps({'remote':str(root),'host_public_key':Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().strip(),'archive_bytes':json.loads((root/'paquete.json').read_text())['bytes']}))
'''.replace('ROOT',repr(root)).replace('KEY',repr(key)).replace('LINE',repr(line))
    started = False
    try:
        gc(['instances','set-scheduling',VM,'--max-run-duration=3600s','--instance-termination-action=STOP'])
        started=True
        gc(['instances','start',VM],timeout=240)
        for attempt in range(12):
            try:
                r=gc(['ssh','clarirz@'+VM,'--command=python3 -c '+shlex.quote(code)],timeout=40,check=False)
                if r.returncode==0:
                    ip=gc(['instances','describe',VM,'--format=value(networkInterfaces[0].accessConfigs[0].natIP)']).stdout.strip()
                    print('ACCESO_LOCAL_LISTO',json.dumps({'ip':ip,'expires_utc':expiry,'details':r.stdout.strip()}),flush=True)
                    print('No se entrenó ni borró nada. La VM queda encendida para copiar directamente; límite una hora.')
                    return
            except subprocess.TimeoutExpired:
                pass
            print('Esperando conexión',attempt+1,flush=True);time.sleep(5)
        raise RuntimeError('No se pudo habilitar acceso')
    except BaseException:
        if started: gc(['instances','stop',VM],timeout=240,check=False)
        raise

if __name__=='__main__':main()
