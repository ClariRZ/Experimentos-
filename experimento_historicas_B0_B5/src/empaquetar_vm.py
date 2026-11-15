"""Exporta únicamente entregables; excluye datos originales, matrices y entorno."""
from pathlib import Path
import tarfile
root=Path.cwd();r=root/'resultados'
assert (r/'EVALUATED.json').exists(),'Evaluación pendiente'
pairs=[]
for name in ['resultados.csv','FROZEN.json','EVALUATED.json','studies.sqlite']:
 pairs.append((r/name,'resultados/'+name))
for e in ['B0','B1','B2','B3','B4','B5']:
 for name in ['model.txt','complete.json','trials.csv','importance.csv','validation_predictions.parquet','test_predictions.parquet','curva_octubre.csv']:
  pairs.append((r/e/name,f'resultados/{e}/{name}'))
pairs.extend([(root/'preparado'/'manifest.json','manifest.json'),(root/'preparado'/'cobertura_desarrollo.csv','auditoria/cobertura_desarrollo.csv'),(root/'requirements_vm.txt','requirements_vm.txt'),(root/'final_run.log','logs/final_run.log'),(root/'pilot_run.log','logs/pilot_run.log')])
for f in (root/'auditoria').iterdir():
 if f.is_file():pairs.append((f,'auditoria_vm/'+f.name))
with tarfile.open(root/'resultados_entrega.tar.gz','w:gz') as t:
 for f,name in pairs:
  assert f.is_file(),str(f)
  t.add(f,arcname=name,recursive=False)
print('resultados_entrega.tar.gz', (root/'resultados_entrega.tar.gz').stat().st_size,'bytes',len(pairs),'archivos')
