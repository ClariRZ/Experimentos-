"""Verify consolidated source files without dataset access or training."""
import hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
inventory=json.loads((root/'informes/consolidacion_repos_2026-11-15/INVENTARIO.json').read_text())
tracked=set(subprocess.check_output(['git','-C',str(root),'ls-files','-z']).decode().split('\0'))
errors=[];checked=0;private=0
for row in inventory['files']:
 name=row['destination_path']
 if name is None:
  private+=1
  if row['source_path'] in tracked:errors.append('Private source republished: '+row['source_path'])
  continue
 path=root/name
 if name not in tracked:errors.append('Not tracked: '+name)
 elif not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:errors.append('Missing or changed: '+name)
 else:checked+=1
result={'source_commit':inventory['source_commit'],'public_files_verified':checked,'private_files_not_republished':private,'errors':errors,'independent_model_reproduction':False}
print(json.dumps(result,indent=2));raise SystemExit(bool(errors))
