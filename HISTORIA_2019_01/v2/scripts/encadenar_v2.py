"""Trabajo único en segundo plano; encadena etapas sólo si finaliza la anterior sin errores."""
from pathlib import Path
import json,sys,subprocess,time,os,fcntl,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'resultados';LOG=ROOT/'logs'
def save(d):
 t=OUT/'cadena_estado.tmp';t.write_text(json.dumps(d,indent=2));t.replace(OUT/'cadena_estado.json')
lock=(OUT/'cadena.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
manifest=json.loads((ROOT/'configuraciones/continuacion_sha256.json').read_text())
for name,expected in manifest.items():
 actual=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
 assert actual==expected,('Código/config cambió',name)
first_pid=int(sys.argv[1]);save({'estado':'ESPERANDO_ESCALERA','pid':os.getpid(),'first_pid':first_pid})
while Path(f'/proc/{first_pid}/cmdline').exists():
 command=Path(f'/proc/{first_pid}/cmdline').read_bytes()
 if b'ejecutar_v2.py' not in command:break
 if (OUT/'STOP').exists():save({'estado':'PAUSA_SOLICITADA'});sys.exit(0)
 time.sleep(30)
state=json.loads((OUT/'estado.json').read_text())
if state['estado']!='ESCALERA_COMPLETA_PENDIENTE_FAMILIAS':save({'estado':'DETENIDO_ESCALERA_NO_COMPLETA','detalle':state});sys.exit(1)
for script,logname,nextstate in [('continuar_familias.py','familias.log','COMBINACIONES_COMPLETAS_PENDIENTE_CANARITOS_REOPT_TEST'),('cerrar_v2.py','cierre.log',None)]:
 save({'estado':'EJECUTANDO','script':script,'pid':os.getpid()})
 with (LOG/logname).open('a') as log:
  result=subprocess.run([sys.executable,str(ROOT/'scripts'/script)],stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4'})
 state=json.loads((OUT/'estado.json').read_text())
 if result.returncode:save({'estado':'ERROR','script':script,'returncode':result.returncode,'detalle':state});sys.exit(result.returncode)
 if nextstate and state['estado']!=nextstate:save({'estado':'FINALIZADO_POR_REGLAS_DE_CONTINUACION','detalle':state});sys.exit(0)
save({'estado':'ETAPAS_EJECUTADAS','detalle':state})
