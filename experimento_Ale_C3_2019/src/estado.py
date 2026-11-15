from pathlib import Path
import json,sqlite3
r=Path(__file__).resolve().parents[1];out=r/'resultados';status={'preparado':(r/'preparado/READY.json').exists(),'congelado':(out/'FROZEN.json').exists(),'completo':(out/'COMPLETE.json').exists()}
for rep in ['baseline','enriquecido']:
 d=out/rep;bo=0
 if (d/'study.sqlite').exists():
  con=sqlite3.connect('file:'+str(d/'study.sqlite')+'?mode=ro',uri=True)
  try:bo=con.execute("select count(*) from trials where state='COMPLETE'").fetchone()[0]
  finally:con.close()
 seeds=list(d.glob('*/complete.json'));status[rep]={'trials_completos':bo,'semillas_completas':len(seeds)}
print(json.dumps(status,indent=2))
