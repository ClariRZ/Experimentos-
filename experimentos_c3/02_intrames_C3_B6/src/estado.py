"""Consulta de progreso agregada, sin abrir matrices ni mostrar predicciones."""
from pathlib import Path
import json,csv
root=Path(__file__).resolve().parents[1]
refpath=root/'referencia_s3/por_seed.csv'
ref={int(r['seed']):r for r in csv.DictReader(refpath.open())} if refpath.exists() else {}
state={'B6_completo':(root/'resultados/B6/COMPLETE.json').exists(),'C3':{},'control_verificado_con_referencia':0,'control_diferente_de_referencia':0,'todo_completo':(root/'COMPLETADO.txt').exists()}
for arm in ['C3_CONTROL','C3_HOJA2500','C3_INTRAMES']:
 records=[]
 for f in (root/'resultados/C3'/arm).glob('*/complete.json'):
  try:r=json.loads(f.read_text())
  except (OSError,json.JSONDecodeError):continue
  records.append(r)
  if arm=='C3_CONTROL' and r['seed'] in ref:
   ok=all(r['cuts'][str(k)]['ganancia']==int(ref[r['seed']]['ganancia_'+str(k)]) for k in [10500,11000,11500])
   state['control_verificado_con_referencia' if ok else 'control_diferente_de_referencia']+=1
 state['C3'][arm]={'completos':len(records),'total':20,'segundos_acumulados':round(sum(r['seconds'] for r in records),1)}
print(json.dumps(state,indent=2))
