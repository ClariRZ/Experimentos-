"""Reproduce desde cero en otra carpeta; no modifica la ejecución de referencia."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',required=True,help='Parquet original, conservado fuera de Git')
    p.add_argument('--out',required=True,help='Carpeta nueva para la reproducción')
    p.add_argument('--python',default='python3.12',help='Python 3.12.3, como en la VM original')
    p.add_argument('--check-only',action='store_true',help='Comprueba insumos sin instalar ni entrenar')
    a=p.parse_args();data=Path(a.data).resolve();out=Path(a.out).resolve()
    if out.exists():raise SystemExit('La carpeta de destino ya existe; elegí una nueva para preservar resultados.')
    cfg=json.loads((ROOT/'config.json').read_text())
    if sha(data)!=cfg['data_sha256']:raise SystemExit('El Parquet no coincide con el SHA-256 del experimento.')
    executable=shutil.which(a.python)
    if not executable:raise SystemExit('No se encontró el intérprete: '+a.python)
    version=json.loads(subprocess.check_output([executable,'-c','import sys,json;print(json.dumps(list(sys.version_info[:3])))'],text=True))
    if version != [3,12,3]:raise SystemExit('Se requiere Python 3.12.3; encontrado '+str(version))
    manifest=json.loads((ROOT/'auditoria/entrega_manifest.json').read_text())
    for name,digest in manifest.items():
        if sha(ROOT/name)!=digest:raise SystemExit('Archivo de referencia modificado: '+name)
    print('Parquet, integridad del paquete e intérprete: OK',flush=True)
    if a.check_only:return
    out.mkdir(parents=True);(out/'logs').mkdir();(out/'auditoria').mkdir()
    shutil.copytree(ROOT/'src',out/'src',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ['config.json','requirements_vm.txt','conclusiones.txt','analisis_del_material.txt','marcelo_usar_adaptar_excluir.csv','bibliografia.txt']:
        shutil.copy2(ROOT/name,out/name)
    shutil.copy2(ROOT/'auditoria/repositorio.json',out/'auditoria/repositorio.json')
    env=os.environ.copy();env['MPLCONFIGDIR']=str(out/'.mplconfig');env['PYTHONHASHSEED']='0'
    commands=[]
    def run(args):
        commands.append([str(x) for x in args]);(out/'comandos.json').write_text(json.dumps(commands,indent=2))
        with open(out/'logs/reproduccion.log','a') as log:
            proc=subprocess.Popen([str(x) for x in args],cwd=out,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            for line in proc.stdout:
                log.write(line);log.flush();print(line,end='',flush=True)
            code=proc.wait()
            if code:raise SystemExit('Etapa fallida; ver logs/reproduccion.log. Código '+str(code))
    run([executable,'-m','venv',out/'.venv'])
    py=out/'.venv/bin/python'
    run([py,'-m','pip','install','-r','requirements_vm.txt'])
    run([py,'-m','pip','check'])
    run([py,'-m','unittest','discover','-s','src','-p','test_*.py'])
    run([py,'src/auditar.py','--data',data,'--out','auditoria'])
    run([py,'src/preparar.py','--data',data,'--out','preparado'])
    run([py,'src/cobertura.py','--prep','preparado','--out','auditoria/cobertura_familias.csv'])
    run([py,'src/entrenar.py','--prep','preparado','--out','resultados','--config','config.json','--mode','train'])
    run([py,'src/entrenar.py','--prep','preparado','--out','resultados','--config','config.json','--mode','evaluate'])
    run([py,'src/verificar_resultados.py','--data',data,'--results','resultados','--out','auditoria/verificacion_final.json'])
    run([py,'src/regenerar_referencia.py','--reference',ROOT/'resultados','--prep','preparado','--out','referencia_regenerada'])
    run([py,'src/verificar_resultados.py','--data',data,'--results','referencia_regenerada','--out','auditoria/verificacion_referencia.json'])
    run([py,'src/comparar_reproduccion.py','--reference','referencia_regenerada','--new','resultados','--out','auditoria/comparacion_reproduccion.json'])
    # Las conclusiones originales sólo se reutilizan si coinciden métricas, ensayos y predicciones.
    run([py,'src/informe.py','--results','resultados','--out','.'])
    print('REPRODUCCION_COMPLETA_Y_COMPARADA:',out,flush=True)

if __name__=='__main__':main()
