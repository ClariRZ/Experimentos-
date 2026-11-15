"""Consulta de avance sin abrir predicciones ni etiquetas del test."""
import json,sqlite3
from pathlib import Path
p=Path('resultados');db=p/'studies.sqlite'
if db.exists():
 c=sqlite3.connect(f'file:{db}?mode=ro',uri=True)
 for name,n,best in c.execute("SELECT s.study_name,COUNT(t.trial_id),MAX(v.value) FROM studies s JOIN trials t ON s.study_id=t.study_id JOIN trial_values v ON v.trial_id=t.trial_id WHERE t.state='COMPLETE' GROUP BY s.study_id ORDER BY s.study_name"):
  print(name,'evaluaciones',n,'mejor_auc',round(best,6))
 print('congelado',(p/'FROZEN.json').exists(),'evaluado',(p/'EVALUATED.json').exists())
