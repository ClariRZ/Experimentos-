from pathlib import Path
import json,hashlib,platform
import numpy,pandas,lightgbm,optuna
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'config/codigo_sha256.json').read_text())
observed={}
for name,expected in manifest.items():
 actual=hashlib.sha256((root/name).read_bytes()).hexdigest();assert actual==expected,name;observed[name]=actual
out={'source_hashes_verified':observed,'platform':platform.platform(),'python':platform.python_version(),'numpy':numpy.__version__,'pandas':pandas.__version__,'lightgbm':lightgbm.__version__,'optuna':optuna.__version__,'config_sha256':hashlib.sha256((root/'config/protocolo.json').read_bytes()).hexdigest()}
(root/'auditoria_runtime.json').write_text(json.dumps(out,indent=2));print('RUNTIME_Y_HASHES_OK')
